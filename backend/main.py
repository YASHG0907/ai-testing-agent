"""
main.py
───────
AI Testing Agent — Full Stack with PostgreSQL (Supabase)
FastAPI + Groq + Playwright + SQLAlchemy

Setup:
    pip install fastapi uvicorn playwright groq sqlalchemy psycopg2-binary python-dotenv alembic
    playwright install chromium

    Create .env file:
        GROQ_API_KEY=gsk_your-key-here
        DATABASE_URL=postgresql://postgres:password@db.xxx.supabase.co:5432/postgres

    Run:
        uvicorn main:app --reload
"""

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Integer, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import uuid, os, json

from agents.test_agent import run_website_test
from agents.test_case_generator import generate_test_cases, generate_test_suite

# ─────────────────────────────────────────────
#  Database Setup
# ─────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "")

engine       = create_engine(DATABASE_URL) if DATABASE_URL else None
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) if engine else None
Base         = declarative_base()


# ─────────────────────────────────────────────
#  Database Models
# ─────────────────────────────────────────────
class DBTestCase(Base):
    __tablename__ = "test_cases"

    id          = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name        = Column(String, nullable=False)
    url         = Column(String, default="")
    description = Column(Text, default="")
    checks      = Column(Text, default="[]")    # JSON string
    ai_generated = Column(Integer, default=0)   # 0=False, 1=True
    raw_case    = Column(Text, default="{}")    # JSON string
    created_at  = Column(DateTime, default=datetime.utcnow)


class DBTestResult(Base):
    __tablename__ = "test_results"

    id          = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    test_id     = Column(String, nullable=False)
    test_name   = Column(String, nullable=False)
    status      = Column(String, default="unknown")
    result_json = Column(Text, default="{}")    # JSON string
    ran_at      = Column(DateTime, default=datetime.utcnow)


# Create tables automatically on startup


# ─────────────────────────────────────────────
#  DB Dependency
# ─────────────────────────────────────────────
def get_db():
    if not SessionLocal:
        raise HTTPException(status_code=500, detail="Database not configured")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─────────────────────────────────────────────
#  App Setup
# ─────────────────────────────────────────────
app = FastAPI(
    title="AI Testing Agent API",
    description="Automated website testing + AI test case generation powered by Groq + PostgreSQL",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:5173")],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    if engine:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables ready")
    else:
        print("⚠️ No DATABASE_URL found")

# ─────────────────────────────────────────────
#  Pydantic Models
# ─────────────────────────────────────────────
class Check(BaseModel):
    type: str
    value: str

class TestCase(BaseModel):
    name: str
    url: HttpUrl
    description: Optional[str] = ""
    checks: Optional[List[Check]] = []

class RunRequest(BaseModel):
    test_id: str

class GenerateRequest(BaseModel):
    endpoint_description: str
    method: Optional[str] = "GET"
    num_cases: Optional[int] = 5

class EndpointItem(BaseModel):
    description: str
    method: Optional[str] = "GET"

class SuiteRequest(BaseModel):
    endpoints: List[EndpointItem]
    num_cases_each: Optional[int] = 3

class GenerateAndRunRequest(BaseModel):
    endpoint_description: str
    method: Optional[str] = "GET"
    num_cases: Optional[int] = 5
    url: HttpUrl


# ─────────────────────────────────────────────
#  Health
# ─────────────────────────────────────────────
@app.get("/", tags=["Health"])
def home():
    return {
        "message": "AI Testing Agent v3.0 Running",
        "database": "PostgreSQL (Supabase) ✅",
        "endpoints": {
            "playwright_testing": ["POST /upload-test", "POST /run-test", "GET /results/{id}", "GET /history", "GET /test-cases"],
            "ai_generation":      ["POST /generate-tests", "POST /generate-suite", "POST /generate-and-run"]
        }
    }


# ─────────────────────────────────────────────
#  Playwright Testing Routes
# ─────────────────────────────────────────────
@app.post("/upload-test", tags=["Playwright Testing"], status_code=201)
def upload_test(test_case: TestCase, db: Session = Depends(get_db)):
    """Register a new Playwright test case. Returns test_id."""
    db_case = DBTestCase(
        id          = str(uuid.uuid4()),
        name        = test_case.name,
        url         = str(test_case.url),
        description = test_case.description,
        checks      = json.dumps([c.dict() for c in test_case.checks]),
        ai_generated = 0
    )
    db.add(db_case)
    db.commit()
    db.refresh(db_case)
    return {
        "message": "Test case uploaded",
        "test_id": db_case.id,
        "test":    _format_test_case(db_case)
    }


@app.post("/run-test", tags=["Playwright Testing"])
def run_test(body: RunRequest, db: Session = Depends(get_db)):
    """Run a registered Playwright test case by test_id."""
    db_case = db.query(DBTestCase).filter(DBTestCase.id == body.test_id).first()
    if not db_case:
        raise HTTPException(status_code=404, detail=f"Test '{body.test_id}' not found")

    test_case_dict = _format_test_case(db_case)
    raw = run_website_test(db_case.url, test_case_dict)

    db_result = DBTestResult(
        id          = str(uuid.uuid4()),
        test_id     = body.test_id,
        test_name   = db_case.name,
        status      = raw.get("status", "unknown"),
        result_json = json.dumps(raw)
    )
    db.add(db_result)
    db.commit()
    db.refresh(db_result)

    return {
        "message":   "Test executed",
        "result_id": db_result.id,
        "summary":   _format_result(db_result),
        "details":   raw
    }


