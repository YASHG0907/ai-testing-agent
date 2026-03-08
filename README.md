# 🤖 AI Testing Agent

An AI-powered full-stack testing system that automatically generates professional test cases from plain English API descriptions using Groq LLM, with real browser automation via Playwright.

🌐 **Live Demo** → https://ai-testing-agent-yashg0907s-projects.vercel.app  
🔧 **Live API** → https://ai-testing-agent-production.up.railway.app  
📖 **API Docs** → https://ai-testing-agent-production.up.railway.app/docs  

---

## 🚀 What It Does

You type this:
```
POST /api/login — accepts email and password in JSON body.
Returns JWT token (200), 401 for wrong credentials, 422 for missing fields.
```

AI instantly generates this:
```
TC-001  Valid Login           HAPPY PATH   → expects 200 + token
TC-002  Empty Email           EDGE CASE    → expects 401
TC-003  Missing Password      VALIDATION   → expects 422
TC-004  Invalid Credentials   AUTH         → expects 401
TC-005  Invalid JSON Body     ERROR        → expects 400
```

What takes a QA engineer 2 hours → done in 5 seconds.

---

## ✨ Features

- **AI Test Generation** — Groq LLM generates structured test cases from plain English
- **5 Test Categories** — Happy path, edge cases, validation, auth, error handling
- **Browser Automation** — Playwright scans real websites automatically
- **Mission Control Dashboard** — Live React UI with 4 tabs
- **Persistent History** — All test runs saved to PostgreSQL forever
- **REST API** — 8 fully documented endpoints
- **Quick Templates** — One-click templates for common API types

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite |
| Backend | FastAPI (Python) |
| AI | Groq API (Llama 3.3 70B) |
| Automation | Playwright |
| Database | PostgreSQL (Neon) |
| Deployment | Railway (backend) + Vercel (frontend) |
| Version Control | Git + GitHub |

---

## 📁 Project Structure

```
ai-testing-agent/
│
├── backend/
│   ├── main.py                    # FastAPI server (8 endpoints)
│   ├── requirements.txt           # Python dependencies
│   ├── Procfile                   # Railway deployment config
│   ├── runtime.txt                # Python version
│   ├── nixpacks.toml              # Railway build config
│   └── agents/
│       ├── test_agent.py          # Playwright browser automation
│       └── test_case_generator.py # Groq AI test generation
│
├── frontend/
│   └── src/
│       └── App.jsx                # React dashboard
│
├── .gitignore
└── README.md
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Health check |
| GET | `/stats` | Dashboard statistics |
| POST | `/upload-test` | Register a Playwright test case |
| POST | `/run-test` | Run a registered test case |
| GET | `/results/{id}` | Get single test result |
| GET | `/history` | Get all test history |
| GET | `/test-cases` | List all test cases |
| POST | `/generate-tests` | AI generate test cases |
| POST | `/generate-suite` | AI generate for multiple endpoints |
| POST | `/generate-and-run` | AI generate + Playwright run |

---

## ⚙️ Local Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Git

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

pip install -r requirements.txt
playwright install chromium
```

Create `backend/.env`:
```env
GROQ_API_KEY=gsk_your-key-here
DATABASE_URL=postgresql://user:password@host/dbname
FRONTEND_URL=http://localhost:5173
```

Run backend:
```bash
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open:
```
Frontend  → http://localhost:5173
API Docs  → http://localhost:8000/docs
```

---

## 🎯 How to Use

1. Open the live site
2. Go to **GENERATE tab**
3. Describe your API endpoint in plain English:
```
POST /api/login — accepts email and password.
Returns JWT token (200), 401 for wrong credentials.
```
4. Select HTTP method and number of test cases
5. Click **⬡ GENERATE TEST CASES**
6. View results in **RESULTS tab**
7. Check **HISTORY tab** for all previous runs

---

## 📝 What to Write in the Generate Tab

Include these details for best results:
```
✅ HTTP method and endpoint path
✅ Required and optional input fields with types
✅ Success response (status code + what it returns)
✅ All error responses and when they occur
✅ Authentication requirements
✅ Any constraints (min/max values, allowed formats)
```

Example:
```
POST /api/register — accepts name (string, required),
email (string, required, unique), password (string, min 8 chars).
Returns 201 with user object on success.
Returns 400 if email already exists.
Returns 422 if fields are missing or invalid.
```

---

## 🌍 Real World Applications

- **Software Companies** — automate QA test case generation
- **Startups** — get QA coverage without dedicated QA engineer
- **Freelancers** — deliver professional quality APIs to clients
- **Students** — learn what good API testing looks like
- **DevOps Teams** — integrate into CI/CD pipelines

---

## 🔮 Future Scope

- Auto-execute test cases against real APIs
- GitHub Actions integration for CI/CD
- Slack/email alerts on test failures
- Export to Postman/Jest/Pytest format
- GraphQL and WebSocket support
- Team collaboration features
- Performance benchmarking

---

## 👨‍💻 Author

**Yash G**  
GitHub → https://github.com/YASHG0907

---

## 📄 License

MIT License — free to use and modify.