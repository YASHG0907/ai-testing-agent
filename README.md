"# AI Testing Agent" 
# AI Testing Agent 🤖

AI-powered automated testing system using Groq, Playwright, FastAPI, and React.

## Features
- AI generates test cases from plain English descriptions
- Playwright scans real websites automatically
- Mission Control dashboard with live results
- Full test history tracking

## Tech Stack
- **Backend**: FastAPI + Python
- **AI**: Groq (Llama 3.3 70B)
- **Automation**: Playwright
- **Frontend**: React + Vite

## Setup

### Backend
pip install fastapi uvicorn playwright groq
playwright install chromium
$env:GROQ_API_KEY="your-key-here"
uvicorn main:app --reload

### Frontend
cd frontend
npm install
npm run dev

## Usage
- Backend: http://localhost:8000
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs