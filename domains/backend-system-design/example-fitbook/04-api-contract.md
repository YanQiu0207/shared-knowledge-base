# 阶段 4a：API 契约

## 全局约定（先定一次，所有接口遵守）

| 约定项 | 决定 |
| --- | --- |
| 路径前缀与版本 | `/api/v1`，版本进 URL |
| 鉴权 | `Authorization: Bearer <token>`（ADR-002）；管理端接口额外要求 `role = admin`，否则 403 |
| 错误结构 | `{ "code": "SCHEDULE_FULL", "message": "该课程已满员" }`，配合恰当的 HTTP 状态码；错误码全大写蛇形命名 |
| 分页 | 请求 `?page=1&page_size=20`（默认 20，上限 100）；响应 `{ "items": [...], "total": 123 }` |
| 幂等 | 预约创建靠 `(schedule_id, user_id)` 唯一约束天然幂等，重复请求返回 409 `BOOKING_EXISTS`；取消类操作（取消预约、取消排期）以状态条件更新实现幂等，重复请求直接返回成功 |
| 时间格式 | ISO 8601 含时区偏移，如 `2026-07-13T20:00:00+08:00` |

错误码清单：`UNAUTHORIZED`、`FORBIDDEN`、`NOT_FOUND`、`VALIDATION_FAILED`、`RATE_LIMITED`、`TOO_MANY_ATTEMPTS`、`SCHEDULE_FULL`、`SCHEDULE_CANCELED`、`BOOKING_EXISTS`、`TOO_LATE_TO_CANCEL`。

## 接口表

### account 模块

| 方法与路径 | 说明 | 入参 | 成功响应 | 业务错误 |
| --- | --- | --- | --- | --- |
| POST `/auth/codes` | 发送登录验证码 | `{phone}` | 204 | `RATE_LIMITED`（同号 60 秒一次） |
| POST `/auth/sessions` | 验证码登录，新号自动注册；验证码一次性消费 | `{phone, code}` | 200 `{token, user}` | `VALIDATION_FAILED`、`TOO_MANY_ATTEMPTS`（同一验证码错 5 次作废，需重新获取） |
| DELETE `/auth/sessions` | 登出 | — | 204 | — |

### catalog 模块

| 方法与路径 | 说明 | 入参 | 成功响应 | 业务错误 |
| --- | --- | --- | --- | --- |
| GET `/schedules?date=2026-07-13` | 按日查课表 | query: `date` | 200 `{items: [{id, course_name, coach_name, start_time, end_time, capacity, remaining, my_status}]}` | — |
| POST `/courses` 【管理】 | 创建课程 | `{name, coach_id, duration_minutes, description}` | 201 `{course}` | — |
| POST `/courses/{id}/schedules` 【管理】 | 为课程创建一节排期 | `{start_time, capacity}` | 201 `{schedule}` | `VALIDATION_FAILED`（时段重复） |
| PATCH `/schedules/{id}` 【管理】 | 取消一节排期：同事务级联取消全部有效预约与候补，并为每位受影响会员写通知任务（05 文档事务 3），幂等 | `{status: "canceled"}` | 200 | — |

`my_status` 为当前登录会员在该节课的状态：`none / booked / waitlisted`，供前端渲染按钮。

### booking 模块

| 方法与路径 | 说明 | 入参 | 成功响应 | 业务错误 |
| --- | --- | --- | --- | --- |
| POST `/bookings` | 预约一节课 | `{schedule_id}` | 201 `{booking}` | `SCHEDULE_FULL`、`SCHEDULE_CANCELED`、`BOOKING_EXISTS` |
| DELETE `/bookings/{id}` | 取消预约（重复取消幂等返回 204） | — | 204 | `TOO_LATE_TO_CANCEL`（开课前 2 小时内） |
| GET `/bookings?status=upcoming` | 我的预约列表 | query: `status` | 200 分页结构 | — |
| POST `/waitlist` | 加入候补 | `{schedule_id}` | 201 `{entry}` | `BOOKING_EXISTS`（已约到或已在候补） |
| DELETE `/waitlist/{id}` | 退出候补 | — | 204 | — |
| GET `/schedules/{id}/bookings` 【管理】 | 某节课预约名单 | — | 200 `{items: [{user_name, phone, booked_at}]}` | — |

notification 模块无对外接口（内部定时任务，见 ADR-003）。

## 需求覆盖检查

| 故事 | 覆盖方式 |
| --- | --- |
| US-1 | POST /auth/codes、POST /auth/sessions |
| US-2 | GET /schedules |
| US-3 | POST /bookings |
| US-4 | DELETE /bookings/{id} |
| US-5 | POST /courses、POST /courses/{id}/schedules、PATCH /schedules/{id} |
| US-6 | GET /schedules/{id}/bookings |
| US-7 | 无接口，由 ADR-001 的约束机制保障 |
| US-8 | POST /waitlist、DELETE /waitlist/{id} |
| US-9 | 无接口，由 notification 定时任务投递（ADR-003） |

## 完成标准自查

- [x] 每个 Must / Should 故事都有对应接口或明确的机制保障
- [x] 全局约定一次定清，接口表未出现约定外的私有风格
- [x] 调用方拿本契约可直接 mock（路径、入参、响应、错误码齐全）
