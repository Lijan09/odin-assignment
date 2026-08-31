# Odin Task Review

An AI-assisted task review application for the technical assessment at Odin Mortgage & Tax. An operations user views incoming tasks, filters and updates their status, and runs an AI analysis to understand what action to take.

## Technologies

| Layer | Choice |
|---|---|
| Backend | Python 3.11 + FastAPI, Pydantic for request/response and LLM-output validation |
| Storage | SQLite via the stdlib `sqlite3` module, raw parameterised SQL behind a repository |
| AI | Google Gemini (`google-genai`) behind an `AiAnalyser` Protocol, with a mock implementation alongside |
| Frontend | React 19 + Vite + TypeScript |
| Tests | pytest with the FastAPI `TestClient` |
| Linting | ruff (backend), oxlint (frontend) |

## Prerequisites

- Python 3.11 or newer
- Node.js 20 or newer
- git

## Running the application

The backend and frontend run as two processes, in two terminals.

### 1. Backend

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment:

```bash
.venv\Scripts\activate
```

(on macOS or Linux: `source .venv/bin/activate`)

```bash
pip install -r requirements.txt
```

Create your local environment file from the committed template:

```bash
copy .env.example .env
```

(on macOS or Linux: `cp .env.example .env`)

The defaults use `AI_PROVIDER=mock`, which needs no API key and makes no network calls, so
the application runs out of the box. To use the real LLM, set `AI_PROVIDER=gemini` and add a
free Gemini API key from [Google AI Studio](https://aistudio.google.com) to `.env`.

Start the server:

```bash
fastapi dev app/main.py
```

The API is on <http://localhost:8000>, with interactive docs at <http://localhost:8000/docs>.

### 2. Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

The application is on <http://localhost:5173>. The Vite dev server proxies `/api/*` to the
backend, so the browser only ever talks to one origin and CORS does not come into play.

## Tests and linting

```bash
cd backend
.venv\Scripts\activate
pytest
```

The backend is linted with [ruff](https://docs.astral.sh/ruff/), including the
`flake8-bandit` security rules, so risks such as string-built SQL are flagged
automatically:

```bash
ruff check .
```

The frontend uses oxlint, via `npm run lint` in the `frontend/` directory.

## Approach

_To be written once the implementation lands._

## What I would improve with more time

_To be written once the implementation lands._

## AI-assisted development

_Which AI coding tools I used, and how I verified the code they produced, to be written._
