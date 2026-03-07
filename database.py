"""
database.py
───────────
PostgreSQL database setup using SQLAlchemy.
Replaces in-memory dicts — data now persists across restarts.

Setup:
    pip install sqlalchemy psycopg2-binary

    Windows PowerShell:
        $env:DATABASE_URL="postgresql://postgres:password@localhost:5432/ai_testing"

    Create DB in psql:
        CREATE DATABASE ai_testing;
"""

import os
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, String, Integer,
    Text, DateTime, Boolean, JSON
)
from sqlalchemy.orm import declarative_base, sessionmaker

# ─────────────────────────────────────────────
#  Connection
# ─────────────────────────────────────────────
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/ai_testing"
)

engine       = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base         = declarative_base()


# ─────────────────────────────────────────────
#  Tables
# ─────────────────────────────────────────────
class TestCaseModel(Base):
    __tablename__ = "test_cases"
    test_id      = Column(String,  primary_key=True, index=True)
    name         = Column(String,  nullable=False)
    url          = Column(String,  default="")
    description  = Column(Text,    default="")
    checks       = Column(JSON,    default=list)
    ai_generated = Column(Boolean, default=False)
    raw_case     = Column(JSON,    default=dict)
    created_at   = Column(DateTime, default=datetime.utcnow)


class TestResultModel(Base):
    __tablename__ = "test_results"
    result_id  = Column(String,   primary_key=True, index=True)
    test_id    = Column(String,   index=True)
    test_name  = Column(String)
    ran_at     = Column(DateTime, default=datetime.utcnow)
    result     = Column(JSON)
    status     = Column(String)


class TestHistoryModel(Base):
    __tablename__ = "test_history"
    id         = Column(Integer,  primary_key=True, autoincrement=True)
    result_id  = Column(String,   index=True)
    test_id    = Column(String)
    test_name  = Column(String)
    status     = Column(String)
    ran_at     = Column(DateTime, default=datetime.utcnow)


# ─────────────────────────────────────────────
#  Init + FastAPI dependency
# ─────────────────────────────────────────────
def init_db():
    Base.metadata.create_all(bind=engine)
    print("  PostgreSQL tables ready ✓")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()