# 阶段 4b：数据模型

## 全局约定

- 所有表带 `created_at` / `updated_at`（`TIMESTAMPTZ`）
- 软删除仅 `courses` 使用（`deleted_at`）；排期与预约是事实记录，用状态字段表达取消，不删行
- 枚举存字符串 + `CHECK` 约束：数据量小，可读性优先于存储空间
- 主键统一 `BIGSERIAL`

## 建表 DDL（PostgreSQL）

```sql
CREATE TABLE users (
    id          BIGSERIAL PRIMARY KEY,
    phone       VARCHAR(20) NOT NULL UNIQUE,
    name        VARCHAR(50) NOT NULL DEFAULT '',
    role        VARCHAR(10) NOT NULL DEFAULT 'member'
                CHECK (role IN ('member', 'admin')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE auth_codes (
    phone       VARCHAR(20) PRIMARY KEY,   -- 每个手机号同时只有一个有效验证码，重发即覆盖
    code_hash   VARCHAR(64) NOT NULL,      -- 验证码摘要（SHA-256），不存明文
    attempts    INT         NOT NULL DEFAULT 0,   -- 校验失败次数，达上限即作废
    expires_at  TIMESTAMPTZ NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE sessions (
    token       VARCHAR(64) PRIMARY KEY,
    user_id     BIGINT      NOT NULL REFERENCES users(id),
    expires_at  TIMESTAMPTZ NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_sessions_user ON sessions(user_id);

CREATE TABLE coaches (
    id          BIGSERIAL PRIMARY KEY,
    name        VARCHAR(50) NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE courses (
    id               BIGSERIAL PRIMARY KEY,
    name             VARCHAR(100) NOT NULL,
    coach_id         BIGINT       NOT NULL REFERENCES coaches(id),
    duration_minutes INT          NOT NULL,
    description      TEXT         NOT NULL DEFAULT '',
    deleted_at       TIMESTAMPTZ,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE schedules (
    id           BIGSERIAL PRIMARY KEY,
    course_id    BIGINT      NOT NULL REFERENCES courses(id),
    start_time   TIMESTAMPTZ NOT NULL,
    end_time     TIMESTAMPTZ NOT NULL,
    capacity     INT         NOT NULL,
    booked_count INT         NOT NULL DEFAULT 0,
    status       VARCHAR(10) NOT NULL DEFAULT 'open'
                 CHECK (status IN ('open', 'canceled')),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (course_id, start_time),
    CHECK (booked_count >= 0 AND booked_count <= capacity)   -- ADR-001 的最后防线
);
CREATE INDEX idx_schedules_start ON schedules(start_time);

CREATE TABLE bookings (
    id          BIGSERIAL PRIMARY KEY,
    schedule_id BIGINT      NOT NULL REFERENCES schedules(id),
    user_id     BIGINT      NOT NULL REFERENCES users(id),
    status      VARCHAR(10) NOT NULL DEFAULT 'confirmed'
                CHECK (status IN ('confirmed', 'canceled')),
    canceled_at TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (schedule_id, user_id)                             -- ADR-001 防重复预约
);
CREATE INDEX idx_bookings_user     ON bookings(user_id, status);
CREATE INDEX idx_bookings_schedule ON bookings(schedule_id);

CREATE TABLE waitlist_entries (
    id          BIGSERIAL PRIMARY KEY,
    schedule_id BIGINT      NOT NULL REFERENCES schedules(id),
    user_id     BIGINT      NOT NULL REFERENCES users(id),
    status      VARCHAR(10) NOT NULL DEFAULT 'waiting'
                CHECK (status IN ('waiting', 'promoted', 'canceled')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (schedule_id, user_id)
);
CREATE INDEX idx_waitlist_promote ON waitlist_entries(schedule_id, status, id);

CREATE TABLE notification_tasks (
    id            BIGSERIAL PRIMARY KEY,
    user_id       BIGINT      NOT NULL REFERENCES users(id),
    type          VARCHAR(30) NOT NULL,   -- booking_confirmed | promoted | schedule_canceled
    payload       JSONB       NOT NULL,
    status        VARCHAR(10) NOT NULL DEFAULT 'pending'
                  CHECK (status IN ('pending', 'sent', 'dead')),
    retry_count   INT         NOT NULL DEFAULT 0,
    next_retry_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_ntasks_poll ON notification_tasks(status, next_retry_at);
```

## 预期行数与索引依据

| 表 | 一年预期行数 | 索引 | 服务的查询 |
| --- | --- | --- | --- |
| schedules | 约 5000 | `idx_schedules_start` | US-2 按日查课表 |
| bookings | 约 20 万 | `idx_bookings_user` / `idx_bookings_schedule` | 我的预约 / 名单与统计 |
| waitlist_entries | 约 1 万 | `idx_waitlist_promote` | 取消时按 `id` 升序取第一个 waiting（先来先递补） |
| notification_tasks | 约 30 万 | `idx_ntasks_poll` | 定时任务轮询 pending 且到期的任务 |

