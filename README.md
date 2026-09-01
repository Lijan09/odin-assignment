# Odin Task Review

An AI-assisted task review application for an operations user: view incoming tasks, filter them by status, change their status and priority, and run an AI analysis to decide what action to take next.

Built for the Odin Junior Software Engineer technical assessment.

---

## Submission format

| | |
|---|---|
| **Name** | Lijan Shrestha |
| **GitHub Repository** | https://github.com/Lijan09/odin-assignment |
| **Backend Language** | Python 3.11 (FastAPI) |
| **Frontend framework** | React 19 + Vite + Typescript |
| **LLM Provider / Mock Used** | Google Gemini (`gemini-3.6-flash`), with a deterministic mock analyser as the default so the app runs with no API key |
| **Approximate Time Spent** | 4 hours |

---

## How to run the application

Two processes in two terminals. **No API key is required**, the app ships configured to use a mock analyser.

**Prerequisites:** Python 3.11+, Node.js 20+, git.

### 1. Backend

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment (Windows):

```bash
.venv\Scripts\activate
```

macOS/Linux: `source .venv/bin/activate`

```bash
pip install -r requirements.txt
```

Create your local environment file from the committed template:

```bash
copy .env.example .env
```

macOS/Linux: `cp .env.example .env`

Start the API:

```bash
fastapi dev app/main.py
```

The database is created and seeded automatically on startup. The API is on <http://127.0.0.1:8000>, with interactive docs at <http://127.0.0.1:8000/docs>.

### 2. Frontend

In a second terminal:

```bash
cd frontend
```

Create your local environment file from the committed template:

```bash
copy .env.example .env
```

macOS/Linux: `cp .env.example .env`

Install the dependencies and start the server:

```bash
npm install
npm run dev
```

Open <http://localhost:5173>.

### Optional: use the real LLM

