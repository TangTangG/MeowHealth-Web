# Backend Infrastructure (Phase 1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Initialize the FastAPI backend project, configure SQLAlchemy with SQLite, set up CORS, and define the base database models for CatProfile and HealthRecord.

**Architecture:** Standard FastAPI layering (routers, services, schemas, models) with SQLite database for single-user deployment.

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy, Uvicorn, Pytest.

---

### Task 1: Initialize Project Structure & Dependencies

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/main.py`
- Create: `backend/tests/test_main.py`
- Create: `backend/tests/__init__.py`

- [ ] **Step 1: Write requirements.txt**

```text
fastapi==0.110.0
uvicorn==0.28.0
sqlalchemy==2.0.28
pydantic==2.6.3
pydantic-settings==2.2.1
pytest==8.1.1
httpx==0.27.0
```

- [ ] **Step 2: Write basic FastAPI app and CORS config**

```python
# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="MeowHealth Web API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok"}
```

- [ ] **Step 3: Write test for health check**

```python
# backend/tests/test_main.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pip install -r requirements.txt && pytest tests/test_main.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/requirements.txt backend/main.py backend/tests/
git commit -m "chore: init backend structure, dependencies, and health check"
```

---

### Task 2: Configure Database Connection (SQLAlchemy)

**Files:**
- Create: `backend/database.py`

- [ ] **Step 1: Write database configuration**

```python
# backend/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./meowhealth.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 2: Commit**

```bash
git add backend/database.py
git commit -m "chore: setup sqlalchemy sqlite engine and db session dependency"
```

---

### Task 3: Define Database Models

**Files:**
- Create: `backend/models.py`
- Modify: `backend/main.py:1-2`

- [ ] **Step 1: Write CatProfile and HealthRecord models**

```python
# backend/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
import datetime
import enum
from database import Base

class RecordType(str, enum.Enum):
    WEIGHT = "weight"
    VACCINE = "vaccine"
    SYMPTOM = "symptom"
    REPORT = "report"

class CatProfile(Base):
    __tablename__ = "cat_profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    breed = Column(String)
    birth_date = Column(DateTime)
    gender = Column(String)
    avatar_url = Column(String)

    records = relationship("HealthRecord", back_populates="cat", cascade="all, delete-orphan")

class HealthRecord(Base):
    __tablename__ = "health_records"

    id = Column(Integer, primary_key=True, index=True)
    cat_id = Column(Integer, ForeignKey("cat_profiles.id"), nullable=False)
    record_type = Column(Enum(RecordType), nullable=False)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Payload for different types (JSON ideally, but text for sqlite compat initially, or columns)
    title = Column(String)
    description = Column(String)
    value_float = Column(Float) # For weight
    value_str = Column(String)  # For symptom details
    
    cat = relationship("CatProfile", back_populates="records")
```

- [ ] **Step 2: Create tables on startup**

Modify `backend/main.py`: Add to imports and before app creation.
```python
from database import engine, Base
import models

Base.metadata.create_all(bind=engine)
```

- [ ] **Step 3: Verify creation (smoke test)**

Run: `cd backend && python -c "import main"`
Expected: Creates `meowhealth.db` in `backend/` directory without errors.

- [ ] **Step 4: Commit**

```bash
git add backend/models.py backend/main.py
git commit -m "feat: add CatProfile and HealthRecord models, auto-create tables"
```
