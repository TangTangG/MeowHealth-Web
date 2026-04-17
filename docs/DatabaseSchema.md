# MeowHealth Web 数据库 Schema 设计文档

## 1. 设计目标与原则

- **兼容性**：同时支持 SQLite（默认，方便单机私有化部署）和 PostgreSQL（可选，便于后续扩展）。
- **一致性**：Schema 设计尽量对齐 iOS 版 SwiftData 模型，降低认知成本与数据迁移难度。
- **完整性**：覆盖 PRD 中全部核心功能（猫咪档案、健康记录流水、AI 化验单分析、提醒、喂食记录、猫粮库）。
- **可审计**：每张表均包含 `created_at`、`updated_at`；部分高频写表增加 `deleted_at` 软删除支持，便于误删恢复与审计。
- **扩展性**：为 Web 版新增特性（如 AI 对话上下文、原始附件版本管理）预留字段。

## 2. 数据库选型与 ORM

- **ORM**：SQLAlchemy 2.0（Declarative Base + Type Annotated）。
- **主键策略**：统一使用 `UUID`（`uuid.uuid4`），与 iOS 版保持一致，避免跨平台主键冲突。
- **时间字段**：统一使用 `DateTime(timezone=True)`，SQLite 下 SQLAlchemy 会自动处理为不带时区的文本存储，应用层统一使用 UTC。
- **JSON 字段**：使用 SQLAlchemy `JSON` 类型，SQLite 下会自动 fallback 到 `JSON` 扩展或 Text 存储。

## 3. ER 图概览（文字版）

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   cat_foods     │     │      cats       │     │   reminders     │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ id (PK)         │◄────│ id (PK)         │◄────│ cat_id (FK)     │
│ ...             │     │ name            │     │ title           │
└─────────────────┘     │ birthday        │     │ due_date        │
                        │ ...             │     │ ...             │
                        └─────────────────┘     └─────────────────┘
                                  ▲
                                  │
            ┌─────────────────────┼─────────────────────┐
            │                     │                     │
            ▼                     ▼                     ▼
   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
   │   weight_logs   │  │ health_records  │  │  feeding_logs   │
   ├─────────────────┤  ├─────────────────┤  ├─────────────────┤
   │ id (PK)         │  │ id (PK)         │  │ id (PK)         │
   │ cat_id (FK)     │  │ cat_id (FK)     │  │ cat_id (FK)     │
   │ date            │  │ date            │  │ timestamp       │
   │ value           │  │ type            │  │ type            │
   │ ...             │  │ title           │  │ amount          │
   └─────────────────┘  │ ...             │  │ ...             │
                        └─────────────────┘  └─────────────────┘
                               │
                               │
                               ▼
                        ┌─────────────────┐
                        │health_indicators│
                        ├─────────────────┤
                        │ id (PK)         │
                        │ record_id (FK)  │
                        │ name            │
                        │ value           │
                        │ ...             │
                        └─────────────────┘
                               │
                               │
                               ▼
                        ┌─────────────────┐
                        │report_attachments│
                        ├─────────────────┤
                        │ id (PK)         │
                        │ record_id (FK)  │
                        │ file_path       │
                        │ ...             │
                        └─────────────────┘
