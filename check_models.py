"""
check_models.py
───────────────
Run this to see which Gemini models are available for your API key.

Usage (PowerShell):
    $env:GOOGLE_API_KEY="AIzaSy-your-key-here"
    python check_models.py
"""

import os
from google import genai

API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    print("\n  ERROR: GOOGLE_API_KEY not set!")
    print("  Run: $env:GOOGLE_API_KEY='AIzaSy-your-key-here'\n")
    exit(1)

client = genai.Client(api_key=API_KEY)

print("\n  Fetching available models...\n")
print(f"  {'MODEL NAME':<45} {'SUPPORTED METHODS'}")
print(f"  {'-'*45} {'-'*30}")

try:
    for model in client.models.list():
        methods = ", ".join(model.supported_actions) if hasattr(model, "supported_actions") else "generateContent"
        print(f"  {model.name:<45} {methods}")
except Exception as e:
    print(f"\n  ERROR: {e}\n")

print("\n  Copy any model name above and use it in test_case_generator.py\n")