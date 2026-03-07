from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware   # ← ADD THIS LINE
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime
import uuid, sys, os

sys.path.append(os.path.abspath(".."))
from agents.test_agent import run_website_test
from agents.test_case_generator import generate_test_cases, generate_test_suite

app = FastAPI(
    title="AI Testing Agent API",
    description="Automated website testing + AI test case generation powered by Groq",
    version="2.0.0"
)

# ← ADD THESE 6 LINES RIGHT HERE
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
# ─────────────────────────────────────────────
#  In-memory stores  (replace with DB in Step 11)
# ─────────────────────────────────────────────
test_cases: dict   = {}
test_results: dict = {}
test_history: list = []


# ─────────────────────────────────────────────
#  Pydantic models — Playwright testing
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


# ─────────────────────────────────────────────
#  Pydantic models — AI generation (Groq)
# ─────────────────────────────────────────────
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
        "message": "AI Testing Agent v2.0 Running",
        "endpoints": {
            "playwright_testing": [
                "POST /upload-test",
                "POST /run-test",
                "GET  /results/{id}",
                "GET  /history",
                "GET  /test-cases"
            ],
            "ai_generation": [
                "POST /generate-tests",
                "POST /generate-suite",
                "POST /generate-and-run"
            ]
        }
    }


# ─────────────────────────────────────────────
#  Playwright Testing Routes
# ─────────────────────────────────────────────
@app.post("/upload-test", tags=["Playwright Testing"], status_code=201)
def upload_test(test_case: TestCase):
    """Register a new Playwright test case. Returns test_id."""
    test_id = str(uuid.uuid4())
    test_cases[test_id] = {
        "test_id":     test_id,
        "name":        test_case.name,
        "url":         str(test_case.url),
        "description": test_case.description,
        "checks":      [c.dict() for c in test_case.checks],
        "created_at":  datetime.utcnow().isoformat()
    }
    return {"message": "Test case uploaded", "test_id": test_id, "test": test_cases[test_id]}


@app.post("/run-test", tags=["Playwright Testing"])
def run_test(body: RunRequest):
    """Run a registered Playwright test case by test_id."""
    if body.test_id not in test_cases:
        raise HTTPException(status_code=404, detail=f"Test '{body.test_id}' not found")

    test_case = test_cases[body.test_id]
    raw       = run_website_test(test_case["url"], test_case)
    result_id = str(uuid.uuid4())

    entry = {
        "result_id": result_id,
        "test_id":   body.test_id,
        "test_name": test_case["name"],
        "ran_at":    datetime.utcnow().isoformat(),
        "result":    raw
    }
    test_results[result_id] = entry
    test_history.append({
        "result_id": result_id,
        "test_id":   body.test_id,
        "test_name": test_case["name"],
        "status":    raw.get("status"),
        "ran_at":    entry["ran_at"]
    })
    return {"message": "Test executed", "result_id": result_id, "summary": test_history[-1], "details": raw}


@app.get("/results/{result_id}", tags=["Playwright Testing"])
def get_result(result_id: str):
    """Return full result for a single test run."""
    if result_id not in test_results:
        raise HTTPException(status_code=404, detail=f"Result '{result_id}' not found")
    return test_results[result_id]


@app.get("/history", tags=["Playwright Testing"])
def get_history(limit: int = 20, status: Optional[str] = None):
    """Return last N runs. Filter by ?status=success or ?status=error."""
    history = test_history[::-1]
    if status:
        history = [h for h in history if h.get("status") == status]
    return {"total": len(test_history), "showing": min(limit, len(history)), "history": history[:limit]}


@app.get("/test-cases", tags=["Playwright Testing"])
def list_test_cases():
    """Return all registered test cases."""
    return {"total": len(test_cases), "test_cases": list(test_cases.values())}


# ─────────────────────────────────────────────
#  AI Generation Routes (Groq)
# ─────────────────────────────────────────────
@app.post("/generate-tests", tags=["AI Generation"])
def generate_tests_endpoint(body: GenerateRequest):
    """
    Use Groq AI to generate structured test cases from plain-English description.

    Example:
    {
        "endpoint_description": "POST /login accepts email and password, returns JWT",
        "method": "POST",
        "num_cases": 5
    }
    """
    result = generate_test_cases(
        endpoint_description=body.endpoint_description,
        method=body.method,
        num_cases=body.num_cases
    )

    if "error" in result:
        raise HTTPException(status_code=500, detail=result)

    # Auto-save generated cases into test_cases store
    saved_ids = []
    for tc in result.get("test_cases", []):
        test_id = str(uuid.uuid4())
        test_cases[test_id] = {
            "test_id":      test_id,
            "name":         tc.get("name", "AI Generated Test"),
            "url":          "",
            "description":  tc.get("description", ""),
            "checks":       [],
            "ai_generated": True,
            "raw_case":     tc,
            "created_at":   datetime.utcnow().isoformat()
        }
        saved_ids.append(test_id)

    return {
        "message":         "Test cases generated and saved",
        "total_generated": result["total_cases"],
        "saved_test_ids":  saved_ids,
        "test_cases":      result["test_cases"]
    }


@app.post("/generate-suite", tags=["AI Generation"])
def generate_suite_endpoint(body: SuiteRequest):
    """
    Generate test cases for multiple endpoints at once.

    Example:
    {
        "endpoints": [
            {"method": "POST",   "description": "POST /login with email + password"},
            {"method": "GET",    "description": "GET /users/{id} returns user profile"},
            {"method": "DELETE", "description": "DELETE /users/{id} admin-only"}
        ],
        "num_cases_each": 3
    }
    """
    suite = generate_test_suite(
        endpoints=[e.dict() for e in body.endpoints],
        num_cases_each=body.num_cases_each
    )

    if "error" in suite:
        raise HTTPException(status_code=500, detail=suite)

    return {"message": "Test suite generated", "total_endpoints": suite["total_endpoints"], "suite": suite["suite"]}


@app.post("/generate-and-run", tags=["AI Generation"])
def generate_and_run(body: GenerateAndRunRequest):
    """
    The POWER endpoint — does everything in one call:
      1. Generates AI test cases with Groq
      2. Runs Playwright on the real URL
      3. Returns combined pass/fail report

    Example:
    {
        "endpoint_description": "Login page with email and password fields",
        "method": "POST",
        "num_cases": 3,
        "url": "https://example.com/login"
    }
    """
    # Step 1 — Generate with Groq AI
    generated = generate_test_cases(
        endpoint_description=body.endpoint_description,
        method=body.method,
        num_cases=body.num_cases
    )
    if "error" in generated:
        raise HTTPException(status_code=500, detail=generated)

    # Step 2 — Run Playwright on real URL
    playwright_result = run_website_test(str(body.url))

    # Step 3 — Build combined report
    result_id = str(uuid.uuid4())
    report = {
        "result_id":          result_id,
        "url":                str(body.url),
        "ran_at":             datetime.utcnow().isoformat(),
        "ai_generated_cases": generated["test_cases"],
        "total_cases":        generated["total_cases"],
        "playwright_result":  playwright_result,
        "overall_status":     playwright_result.get("status", "unknown")
    }

    test_results[result_id] = report
    test_history.append({
        "result_id": result_id,
        "test_id":   "ai-generated",
        "test_name": body.endpoint_description[:50],
        "status":    report["overall_status"],
        "ran_at":    report["ran_at"]
    })

    return {"message": "Generated and executed successfully", "report": report}