```

## 4. 表详细设计

### 4.1 `cats` — 猫咪主档案

存储每只猫咪的核心身份信息，对应 iOS 版 `Cat` 模型。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | UUID | PK | 主键，与 iOS 版 `UUID` 对齐 |
| `name` | VARCHAR(100) | NOT NULL | 猫咪昵称 |
| `breed` | VARCHAR(100) | NOT NULL | 品种 |
| `birthday` | DATE | NOT NULL | 生日，用于计算年龄 |
| `gender` | VARCHAR(20) | NOT NULL | `male` / `female` / `unknown` |
| `is_neutered` | BOOLEAN | NOT NULL DEFAULT FALSE | 是否绝育 |
| `photo_path` | VARCHAR(500) | NULL | 头像文件路径（Web 版将 iOS 的 `photoData: Data` 改为文件路径存储） |
| `target_weight_min` | DOUBLE | NULL | 理想体重下限（kg） |
| `target_weight_max` | DOUBLE | NULL | 理想体重上限（kg） |
| `created_at` | DateTime | NOT NULL DEFAULT now() | 创建时间 |
| `updated_at` | DateTime | NOT NULL DEFAULT now() | 更新时间 |
| `deleted_at` | DateTime | NULL | 软删除时间 |

**索引建议**：
- `idx_cats_deleted_at`：筛除已软删记录。

**级联策略**：
- `cats` 被删除（软删）时，关联的 `weight_logs`、`health_records`、`feeding_logs` 一同软删或物理删除，由应用层事务控制（关系型数据库级联删除更适合物理删除；若用软删，建议在应用层统一处理）。

**iOS 差异说明**：
- `photoData`（二进制 Data）改为 `photo_path`（文件路径），Web 端更适合文件系统或对象存储存放图片。

---

### 4.2 `health_records` — 健康记录流水

对应 iOS 版 `HealthRecord` 模型，是医疗/健康事件的统一流水表。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | UUID | PK | 主键 |
| `cat_id` | UUID | FK → cats.id | 关联猫咪 |
| `date` | DateTime | NOT NULL | 记录日期 |
| `type` | VARCHAR(50) | NOT NULL | `vaccine` / `deworming` / `lab_report` / `clinic_visit` / `surgery` |
| `title` | VARCHAR(200) | NOT NULL | 记录标题 |
| `note` | TEXT | NULL | 用户备注 |
| `ai_summary` | TEXT | NULL | AI 生成的一句话核心结论 |
| `actionable_advice` | JSON | NULL | AI 生成的 actionable 建议列表（对应 iOS 版 `[String]`） |
| `created_at` | DateTime | NOT NULL DEFAULT now() | 创建时间 |
| `updated_at` | DateTime | NOT NULL DEFAULT now() | 更新时间 |
| `deleted_at` | DateTime | NULL | 软删除时间 |

**索引建议**：
- `idx_health_records_cat_id_date`：按猫咪和时间范围查询最常用。
- `idx_health_records_type`：按类型筛选（如只看化验单）。
- `idx_health_records_deleted_at`：软删过滤。

**级联策略**：
- `health_records` 物理删除时，级联删除关联的 `health_indicators` 和 `report_attachments`（`ON DELETE CASCADE`）。

---

### 4.3 `health_indicators` — 健康指标明细

对应 iOS 版 `HealthIndicator` 模型，专门存储化验单或体检中的各项指标。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | UUID | PK | 主键 |
| `record_id` | UUID | FK → health_records.id | 关联的健康记录 |
| `name` | VARCHAR(100) | NOT NULL | 指标英文/标准代码名（如 `CREA`、`WBC`） |
| `display_name` | VARCHAR(200) | NOT NULL | 展示名称（如 `肌酐 (CREA)`） |
| `value` | DOUBLE | NULL | 数值结果 |
| `unit` | VARCHAR(50) | NOT NULL | 单位（如 `μmol/L`、`10^9/L`） |
| `reference_min` | DOUBLE | NULL | 参考范围下限（Web 版新增，用于异常判断与前端高亮） |
| `reference_max` | DOUBLE | NULL | 参考范围上限（Web 版新增） |
| `is_abnormal` | BOOLEAN | NOT NULL DEFAULT FALSE | 是否异常 |
| `explanation` | TEXT | NULL | AI 对该指标的白话解释 |
| `created_at` | DateTime | NOT NULL DEFAULT now() | 创建时间 |
| `updated_at` | DateTime | NOT NULL DEFAULT now() | 更新时间 |

**索引建议**：
- `idx_health_indicators_record_id`：按记录查询指标列表。
- `idx_health_indicators_name_cat_id`（通过 JOIN health_records 实现）：用于「某猫咪某指标历史趋势」查询。

**级联策略**：
- `ON DELETE CASCADE` 跟随 `health_records`。

**Web 新增**：
- `reference_min`、`reference_max`：iOS 版之前可能把参考范围藏在 `explanation` 里，Web 版将其结构化，便于前端图表绘制与异常高亮。

---

### 4.4 `report_attachments` — 化验单/报告原始附件

Web 版新增表，用于管理原始文件（PDF、JPG、PNG）的存储路径。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | UUID | PK | 主键 |
| `record_id` | UUID | FK → health_records.id | 关联健康记录 |
| `file_path` | VARCHAR(500) | NOT NULL | 服务器本地存储路径（或对象存储 URL） |
| `file_name` | VARCHAR(255) | NOT NULL | 原始文件名 |
| `mime_type` | VARCHAR(100) | NOT NULL | `application/pdf`、`image/jpeg` 等 |
| `file_size` | INTEGER | NULL | 文件大小（字节） |
| `created_at` | DateTime | NOT NULL DEFAULT now() | 创建时间 |

**索引建议**：
- `idx_report_attachments_record_id`：按记录加载附件列表。

**级联策略**：
- `ON DELETE CASCADE` 跟随 `health_records`。

**iOS 差异说明**：
- iOS 版使用 `attachmentPaths: [String]` 直接存在 `HealthRecord` 里。Web 版拆分为独立表，便于扩展（如增加对象存储 URL、缩略图、OCR 文本缓存等）。

---

### 4.5 `weight_logs` — 体重记录

对应 iOS 版 `WeightLog` 模型。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | UUID | PK | 主键 |
| `cat_id` | UUID | FK → cats.id | 关联猫咪 |
| `date` | DATE | NOT NULL | 记录日期 |
| `value` | DOUBLE | NOT NULL | 体重（kg） |
| `note` | VARCHAR(500) | NULL | 备注 |
| `created_at` | DateTime | NOT NULL DEFAULT now() | 创建时间 |
| `updated_at` | DateTime | NOT NULL DEFAULT now() | 更新时间 |

**索引建议**：
- `idx_weight_logs_cat_id_date`：生成体重趋势图的核心查询。

---

### 4.6 `feeding_logs` — 喂食记录

对应 iOS 版 `FeedingLog` 模型。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | UUID | PK | 主键 |
| `cat_id` | UUID | FK → cats.id | 关联猫咪 |
| `timestamp` | DateTime | NOT NULL | 喂食时间点 |
| `type` | VARCHAR(50) | NOT NULL | `dry_food` / `wet_food` / `treat` / `water` |
| `amount` | DOUBLE | NOT NULL | 数量（克 g 或毫升 ml） |
| `note` | VARCHAR(500) | NULL | 备注 |
| `created_at` | DateTime | NOT NULL DEFAULT now() | 创建时间 |
| `updated_at` | DateTime | NOT NULL DEFAULT now() | 更新时间 |

**索引建议**：
- `idx_feeding_logs_cat_id_timestamp`：按时间范围查询喂食流水。

---

### 4.7 `reminders` — 提醒/待办事项

Web 版新增表，用于替代 iOS 版的 `UNNotificationManager` 本地推送逻辑，改为数据库级提醒履约。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | UUID | PK | 主键 |
| `cat_id` | UUID | FK → cats.id NULLABLE | 关联猫咪（可为空，表示全局提醒） |
| `title` | VARCHAR(200) | NOT NULL | 提醒标题 |
| `description` | TEXT | NULL | 详细描述 |
| `reminder_type` | VARCHAR(50) | NOT NULL | `vaccine` / `deworming` / `custom` |
| `due_date` | DATE | NOT NULL | 到期日 |
| `is_completed` | BOOLEAN | NOT NULL DEFAULT FALSE | 是否已完成 |
| `completed_at` | DateTime | NULL | 完成时间 |
| `created_at` | DateTime | NOT NULL DEFAULT now() | 创建时间 |
| `updated_at` | DateTime | NOT NULL DEFAULT now() | 更新时间 |

**索引建议**：
- `idx_reminders_cat_id_due_date`：Dashboard 待办列表默认查询。
- `idx_reminders_is_completed_due_date`：快速筛选「未完成的近期提醒」。

---

### 4.8 `ai_chat_messages` — AI 对话上下文（悬浮助手）

Web 版新增表，用于保存用户在查看化验单时与 AI 悬浮助手的对话历史。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | UUID | PK | 主键 |
| `record_id` | UUID | FK → health_records.id NULLABLE | 关联的化验单记录（为空时表示全局对话） |
| `role` | VARCHAR(20) | NOT NULL | `user` / `model` / `system` |
| `content` | TEXT | NOT NULL | 对话内容 |
| `model_name` | VARCHAR(100) | NULL | 使用的模型（如 `gemini-2.0-flash`） |
| `token_usage` | INTEGER | NULL | 可选：记录 token 消耗 |
| `created_at` | DateTime | NOT NULL DEFAULT now() | 创建时间 |

**索引建议**：
- `idx_ai_chat_messages_record_id_created_at`：按记录加载对话历史。

---

### 4.9 `cat_foods` — 猫粮数据库

对应 iOS 版 `CatFood` 模型。该表在 Web 版中优先级较低，可先作为静态参考表或管理员维护表处理。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | UUID | PK | 主键 |
| `brand` | VARCHAR(200) | NOT NULL | 品牌 |
| `name` | VARCHAR(200) | NOT NULL | 产品名 |
| `food_type` | VARCHAR(50) | NOT NULL | `dry` / `wet` / `freeze_dried` / `raw` / `semi_moist` |
| `life_stages` | JSON | NULL | 适用阶段列表（如 `["kitten", "adult"]`） |
| `special_formulas` | JSON | NULL | 特殊配方列表 |
| `nutrition_facts` | JSON | NULL | 营养成分结构化 JSON |
| `price` | DOUBLE | NULL | 价格（元） |
| `weight` | DOUBLE | NULL | 规格重量（kg） |
| `origin` | VARCHAR(100) | NULL | 产地 |
| `main_ingredients` | JSON | NULL | 主要成分列表 |
| `is_recommended` | BOOLEAN | NOT NULL DEFAULT FALSE | 是否推荐 |
| `rating` | DOUBLE | NULL | 评分 |
| `review_count` | INTEGER | NULL | 评价数 |
| `created_at` | DateTime | NOT NULL DEFAULT now() | 创建时间 |
| `updated_at` | DateTime | NOT NULL DEFAULT now() | 更新时间 |

**说明**：
- iOS 版中 `CatFood` 带有大量计算属性（`pricePerKg`、`carbohydrates`、`metabolizableEnergy`），Web 版建议将这些逻辑移到后端服务层或前端计算，不直接持久化，保持 schema 简洁。

---

## 5. SQLAlchemy 2.0 模型代码（推荐实现）

```python
from datetime import datetime
from typing import Optional, List
import uuid