## 设计要点

**取消后再预约**：`(schedule_id, user_id)` 唯一约束下，已取消的行会挡住再次 INSERT。处理方式是复用同一行做状态翻转（`canceled → confirmed`），不依赖数据库方言的部分唯一索引，可移植。

**验证码防爆破与一次性消费**：校验在一个事务内完成——先用条件更新占用一次尝试机会：`UPDATE auth_codes SET attempts = attempts + 1 WHERE phone = :phone AND expires_at > now() AND attempts < 5`，影响行数为 0 说明已过期或次数用尽，返回 `TOO_MANY_ATTEMPTS`；再比对摘要，成功则在同一事务内删除该行（一次性消费，防重放）并创建会话。配合发送侧 60 秒限频，每个验证码最多被猜 5 次，6 位数字空间下在线爆破不可行；存摘要不存明文，库泄露时有效期内的验证码也不能被直接读走使用。

**关键事务 1——预约（ADR-001）**：

```sql
BEGIN;
UPDATE schedules SET booked_count = booked_count + 1
 WHERE id = :sid AND status = 'open' AND booked_count < capacity;
-- 影响行数 = 0：回滚，返回 SCHEDULE_FULL 或 SCHEDULE_CANCELED
INSERT INTO bookings (schedule_id, user_id) VALUES (:sid, :uid);
-- 唯一冲突且旧行为 canceled：改为状态翻转；旧行为 confirmed：回滚，返回 BOOKING_EXISTS
INSERT INTO notification_tasks (user_id, type, payload) VALUES (:uid, 'booking_confirmed', :payload);
COMMIT;
```

**关键事务 2——取消预约 + 候补递补**：

```sql
BEGIN;
SELECT status FROM schedules WHERE id = :sid FOR UPDATE;
-- 'canceled'：排期已整体取消，预约已被事务 3 批量处理，幂等返回
UPDATE bookings SET status = 'canceled', canceled_at = now()
 WHERE id = :bid AND user_id = :uid AND status = 'confirmed';
-- 影响行数 = 0：重复取消（并发或客户端重试），幂等返回，不进入递补
SELECT id, user_id FROM waitlist_entries
 WHERE schedule_id = :sid AND status = 'waiting'
 ORDER BY id LIMIT 1 FOR UPDATE;
-- 有候补：置 'promoted'，为其建立 / 翻转 confirmed 预约，写通知任务，booked_count 不变
-- 无候补：UPDATE schedules SET booked_count = booked_count - 1 WHERE id = :sid
COMMIT;
```

对 `status = 'confirmed'` 的条件更新保证 `confirmed → canceled` 只发生一次——没有它，并发或重试的重复取消会触发多次递补，而 `booked_count` 不变，实际确认数将超过容量。

**关键事务 3——取消排期（跨模块用例，由 booking 编排，见 02 文档边界备注）**：

```sql
BEGIN;
UPDATE schedules SET status = 'canceled' WHERE id = :sid AND status = 'open';
-- 影响行数 = 0：已取消或不存在，幂等返回
UPDATE bookings SET status = 'canceled', canceled_at = now()
 WHERE schedule_id = :sid AND status = 'confirmed' RETURNING user_id;
UPDATE waitlist_entries SET status = 'canceled'
 WHERE schedule_id = :sid AND status = 'waiting' RETURNING user_id;
-- 为上面收集到的每位受影响用户各写一条 schedule_canceled 通知任务
COMMIT;
```

`booked_count` 保留历史值即可：事务 1 的条件更新含 `status = 'open'`，已取消的排期不会再接收新预约。单节课容量 ≤ 50，批量更新与通知写入在单事务内的开销可忽略。

**统一锁序防死锁**：三条事务都以排期行为第一个锁目标（事务 1、3 通过条件 UPDATE，事务 2 通过 `SELECT … FOR UPDATE`），之后才锁预约 / 候补行。所有写路径在排期行上天然串行——100 QPS 量级下这是最简单且无死锁的并发方案，也堵死了「取消预约与取消排期交错执行导致递补漏网」的窗口。

## 完成标准自查

- [x] 建表 SQL 可直接执行
- [x] 每张表标注了预期行数，每个索引对应明确的查询模式
- [x] 软删除、时间戳、枚举存储三项全局约定统一
- [x] ADR-001 的约束落到了 DDL（条件更新 + 唯一约束 + CHECK）
- [x] 三条关键事务均幂等（状态条件更新守护转换），加锁顺序统一（先排期行）
- [x] 验证码有尝试上限、一次性消费和摘要存储
