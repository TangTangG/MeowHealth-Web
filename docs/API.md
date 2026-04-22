# MeowHealth API 文档

> 版本: v1.0 (Phase 3)  
> 更新日期: 2026-04-22

---

## 目录

1. [基础信息](#基础信息)
2. [认证说明](#认证说明)
3. [猫咪接口 (Cats)](#猫咪接口-cats)
4. [上传接口 (Uploads)](#上传接口-uploads)
5. [报告接口 (Reports)](#报告接口-reports)
6. [错误码表](#错误码表)

---

## 基础信息

| 项目 | 说明 |
|------|------|
| **Base URL** | `http://localhost:8000` (开发环境) |
| **Content-Type** | `application/json` (JSON 接口) / `multipart/form-data` (文件上传) |
| **数据格式** | 所有请求/响应均使用 JSON，字段采用 `snake_case` |
| **时区** | 服务器使用 UTC，客户端需自行转换 |

### 通用响应格式

所有成功响应直接返回对应资源对象或数组。错误响应统一格式：

```json
{
  "detail": "错误描述信息"
}
```

---

## 认证说明

> ⚠️ **当前版本 (Phase 3) 暂不要求认证**，所有接口均为开放访问。  
> Phase 4 将引入基于 JWT Token 的用户认证系统，届时需在请求头中携带：

```
Authorization: Bearer <jwt_token>
```

---

## 猫咪接口 (Cats)

前缀: `/cats`

### GET /cats/

**功能**: 获取所有猫咪列表（支持分页）

#### 请求参数 (Query)

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `skip` | int | 否 | 0 | 跳过记录数 |
| `limit` | int | 否 | 100 | 返回最大记录数 |

#### 响应格式

`200 OK` — `CatResponse[]`

```json
[
  {
    "id": "cat-uuid-1",
    "name": "咪咪",
    "breed": "英短",
    "birthday": "2022-03-15T00:00:00",
    "gender": "female",
    "is_neutered": true,
    "photo_path": "/uploads/cat-photo-1.jpg",
    "target_weight_min": 3.5,
    "target_weight_max": 4.5,
    "created_at": "2026-04-01T10:00:00",
    "updated_at": "2026-04-01T10:00:00"
  }
]
```

---

### POST /cats/

**功能**: 创建新猫咪

#### 请求体 (JSON)

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | ✅ | 猫咪名字 |
| `breed` | string | ✅ | 品种 |
| `birthday` | datetime | ✅ | 生日 (ISO 8601 格式) |
| `gender` | string | ✅ | 性别 (`male` / `female`) |
| `is_neutered` | bool | 否 | 是否绝育，默认 `false` |
| `photo_path` | string | 否 | 照片路径 |
| `target_weight_min` | float | 否 | 目标体重下限 (kg) |
| `target_weight_max` | float | 否 | 目标体重上限 (kg) |

#### 请求示例

```json
{
  "name": "咪咪",
  "breed": "英短",
  "birthday": "2022-03-15T00:00:00",
  "gender": "female",
  "is_neutered": true,
  "target_weight_min": 3.5,
  "target_weight_max": 4.5
}
```

#### 响应格式

`200 OK` — `CatResponse` (同 GET 列表中的单条结构)

---

### GET /cats/{cat_id}

**功能**: 获取单个猫咪详情

#### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `cat_id` | string | 猫咪 UUID |

#### 响应格式

`200 OK` — `CatResponse`

`404 Not Found` — 猫咪不存在或已删除

---

### PUT /cats/{cat_id}

**功能**: 更新猫咪信息

#### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `cat_id` | string | 猫咪 UUID |

#### 请求体

同 `POST /cats/`，全字段可选（传入则覆盖）

#### 响应格式

`200 OK` — `CatResponse`

`404 Not Found` — 猫咪不存在或已删除

---

### DELETE /cats/{cat_id}

**功能**: 软删除猫咪（设置 `deleted_at` 时间戳）

#### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `cat_id` | string | 猫咪 UUID |

#### 响应格式

`200 OK`

```json
{
  "message": "Cat deleted successfully"
}
```

`404 Not Found` — 猫咪不存在或已删除

---

### GET /cats/{cat_id}/weights

**功能**: 获取猫咪体重历史

#### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `cat_id` | string | 猫咪 UUID |

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `limit` | int | 否 | 30 | 返回记录数，范围 1~365 |

#### 响应格式

`200 OK` — `WeightLogResponse[]`

```json
[
  {
    "id": "weight-uuid-1",
    "cat_id": "cat-uuid-1",
    "date": "2026-04-01T08:00:00",
    "value": 4.2,
    "note": "饭后称重",
    "created_at": "2026-04-01T08:00:00",
    "updated_at": "2026-04-01T08:00:00"
  }
]
```

---

### POST /cats/{cat_id}/weights

**功能**: 记录猫咪体重

#### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `cat_id` | string | 猫咪 UUID |

#### 请求体 (JSON)

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `date` | datetime | ✅ | 称重日期 |
| `value` | float | ✅ | 体重 (kg) |
| `note` | string | 否 | 备注 |

#### 响应格式

`200 OK` — `WeightLogResponse`

---

### GET /cats/{cat_id}/reminders

**功能**: 获取猫咪待办提醒

#### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `cat_id` | string | 猫咪 UUID |

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `include_completed` | bool | 否 | `false` | 是否包含已完成提醒 |

#### 响应格式

`200 OK` — `ReminderResponse[]`

```json
[
  {
    "id": "reminder-uuid-1",
    "cat_id": "cat-uuid-1",
    "title": "驱虫",
    "description": "每月一次体外驱虫",
    "reminder_type": "deworming",
    "due_date": "2026-05-01T10:00:00",
    "is_completed": false,
    "completed_at": null,
    "created_at": "2026-04-01T10:00:00",
    "updated_at": "2026-04-01T10:00:00"
  }
]
```

---

### POST /cats/{cat_id}/reminders

**功能**: 创建待办提醒

#### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `cat_id` | string | 猫咪 UUID |

#### 请求体 (JSON)

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `title` | string | ✅ | 提醒标题 |
| `description` | string | 否 | 详细描述 |
| `reminder_type` | string | ✅ | 提醒类型 |
| `due_date` | datetime | ✅ | 截止日期 |
| `is_completed` | bool | 否 | 是否已完成，默认 `false` |

#### 响应格式

`200 OK` — `ReminderResponse`

---

## 上传接口 (Uploads)

前缀: `/api/uploads`

### POST /api/uploads/

**功能**: 上传化验单文件（图片/PDF），返回文件元数据

#### 请求格式

`Content-Type: multipart/form-data`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file` | File | ✅ | 文件内容 |

#### 支持文件类型

| MIME 类型 | 扩展名 | 说明 |
|-----------|--------|------|
| `image/jpeg` | `.jpg` | JPEG 图片 |
| `image/png` | `.png` | PNG 图片 |
| `application/pdf` | `.pdf` | PDF 文档 |

#### 限制

- **文件大小上限**: 10 MB
- **存储位置**: `uploads/` 目录（相对服务器启动路径）

#### 响应格式

`200 OK`

```json
{
  "file_id": "550e8400-e29b-41d4-a716-446655440000",
  "file_path": "uploads/550e8400-e29b-41d4-a716-446655440000.pdf",
  "file_name": "血常规报告.pdf",
  "mime_type": "application/pdf",
  "file_size": 245760
}
```

---

## 报告接口 (Reports)

前缀: `/api/reports`

### POST /api/reports/analyze

**功能**: 分析上传的文件并创建健康报告（AI 自动分析化验单）

#### 请求体 (JSON)

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `cat_id` | string | ✅ | 关联猫咪 UUID |
| `file_path` | string | ✅ | 上传后的文件路径 |
| `file_name` | string | ✅ | 原始文件名 |
| `mime_type` | string | ✅ | 文件 MIME 类型 |
| `file_size` | int | ✅ | 文件大小 (bytes) |

#### 请求示例

```json
{
  "cat_id": "cat-uuid-1",
  "file_path": "uploads/550e8400-e29b-41d4-a716-446655440000.pdf",
  "file_name": "血常规报告.pdf",
  "mime_type": "application/pdf",
  "file_size": 245760
}
```

#### 响应格式

`200 OK` — `ReportResponse`

```json
{
  "id": "report-uuid-1",
  "cat_id": "cat-uuid-1",
  "date": "2026-04-22T15:30:00",
  "type": "lab_report",
  "title": "化验单分析 - 血常规报告.pdf",
  "note": null,
  "ai_summary": "白细胞计数略高，可能存在轻微炎症...",
  "actionable_advice": [
    "建议 3 天后复查白细胞",
    "注意观察猫咪精神状态"
  ],
  "indicators": [
    {
      "id": "indicator-uuid-1",
      "record_id": "report-uuid-1",
      "name": "WBC",
      "display_name": "白细胞计数",
      "value": 12.5,
      "unit": "10^9/L",
      "reference_min": 5.5,
      "reference_max": 19.5,
      "is_abnormal": false,
      "explanation": "白细胞在正常范围内",
      "created_at": "2026-04-22T15:30:00",
      "updated_at": "2026-04-22T15:30:00"
    }
  ],
  "attachments": [
    {
      "id": "attachment-uuid-1",
      "file_path": "uploads/550e8400-e29b-41d4-a716-446655440000.pdf",
      "file_name": "血常规报告.pdf",
      "mime_type": "application/pdf",
      "file_size": 245760,
      "created_at": "2026-04-22T15:30:00"
    }
  ],
  "created_at": "2026-04-22T15:30:00",
  "updated_at": "2026-04-22T15:30:00"
}
```

`400 Bad Request` — AI 分析失败或文件格式不支持

---

### GET /api/reports/

**功能**: 列出所有报告（可按猫咪筛选）

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `cat_id` | string | 否 | — | 筛选特定猫咪的报告 |

#### 响应格式

`200 OK` — `ReportResponse[]`（按 `date` 降序排列）

---

### GET /api/reports/{report_id}

**功能**: 获取单个报告详情

#### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `report_id` | string | 报告 UUID |

#### 响应格式

`200 OK` — `ReportResponse`

`404 Not Found` — 报告不存在

---

### POST /api/reports/{report_id}/chat

**功能**: 与 AI 就报告内容进行对话

#### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `report_id` | string | 报告 UUID |

#### 请求体 (JSON)

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `content` | string | ✅ | 用户提问内容 |

#### 请求示例

```json
{
  "content": "白细胞偏高是什么意思？"
}
```

#### 响应格式

`200 OK` — `ChatMessageResponse`（AI 回复消息）

```json
{
  "id": "chat-uuid-2",
  "record_id": "report-uuid-1",
  "role": "model",
  "content": "白细胞计数偏高通常表示身体正在对抗感染或炎症...",
  "model_name": "gemini-2.0-flash",
  "token_usage": null,
  "created_at": "2026-04-22T15:35:00"
}
```

`404 Not Found` — 报告不存在

---

### GET /api/reports/{report_id}/chat/history

**功能**: 获取某报告下的完整对话历史

#### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `report_id` | string | 报告 UUID |

#### 响应格式

`200 OK` — `ChatMessageResponse[]`（按时间升序排列）

```json
[
  {
    "id": "chat-uuid-1",
    "record_id": "report-uuid-1",
    "role": "user",
    "content": "白细胞偏高是什么意思？",
    "model_name": null,
    "token_usage": null,
    "created_at": "2026-04-22T15:35:00"
  },
  {
    "id": "chat-uuid-2",
    "record_id": "report-uuid-1",
    "role": "model",
    "content": "白细胞计数偏高通常表示身体正在对抗感染或炎症...",
    "model_name": "gemini-2.0-flash",
    "token_usage": null,
    "created_at": "2026-04-22T15:35:00"
  }
]
```

---

### DELETE /api/reports/{report_id}

**功能**: 删除报告（级联删除关联的指标、附件、聊天记录）

#### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `report_id` | string | 报告 UUID |

#### 响应格式

`200 OK`

```json
{
  "message": "Report deleted successfully"
}
```

`404 Not Found` — 报告不存在

---

## 错误码表

| HTTP 状态码 | 含义 | 触发场景 |
|-------------|------|----------|
| `200` | 成功 | 请求正常处理 |
| `400` | 请求参数错误 | 文件类型不支持、文件过大、AI 分析失败、缺少必填字段 |
| `404` | 资源不存在 | 猫咪/报告/记录未找到或已删除 |
| `422` | 验证错误 | 请求体 JSON 格式错误或字段类型不匹配 |
| `500` | 服务器内部错误 | 数据库异常、AI 服务不可用等 |

### 常见错误示例

**400 — 不支持的文件类型**
```json
{
  "detail": "不支持的文件类型: image/webp"
}
```

**400 — 文件过大**
```json
{
  "detail": "文件大小超过10MB限制"
}
```

**400 — AI 分析失败**
```json
{
  "detail": "无法解析化验单内容，请检查文件清晰度"
}
```

**404 — 猫咪不存在**
```json
{
  "detail": "Cat not found"
}
```

**404 — 报告不存在**
```json
{
  "detail": "报告不存在"
}
```

---

## 数据模型速查

### Cat

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | UUID |
| `name` | string | 名字 |
| `breed` | string | 品种 |
| `birthday` | datetime | 生日 |
| `gender` | string | `male` / `female` |
| `is_neutered` | bool | 是否绝育 |
| `photo_path` | string | 照片路径 |
| `target_weight_min` | float | 目标体重下限 (kg) |
| `target_weight_max` | float | 目标体重上限 (kg) |
| `created_at` | datetime | 创建时间 |
| `updated_at` | datetime | 更新时间 |

### HealthIndicator (健康指标)

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | UUID |
| `record_id` | string | 关联报告 ID |
| `name` | string | 指标代码 (如 `WBC`) |
| `display_name` | string | 显示名称 (如 `白细胞计数`) |
| `value` | float | 检测值 |
| `unit` | string | 单位 |
| `reference_min` | float | 参考范围下限 |
| `reference_max` | float | 参考范围上限 |
| `is_abnormal` | bool | 是否异常 |
| `explanation` | string | 解释说明 |

### ChatMessage (聊天消息)

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | UUID |
| `record_id` | string | 关联报告 ID |
| `role` | string | `user` / `model` |
| `content` | string | 消息内容 |
| `model_name` | string | AI 模型名称 |
| `token_usage` | int | Token 使用量 |
| `created_at` | datetime | 创建时间 |