from sqlalchemy import (
    create_engine, ForeignKey, String, Text, Double, Boolean,
    DateTime, JSON, Integer, func, Index
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Cat(Base):
    __tablename__ = "cats"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100))
    breed: Mapped[str] = mapped_column(String(100))
    birthday: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    gender: Mapped[str] = mapped_column(String(20))
    is_neutered: Mapped[bool] = mapped_column(Boolean, default=False)
    photo_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    target_weight_min: Mapped[Optional[float]] = mapped_column(Double, nullable=True)
    target_weight_max: Mapped[Optional[float]] = mapped_column(Double, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_cats_deleted_at", "deleted_at"),
    )


class HealthRecord(Base):
    __tablename__ = "health_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cat_id: Mapped[str] = mapped_column(ForeignKey("cats.id", ondelete="CASCADE"))
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    type: Mapped[str] = mapped_column(String(50))  # vaccine, deworming, lab_report, clinic_visit, surgery
    title: Mapped[str] = mapped_column(String(200))
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    actionable_advice: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    indicators: Mapped[List["HealthIndicator"]] = relationship(back_populates="record", cascade="all, delete-orphan")
    attachments: Mapped[List["ReportAttachment"]] = relationship(back_populates="record", cascade="all, delete-orphan")
    chat_messages: Mapped[List["AIChatMessage"]] = relationship(back_populates="record", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_health_records_cat_id_date", "cat_id", "date"),
        Index("idx_health_records_type", "type"),
        Index("idx_health_records_deleted_at", "deleted_at"),
    )


