
import os
import json
from groq import Groq

# ─────────────────────────────────────────────
#  Configure Groq client
# ─────────────────────────────────────────────
API_KEY = os.getenv("GROQ_API_KEY")

if not API_KEY:
    raise EnvironmentError(
        "\n\n  GROQ_API_KEY not set!\n"
        "  1. Get free key at: https://console.groq.com\n"
        "  2. Windows PowerShell: $env:GROQ_API_KEY='gsk_your-key-here'\n"
        "  3. Run again\n"
    )

client = Groq(api_key=API_KEY)


# ─────────────────────────────────────────────
#  Core generator function
# ─────────────────────────────────────────────
def generate_test_cases(
    endpoint_description: str,
    method: str = "GET",
    num_cases: int = 5,
    model: str = "llama-3.3-70b-versatile"   # free, fast, very capable
) -> dict:
    """
    Generate structured test cases for an API endpoint using Groq.

    Args:
        endpoint_description : Plain-English description of the endpoint
        method               : HTTP method (GET, POST, PUT, DELETE, PATCH)
        num_cases            : How many test cases to generate (default 5)
        model                : Groq model name

    Returns:
        dict with keys:
            - endpoint        : description echoed back
            - method          : HTTP method
            - total_cases     : number of cases generated
            - test_cases      : list of structured test case dicts
            - raw_ai_response : raw text from Groq (for debugging)
    """

    system_prompt = """
You are a senior QA engineer specializing in API testing.
When given an API endpoint description, generate detailed test cases.

Return ONLY a valid JSON array — no explanation, no markdown, no code fences.
Each object must have exactly these fields:
[
  {
    "id":          "TC-001",
    "name":        "Short descriptive name",
    "category":    "happy_path or edge_case or validation or auth or error_handling",
    "description": "What this test verifies",
    "input": {
      "headers": {},
      "params":  {},
      "body":    {}
    },
    "expected": {
      "status_code":       200,
      "response_contains": [],
      "response_schema":   {}
    },
    "priority": "high or medium or low"
  }
]
""".strip()

    user_prompt = f"""
Generate {num_cases} test cases for this API endpoint:

HTTP Method  : {method.upper()}
Description  : {endpoint_description}

Cover these categories:
1. Happy path        - valid inputs -> expected success response
2. Edge cases        - empty values, boundary values, special characters
3. Validation errors - missing required fields, wrong data types
4. Auth errors       - missing token, expired token, wrong role
5. Error handling    - invalid JSON, extreme input lengths

Return ONLY the JSON array, nothing else.
""".strip()

    raw_text = ""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt}
            ],
            temperature=0.4,
            max_tokens=2000
        )

        raw_text = response.choices[0].message.content.strip()

        # Strip markdown code fences if model wraps in ```json ... ```
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
            raw_text = raw_text.strip()

        cases = json.loads(raw_text)

        # Normalise: unwrap if returned as {"test_cases": [...]}
        if isinstance(cases, dict):
            cases = next(iter(cases.values()))

        return {
            "endpoint":        endpoint_description,
            "method":          method.upper(),
            "total_cases":     len(cases),
            "test_cases":      cases,
            "raw_ai_response": raw_text
        }

    except json.JSONDecodeError as e:
        return {
            "error":           "Response was not valid JSON",
            "detail":          str(e),
            "raw_ai_response": raw_text
        }
    except Exception as e:
        return {
            "error":  "Groq API call failed",
            "detail": str(e)
        }


# ─────────────────────────────────────────────
#  Batch generator  (multiple endpoints at once)
# ─────────────────────────────────────────────
def generate_test_suite(endpoints: list, num_cases_each: int = 3) -> dict:
    """
    Generate test cases for multiple endpoints in one call.

    Args:
        endpoints      : list of dicts with 'description' and 'method'
        num_cases_each : test cases per endpoint
    """
    suite = {}
    for ep in endpoints:
        description = ep.get("description", "")
        method      = ep.get("method", "GET")
        print(f"  Generating: [{method}] {description[:55]}...")
        suite[description] = generate_test_cases(
            endpoint_description=description,
            method=method,
            num_cases=num_cases_each
        )
    return {"suite": suite, "total_endpoints": len(endpoints)}


# ─────────────────────────────────────────────
#  Pretty printer
# ─────────────────────────────────────────────
def print_test_cases(result: dict) -> None:
    if "error" in result:
        print(f"\n  ERROR   : {result['error']}")
        print(f"  Detail  : {result.get('detail', '')}")
        print(f"  Raw     : {result.get('raw_ai_response', '')[:300]}")
        return

    print(f"\n{'='*62}")
    print(f"  Endpoint : {result['endpoint'][:55]}")
    print(f"  Method   : {result['method']}")
    print(f"  Cases    : {result['total_cases']}")
    print(f"{'='*62}")

    priority_label = {"high": "[HIGH]", "medium": "[MED] ", "low": "[LOW] "}

    for tc in result.get("test_cases", []):
        label = priority_label.get(tc.get("priority", "").lower(), "[?]  ")
        print(f"\n  {label} {tc.get('id','?')} - {tc.get('name','?')}")
        print(f"         Category    : {tc.get('category','?')}")
        print(f"         Description : {tc.get('description','?')}")
        inp = tc.get("input", {})
        if any(v for v in inp.values() if v):
            print(f"         Input       : {json.dumps(inp)}")
        exp = tc.get("expected", {})
        print(f"         Expected    : status={exp.get('status_code','?')}  "
              f"contains={exp.get('response_contains', [])}")
    print(f"\n{'='*62}")


# ─────────────────────────────────────────────
#  Demo  ->  python agents/test_case_generator.py
# ─────────────────────────────────────────────
if __name__ == "__main__":

    print("\n>>> Single endpoint demo\n")

    result = generate_test_cases(
        endpoint_description=(
            "POST /api/v1/login - accepts JSON body with "
            "'email' (string) and 'password' (string). "
            "Returns a JWT access token on success (200). "
            "Returns 401 for wrong credentials, 422 for missing fields."
        ),
        method="POST",
        num_cases=5
    )
    print_test_cases(result)

    with open("generated_test_cases.json", "w") as f:
        json.dump(result, f, indent=2)
    print("\n  Saved -> generated_test_cases.json")

    print("\n>>> Full suite demo (3 endpoints)\n")

    suite = generate_test_suite(
        endpoints=[
            {"method": "GET",    "description": "GET /users/{id} - returns user profile by ID"},
            {"method": "POST",   "description": "POST /users - create new user with name, email, role"},
            {"method": "DELETE", "description": "DELETE /users/{id} - admin-only, deletes a user"},
        ],
        num_cases_each=3
    )

    with open("generated_test_suite.json", "w") as f:
        json.dump(suite, f, indent=2)
    print(f"\n  Suite saved -> generated_test_suite.json")
    print(f"  Total endpoints: {suite['total_endpoints']}")