The default `AI_PROVIDER=mock` needs no key and makes no network calls. To use Gemini, get a free key from [Google AI Studio](https://aistudio.google.com) and set in `backend/.env`:

```
AI_PROVIDER=gemini
GEMINI_API_KEY=your-key-here
GEMINI_MODEL=gemini-3.6-flash
```

Then restart the backend — settings are read once at startup. `.env` is gitignored, and no key is committed anywhere in this repository.

### Reseeding the database

```bash
cd backend
python -m app.db --reset
```

---

## API

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/tasks` | List tasks, newest first. Optional `?status=` filter. |
| `PATCH` | `/tasks/{id}/status` | Update a task's status. |
| `PATCH` | `/tasks/{id}/priority` | Update a task's priority. |
| `POST` | `/tasks/{id}/analyse` | Run an AI analysis, return a structured result. |
| `GET` | `/health` | Server status check. |

Analysis returns exactly the shape given in the brief:

```json
{
  "category": "DOCUMENT_REQUEST",
  "priority": "HIGH",
  "summary": "Customer needs to provide their latest payslip.",
  "recommendedAction": "Request the missing payslip."
}
```

Every error uses one envelope, so the frontend has a single shape to parse:

```json
{
  "error": "validation_error",
  "message": "The request was rejected by validation.",
  "details": [{ "field": "status", "message": "Input should be 'NEW', 'IN_PROGRESS' or 'COMPLETED'" }]
}
```

| Status | When |
|---|---|
| `422` | Unsupported status or priority value, malformed body, non-integer id |
| `404` | Task id does not exist |
| `502` | The AI provider failed, or returned something that did not validate |

---

## Technologies used

| Layer | Choice | Why |
|---|---|---|
| Backend | Python 3.11 + FastAPI 0.141 | Pydantic serves as both the API contract and the validator for LLM output; one mechanism doing two jobs |
| Storage | SQLite via the stdlib `sqlite3`, raw SQL behind a repository | The role lists SQL fundamentals as required; an ORM would hide exactly the thing worth showing. Zero dependencies, and reviewers need no database setup |
| AI | Google Gemini (`google-genai` 2.20) behind an `AiAnalyser` Protocol, with a mock alongside | A real integration, while the interface keeps the failure path testable with no network |
| Frontend | React 19 + Vite + TypeScript | React is named in the job description; the Vite dev proxy removes CORS from the problem entirely |
| Tests | pytest 9 + FastAPI `TestClient` | `app.dependency_overrides` is a clean seam for forcing an AI failure |
| Linting | ruff (incl. `flake8-bandit`), oxlint | Security rules on the backend catch string-built SQL automatically |

---

## Approach

### Scope discipline was a deliberate decision

The brief specifies a small application precisely. I built what it asks for and resisted adding around it; no authentication, no pagination, no task creation, no component library. Each of those would have been surface area to defend rather than evidence of judgement. Where I wanted something extra, I wrote it into "what I would improve" below instead of building it.

The one addition beyond the brief is priority editing. The brief makes status the only mutable field, but the AI returns a suggested priority, and an interface that shows a suggestion with no way to act on it felt incomplete. I added it knowing it was an extension, and kept the suggestion advisory: nothing applies it automatically.

### Vertical slices, so something always runs

Build order: schema and seed data → list and filter → status tests → AI module → analysis endpoint and its failure path → UI → documentation. Tests came before any AI work eliberately, so the plain CRUD path was proven before adding a dependency that can fail. At every point the application ran end to end.

### Treating LLM output as untrusted input

This is the decision I care most about. The JSON schema generated from the Pydantic model is sent to Gemini so it constrains generation — and the reply is still parsed through Pydantic before it can reach a caller. If the model returns well-formed JSON with `"category": "REFUND"`, validation fails, `AiAnalysisError` is raised, and the endpoint returns 502 rather than passing an invalid value to the UI. 

A language model is not a trusted source of well-formed data, even when you have asked it politely with a schema. Four tests cover this case.

### AI failure is a designed path, not a bare `except`

The analyser distinguishes failure kinds rather than catching everything:

- **4xx (`ClientError`)**: a bad key, a retired model, a rejected prompt. Retrying an identical request cannot fix any of these, so it fails immediately.
- **5xx and timeouts (`ServerError`)**: transient. Retried once, then a typed error.
- **Malformed or schema-violating output**: retried once, then a typed error.

Only `AiAnalysisError` maps to 502. An unexpected exception is deliberately left to surface as a server error, because masking a real bug as a tidy 502 hides it, there is a test asserting that too. The caller-facing message never contains provider detail; the specific reason goes to the server log. A test asserts that a provider's internal hostname in an error does not reach the client.

### Why raw SQL

`sqlite3` is in the standard library, so reviewers need no database and no extra dependency. Every statement is a full literal with bound parameters, no f-strings, no fragments joined at runtime, so no input can influence the SQL text. The `tasks` table also carries `CHECK` constraints on status and priority, so an invalid row cannot be written by any route in, including a manual `sqlite3` session. That redundancy is deliberate: the Pydantic enum and the database constraint guard the same rule at different layers.

### Frontend: state coverage over visual polish

The brief says visual design is not assessed but asks for "appropriate loading and error states", so the UI effort went there. The rule I held to is that every asynchronous action is scoped to a single task. Analysing task 3 leaves task 5 fully interactive: no page-wide spinner, no overlay. Each row owns its loading, error and retry state, and a failed status change reverts the select and explains why, next to the control it describes.

The frontend never names a host. `api.ts` uses the relative base `/api`, and the Vite dev server proxies it to the backend, stripping the prefix. The browser therefore only ever talks to one origin, so there is no CORS middleware in the backend at all,  and no `VITE_`-prefixed variable that could compile a secret into the browser bundle.

### Choices made deliberately, not by accident

- **422, not 400, for an unsupported status**: The request is syntactically valid JSON whose *content* is unacceptable, which is what 422 means, and keeping it makes every   validation failure in the API consistent. FastAPI's default body is a nested array that is awkward to consume, so a handler flattens it into a documented shape.
- **camelCase on the wire**: The brief's examples use `createdAt` and `recommendedAction`, so every model derives from a `CamelModel` base using a Pydantic alias generator. Python stays snake_case; the API emits their documented shape.
- **Analysis is not persisted**: The brief frames it as a decision aid, not a field on the record, so `analyse` reads and returns without writing.
- **The API key is a `SecretStr`**: A plain `str` would print in any traceback or debug log. It is unwrapped at exactly one call site.
- **Seed data is mock business**: missing payslip, uncertified passport, settlement brought forward, Brisbane valuation, Singapore tax residency, lender chase. `Task 1, Task 2` would have made the AI output meaningless to read.

---

## Testing

```bash
cd backend
.venv\Scripts\activate
pytest
```

**57 tests.** The brief asks for at least one meaningful test and suggests three behaviours; all three are covered, plus the surrounding cases.

| File | Tests | Covers |
|---|---|---|
| `test_status.py` | 14 | Valid status accepted and persisted; five kinds of invalid value rejected; rejection leaves the task unchanged; 404 |
| `test_priority.py` | 13 | The same rules for priority, plus that editing one field never disturbs the other |
| `test_tasks.py` | 8 | Listing, filtering, ordering, and that no snake_case leaks onto the wire |
| `test_analyse.py` | 8 | The documented result shape; **AI failure returns 502 and the app keeps working**; an unexpected error is not swallowed |
| `test_gemini_analyser.py` | 11 | Retry on 5xx, **no** retry on 4xx, malformed JSON rejected, schema-violating JSON rejected, no provider detail in the error |
| `test_db.py` | 3 | Connection usable across threads (regression), foreign keys on, row access by name |

Each test gets a fresh in-memory database via `app.dependency_overrides`, so tests are isolated from each other and never touch the developer's database file. The analyser is also overridden with the mock for every test, so the suite makes no network calls regardless of what `AI_PROVIDER` is set to locally.

Linting:

```bash
cd backend
ruff check .
```

```bash
cd frontend
npm run lint
```

---

## AI-assisted development

I used Claude Code as an AI tool throughout: scaffolding, first drafts of modules, and test cases. I directed the design decisions, reviewed what it produced, and ran the application against real load and a real API. The brief asks how I checked that AI-generated code was correct. Rather than list principles, I did the following:

### Its recalled facts were wrong, twice

It pinned `google-genai==0.3.0` from memory. The real current version is **2.20.0**: wrong by two major versions. I had it install unpinned first and then pin to what actually resolved, so `requirements.txt` reflects a state that was really run.

It then wrote the Gemini call from a remembered API shape (`client.interactions.create`). I made it introspect the installed package instead. The real structured-output path is `client.models.generate_content` with a `GenerateContentConfig`, and `HttpOptions.timeout` is in milliseconds, not seconds. The recalled shape was plausible enough to be dangerous: `interactions` does exist on the client, it just is not the right entry point.

**Rule I applied from then on:** for anything version-dependent, check the installed artefact or the live docs, never the model's memory.

### I verified the guardrails before trusting them

`.gitignore` is the one mistake that cannot be undone, so I did not eyeball the patterns. I wrote a decoy `backend/.env` containing a fake secret, ran `git add --all --dry-run`, and confirmed it was excluded while `.env.example` stayed tracked.

Similarly, before any SQL was written I had the linter fed a deliberately vulnerable query to confirm `S608` actually fires. It did. Then it then caught a real f-string in
the first draft of `repository.py`. That was technically a false positive (the interpolated value was a module constant), but I had the statements rewritten as full
literals rather than adding a suppression, because a suppression in data-access code is a bad habit to start.

### I mutation-tested the tests

Green tests prove nothing unless they fail when the code breaks. So I broke things deliberately and checked:

| Deliberate defect | Tests that failed |
|---|---|
| `StatusUpdate.status` weakened from the enum to a plain `str` | 11 |
| The `AiAnalysisError` → 502 handler deleted | 2 |
| The typed error replaced with a bare `except` returning a placebo result | 3 |

### The bug: a concurrency defect it argued was not there

An early test failure was `sqlite3.ProgrammingError: SQLite objects created in a thread can only be used in that same thread`. The assistant fixed the test fixture and told me production was safe, because the connection dependency opens its connection inside the request.

That reasoning was wrong, and running the application proved it. FastAPI runs a sync generator dependency and the endpoint consuming it as two separate `run_in_threadpool` calls, and AnyIO does not guarantee the same worker thread for both. Under real use I hit the same error in the server log.

I had it reproduced deterministically rather than patched on a hunch; 60 concurrent requests against a running server:

```
before fix: {500: 22, 200: 38}
after fix:  {200: 60}    and 90 mixed read/write requests: {200: 90}
```

The fix is `check_same_thread=False` on the connection, safe here because each request gets its own and setup, handler and teardown touch it strictly in sequence. The deeper problem was that 41 passing tests could never have caught it, because the test fixture already set that flag. `test_db.py` now asserts the requirement directly, and I confirmed it fails when the fix is reverted.

This is the clearest example of why I reviewed rather than accepted: the code was plausible, reviewed, tested and running, and it was still wrong under concurrency.

### Other issues I found by running the application

- **The tests were not isolated**: Switching `AI_PROVIDER=gemini` in `.env` would have made the suite fire real, billable API calls, and CI would have failed for lack of a key. Caught before I put a live key in.
- **A retired model, surfaced as a 502**: The first live call failed with `The AI provider rejected the request`. The server log gave the real reason: `gemini-2.5-flash` is no longer available to new keys. The design worked as intended, a 404 is a 4xx, so it failed fast without a pointless retry.
- **Tab counts were wrong when a filter was active**: they were derived from the filtered list, so selecting "New" showed `In progress 0, Completed 0`. Found by clicking through the UI, not by reading the code.
- **A race condition on rapid filter switching**: where a slow earlier response could overwrite a newer one. Fixed with a cancellation guard in the effect.
- **A scrollbar in the filter tab row**: I had it measured rather than guessed; the element had a real 15px scrollbar. The root cause was a CSS rule neither of us would have predicted, setting `overflow-x` makes the other axis compute to `auto`, and the tabs `-1px` bottom margin overflowed it by a single pixel.
- **A spurious SDK warning**: about automatic function calling on every start. We pass no tools, so I had it disabled explicitly rather than left in the log to confuse a reader.

### Real failures observed against the live API, all handled as designed

Running against Gemini produced three distinct upstream failures without my staging any of them:

| Real event | Behaviour |
|---|---|
| `404` retired model | `ClientError` → failed fast, no retry, clean 502 |
| `503` model overloaded | Retried once, then a clean 502, no crash |
| `504 DEADLINE_EXCEEDED` | Retried once, second attempt succeeded, the user saw a normal result |

The 504 is the one I would point to a genuine transient failure at Google's end was absorbed by the retry and the operator never knew. That is the behaviour the brief asks for, demonstrated by accident rather than by simulation.

---

## What I would improve with more time

- **Analysis is synchronous.** A slow provider means the request waits, and a 504 followed by a retry can take tens of seconds. The right shape is `202 Accepted` with the UI polling for the result, so a slow model never occupies a request thread.
- **No caching or rate limiting on `/analyse`.** With a real key that is a cost and abuse path. Caching a result per task would also make repeat views instant.
- **Tasks have no owner.** A real operations queue would assign tasks and default the list to the signed-in user's work — which means a `users` table, authentication and per-user filtering. I left it out deliberately: the brief specifies the task shape exactly and does not include an owner, and building authentication badly is worse than not building it at all.
- **The AI's suggested priority is advisory only.** I would add an explicit "apply suggestion" action so an operator accepts it in one click, plus an audit trail recording that the change originated from an AI suggestion — rather than letting a model write to the record directly.
- **`sqlite3.connect()` silently creates an empty file** when the database is missing, so a misconfigured `DATABASE_PATH` surfaces as `no such table` on the first query instead of a clear startup error. I would verify the schema during startup and fail loudly.
- **The Vite proxy is a development convenience, not an architecture.** A deployment would need a reverse proxy in front of both services, or a configurable API base URL with a properly restricted CORS policy.
- **No CI.** A GitHub Actions workflow running `pytest` and both linters on every push is a small addition I would make next.
- **Structured logging with a request id**, so an AI failure in the log can be traced back to the request that caused it.