class HealthIndicator(Base):
    __tablename__ = "health_indicators"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    record_id: Mapped[str] = mapped_column(ForeignKey("health_records.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100))
    display_name: Mapped[str] = mapped_column(String(200))
    value: Mapped[Optional[float]] = mapped_column(Double, nullable=True)
    unit: Mapped[str] = mapped_column(String(50))
    reference_min: Mapped[Optional[float]] = mapped_column(Double, nullable=True)
    reference_max: Mapped[Optional[float]] = mapped_column(Double, nullable=True)
    is_abnormal: Mapped[bool] = mapped_column(Boolean, default=False)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    record: Mapped["HealthRecord"] = relationship(back_populates="indicators")

    __table_args__ = (
        Index("idx_health_indicators_record_id", "record_id"),
    )


class ReportAttachment(Base):
    __tablename__ = "report_attachments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    record_id: Mapped[str] = mapped_column(ForeignKey("health_records.id", ondelete="CASCADE"))
    file_path: Mapped[str] = mapped_column(String(500))
    file_name: Mapped[str] = mapped_column(String(255))
    mime_type: Mapped[str] = mapped_column(String(100))
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    record: Mapped["HealthRecord"] = relationship(back_populates="attachments")

    __table_args__ = (
        Index("idx_report_attachments_record_id", "record_id"),
    )


class WeightLog(Base):
    __tablename__ = "weight_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cat_id: Mapped[str] = mapped_column(ForeignKey("cats.id", ondelete="CASCADE"))
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    value: Mapped[float] = mapped_column(Double)
    note: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_weight_logs_cat_id_date", "cat_id", "date"),
    )


class FeedingLog(Base):
    __tablename__ = "feeding_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cat_id: Mapped[str] = mapped_column(ForeignKey("cats.id", ondelete="CASCADE"))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    type: Mapped[str] = mapped_column(String(50))  # dry_food, wet_food, treat, water
    amount: Mapped[float] = mapped_column(Double)
    note: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_feeding_logs_cat_id_timestamp", "cat_id", "timestamp"),
    )


