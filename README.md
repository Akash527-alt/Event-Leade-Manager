# AI Event Lead Manager

A small full-stack app for capturing and following up with people you meet at business events. Add leads, search and filter them, and use **Gemini** to summarise your conversation notes or draft a follow-up email.

- **Frontend:** React 18 + Vite
- **Backend:** Python FastAPI + SQLAlchemy 2
- **Database:** PostgreSQL (SQLite works locally with zero setup)
- **AI:** Google Gemini via its REST API

**Live app:** `<ADD LIVE LINK>` · **API docs:** `<BACKEND URL>/docs`

## Features

- Add, edit, delete leads (name, company, email, event, notes, follow-up status)
- Search across name, company, email, event and notes; filter by status and by event
- Follow-up statuses: Not contacted → Contacted → Replied → Meeting booked → Closed
- **AI:** "Summarise notes" (short bullet summary) and "Draft follow-up" (email with tone selector, editable result, copy / open in email app)
- Responsive UI (table on desktop, stacked cards on phones), light and dark mode
- Backend test suite (16 tests, AI calls mocked)

## Project structure

```
backend/
  app/
    main.py          # app setup, CORS, table creation
    config.py        # env-based settings
    database.py      # engine + session dependency
    models.py        # Lead model
    schemas.py       # request/response validation
    ai.py            # Gemini prompts + HTTP call
    routers/leads.py # CRUD, search, filter
    routers/ai.py    # summarise / follow-up endpoints
  tests/
frontend/
  src/
    App.jsx          # state, filters, modals
    api.js           # fetch wrapper with readable errors
    components/      # LeadTable, LeadForm, AiPanel, Modal, StatusBadge
```

## Setup (local)

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # then edit .env (see below)
uvicorn app.main:app --reload    # http://localhost:8000  (docs at /docs)
```

Edit `backend/.env`:

| Variable | What to put |
| --- | --- |
| `DATABASE_URL` | Your Postgres URL, e.g. `postgresql://user:pass@host:5432/dbname`. While it is still the placeholder, the app uses a local SQLite file so it runs out of the box. |
| `GEMINI_API_URL` | Full Gemini `generateContent` endpoint, e.g. `https://generativelanguage.googleapis.com/v1beta/models/<model>:generateContent` |
| `GEMINI_API_KEY` | Your Gemini API key (from Google AI Studio) |
| `CORS_ORIGINS` | Comma-separated frontend origins allowed to call the API |

Tables are created automatically on startup. Until the Gemini values are filled in, the AI buttons show a clear "AI is not configured yet" message instead of failing silently.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev                      # http://localhost:5173
```

In development, Vite proxies `/api` to `localhost:8000`, so no extra config is needed.

### 3. Tests

```bash
cd backend && pytest
```

## Deployment

1. **Database:** create a free Postgres instance (Neon, Supabase or Render) and copy its connection string.
2. **Backend (Render / Railway):** root directory `backend`, build `pip install -r requirements.txt`, start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Set `DATABASE_URL`, `GEMINI_API_URL`, `GEMINI_API_KEY`, and `CORS_ORIGINS` (your frontend URL).
3. **Frontend (Vercel / Netlify):** root directory `frontend`, build `npm run build`, output `dist`. Set `VITE_API_URL` to the backend URL.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/leads?search=&status=&event=&limit=&offset=` | List, search, filter (newest first) |
| POST | `/api/leads` | Create a lead |
| GET | `/api/leads/{id}` | Get one lead |
| PUT | `/api/leads/{id}` | Update (partial: send only changed fields) |
| DELETE | `/api/leads/{id}` | Delete a lead |
| GET | `/api/events` | Distinct event names (for the filter) |
| POST | `/api/leads/{id}/summarize` | AI summary of the lead's notes |
| POST | `/api/leads/{id}/follow-up` | AI follow-up email (`tone`, `sender_name`) |
| GET | `/api/health` | Health check |

## Key decisions

- **FastAPI + SQLAlchemy:** typed request validation (Pydantic) gives clean 422 errors for free, and the same models work on Postgres and SQLite, which keeps local setup and tests simple.
- **Single `leads` table:** the assignment's data is flat, so a single table with indexes on `status` and `event` is the simplest design that supports the filters. Statuses are validated against a fixed set at the API layer.
- **Server-side search and filtering:** done in SQL (`ILIKE` + exact filters) rather than in the browser, so it keeps working as the list grows. The UI debounces typing and ignores stale responses.
- **AI behind the backend:** the Gemini key never reaches the browser. Prompts instruct the model to use only facts from the notes, to avoid invented details. Results are editable before copying, because a human should review AI-written emails before sending.
- **Config via env vars:** the Gemini URL and key are not hard-coded, so the model can be swapped without code changes. Upstream failures map to clear HTTP codes (503 not configured, 502 Gemini error).
- **Tables via `create_all`:** fine at this scale; a growing app would move to Alembic migrations.

## Possible next steps

Authentication and per-user leads, pagination controls in the UI, CSV import/export, saving generated emails against a lead, and streaming AI responses.