@app.get("/results/{result_id}", tags=["Playwright Testing"])
def get_result(result_id: str, db: Session = Depends(get_db)):
    """Return full result for a single test run."""
    db_result = db.query(DBTestResult).filter(DBTestResult.id == result_id).first()
    if not db_result:
        raise HTTPException(status_code=404, detail=f"Result '{result_id}' not found")
    return {**_format_result(db_result), "result": json.loads(db_result.result_json)}


@app.get("/history", tags=["Playwright Testing"])
def get_history(limit: int = 30, status: Optional[str] = None, db: Session = Depends(get_db)):
    """Return last N runs from database. Filter by ?status=success or ?status=error."""
    query = db.query(DBTestResult).order_by(DBTestResult.ran_at.desc())
    if status:
        query = query.filter(DBTestResult.status == status)
    results = query.limit(limit).all()
    total   = db.query(DBTestResult).count()
    return {
        "total":   total,
        "showing": len(results),
        "history": [_format_result(r) for r in results]
    }


@app.get("/test-cases", tags=["Playwright Testing"])
def list_test_cases(db: Session = Depends(get_db)):
    """Return all registered test cases from database."""
    cases = db.query(DBTestCase).order_by(DBTestCase.created_at.desc()).all()
    return {"total": len(cases), "test_cases": [_format_test_case(c) for c in cases]}


# ─────────────────────────────────────────────
#  AI Generation Routes
# ─────────────────────────────────────────────
@app.post("/generate-tests", tags=["AI Generation"])
def generate_tests_endpoint(body: GenerateRequest, db: Session = Depends(get_db)):
    """Generate AI test cases and save them to PostgreSQL."""
    result = generate_test_cases(
        endpoint_description=body.endpoint_description,
        method=body.method,
        num_cases=body.num_cases
    )
    if "error" in result:
        raise HTTPException(status_code=500, detail=result)

    saved_ids = []
    for tc in result.get("test_cases", []):
        db_case = DBTestCase(
            id           = str(uuid.uuid4()),
            name         = tc.get("name", "AI Generated Test"),
            url          = "",
            description  = tc.get("description", ""),
            checks       = "[]",
            ai_generated = 1,
            raw_case     = json.dumps(tc)
        )
        db.add(db_case)
        saved_ids.append(db_case.id)

    db.commit()
    return {
        "message":         "Test cases generated and saved to database",
        "total_generated": result["total_cases"],
        "saved_test_ids":  saved_ids,
        "test_cases":      result["test_cases"]
    }


@app.post("/generate-suite", tags=["AI Generation"])
def generate_suite_endpoint(body: SuiteRequest):
    """Generate test cases for multiple endpoints."""
    suite = generate_test_suite(
        endpoints=[e.dict() for e in body.endpoints],
        num_cases_each=body.num_cases_each
    )
    if "error" in suite:
        raise HTTPException(status_code=500, detail=suite)
    return {"message": "Test suite generated", "total_endpoints": suite["total_endpoints"], "suite": suite["suite"]}


@app.post("/generate-and-run", tags=["AI Generation"])
def generate_and_run(body: GenerateAndRunRequest, db: Session = Depends(get_db)):
    """Generate AI test cases + run Playwright + save everything to database."""

    # Step 1 — Generate with Groq AI
    generated = generate_test_cases(
        endpoint_description=body.endpoint_description,
        method=body.method,
        num_cases=body.num_cases
    )
    if "error" in generated:
        raise HTTPException(status_code=500, detail=generated)

    # Step 2 — Run Playwright
    playwright_result = run_website_test(str(body.url))

    # Step 3 — Save result to database
    db_result = DBTestResult(
        id          = str(uuid.uuid4()),
        test_id     = "ai-generated",
        test_name   = body.endpoint_description[:80],
        status      = playwright_result.get("status", "unknown"),
        result_json = json.dumps({
            "ai_generated_cases": generated["test_cases"],
            "playwright_result":  playwright_result,
            "url":                str(body.url)
        })
    )
    db.add(db_result)
    db.commit()

    return {
        "message": "Generated and executed — saved to database ✅",
        "report": {
            "result_id":          db_result.id,
            "url":                str(body.url),
            "ran_at":             db_result.ran_at.isoformat(),
            "ai_generated_cases": generated["test_cases"],
            "total_cases":        generated["total_cases"],
            "playwright_result":  playwright_result,
            "overall_status":     playwright_result.get("status", "unknown")
        }
    }


# ─────────────────────────────────────────────
#  Stats endpoint (for dashboard header)
# ─────────────────────────────────────────────
@app.get("/stats", tags=["Health"])
def get_stats(db: Session = Depends(get_db)):
    """Return overall stats for dashboard."""
    total  = db.query(DBTestResult).count()
    passed = db.query(DBTestResult).filter(DBTestResult.status == "success").count()
    return {
        "total_runs":    total,
        "passed":        passed,
        "failed":        total - passed,
        "total_cases":   db.query(DBTestCase).count()
    }


# ─────────────────────────────────────────────
#  Helper formatters
# ─────────────────────────────────────────────
def _format_test_case(c: DBTestCase) -> dict:
    return {
        "test_id":     c.id,
        "name":        c.name,
        "url":         c.url,
        "description": c.description,
        "checks":      json.loads(c.checks or "[]"),
        "ai_generated": bool(c.ai_generated),
        "created_at":  c.created_at.isoformat() if c.created_at else ""
    }

def _format_result(r: DBTestResult) -> dict:
    return {
        "result_id": r.id,
        "test_id":   r.test_id,
        "test_name": r.test_name,
        "status":    r.status,
        "ran_at":    r.ran_at.isoformat() if r.ran_at else ""
    }