class Reminder(Base):
    __tablename__ = "reminders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cat_id: Mapped[Optional[str]] = mapped_column(ForeignKey("cats.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reminder_type: Mapped[str] = mapped_column(String(50))  # vaccine, deworming, custom
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_reminders_cat_id_due_date", "cat_id", "due_date"),
        Index("idx_reminders_is_completed_due_date", "is_completed", "due_date"),
    )


class AIChatMessage(Base):
    __tablename__ = "ai_chat_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    record_id: Mapped[Optional[str]] = mapped_column(ForeignKey("health_records.id", ondelete="CASCADE"), nullable=True)
    role: Mapped[str] = mapped_column(String(20))  # user, model, system
    content: Mapped[str] = mapped_column(Text)
    model_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    token_usage: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    record: Mapped[Optional["HealthRecord"]] = relationship(back_populates="chat_messages")

    __table_args__ = (
        Index("idx_ai_chat_messages_record_id_created_at", "record_id", "created_at"),
    )


class CatFood(Base):
    __tablename__ = "cat_foods"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    brand: Mapped[str] = mapped_column(String(200))
    name: Mapped[str] = mapped_column(String(200))
    food_type: Mapped[str] = mapped_column(String(50))
    life_stages: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    special_formulas: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    nutrition_facts: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    price: Mapped[Optional[float]] = mapped_column(Double, nullable=True)
    weight: Mapped[Optional[float]] = mapped_column(Double, nullable=True)
    origin: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    main_ingredients: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    is_recommended: Mapped[bool] = mapped_column(Boolean, default=False)
    rating: Mapped[Optional[float]] = mapped_column(Double, nullable=True)
    review_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

## 6. 关键设计决策说明

| 决策点 | 说明 |
|--------|------|
| **UUID 主键** | 与 iOS 版保持一致，方便未来数据互通；同时避免单机 SQLite 下自增 ID 的冲突问题。 |
| **附件独立成表** | iOS 用 `[String]` 直接存路径，Web 版拆分为 `report_attachments`，便于后续扩展（如缩略图、OCR 文本缓存）。 |
| **参考范围结构化** | `health_indicators` 新增 `reference_min` / `reference_max`，前端可直接用数值做异常高亮和图表渲染。 |
| **软删除策略** | `cats`、`health_records` 增加 `deleted_at`，便于误删恢复；其他日志类表数据价值相对较低，暂不做软删。 |
| ** reminders 替代本地通知** | Web 无法直接使用 iOS `UNNotificationManager`，改用数据库级 `reminders` 表，登录即拉取；后续可对接 Web Push 或 Telegram Bot 做外部提醒。 |
| **AI 对话上下文持久化** | `ai_chat_messages` 支持按 `record_id` 关联，实现报告详情页悬浮助手的多轮对话记忆。 |

## 7. 后续步骤建议

1. **初始化迁移脚本**：使用 Alembic 管理 schema 版本。
2. **种子数据**：为 `cat_foods` 表准备一批初始化数据（可直接复用 iOS 版 `CatFood.commonCatFoods`）。
3. **API 设计**：基于本 schema 设计 FastAPI Pydantic Schema 与 CRUD 接口。
