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
    code        VARCHAR(6)  NOT NULL,
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

**关键事务 2——取消 + 候补递补**：同一事务内，把预约置为 `canceled`；按 `idx_waitlist_promote` 取第一个 waiting 条目并 `FOR UPDATE` 锁定。有候补则递补（候补置 `promoted`、为其翻转 / 建立预约、写通知任务，`booked_count` 不变）；无候补则 `booked_count - 1`。

## 完成标准自查

- [x] 建表 SQL 可直接执行
- [x] 每张表标注了预期行数，每个索引对应明确的查询模式
- [x] 软删除、时间戳、枚举存储三项全局约定统一
- [x] ADR-001 的约束落到了 DDL（条件更新 + 唯一约束 + CHECK）
