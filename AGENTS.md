# AGENTS.md

Project-level instructions for future Codex/agent work in this repository.

## Scope

These instructions apply to the whole repository.

## Project Shape

- This is a lightweight full-stack demo app for managing Chinese meeting summaries.
- Backend: FastAPI + SQLModel + SQLite in `backend/`.
- Frontend: Vue 3 + Vite + plain CSS in `frontend/`.
- Summary generation uses an OpenAI-compatible Chat Completions API configured by `backend/.env`.

## Run Commands

Backend:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Build frontend:

```bash
cd frontend
npm run build
```

Default local URLs:

- Backend API: `http://127.0.0.1:8000`
- API docs: `http://127.0.0.1:8000/docs`
- Frontend dev server: `http://127.0.0.1:5173`

## Interface Contracts

Backend endpoints currently used by the frontend:

- `POST /meetings`
  - Request body: `{ "title": string, "transcript": string }`
  - Response: full meeting object with `id`, `title`, `transcript`, `summary`, `action_items`, `keywords`, and `created_at`.
- `GET /meetings`
  - Response: meeting list ordered by `created_at` descending.
- `GET /meetings/{meeting_id}`
  - Response: full meeting object.

The frontend hardcodes `API_BASE_URL = 'http://127.0.0.1:8000'` in `frontend/src/App.vue`.

Model output parsing in `backend/main.py` expects JSON fields:

- `summary`: Chinese meeting summary.
- `action_items`: Chinese action items separated by newlines.
- `keywords`: 3 to 6 Chinese keywords separated by English commas.

If any API shape, environment variable, port, or model-output contract changes, update this file and the README together.

## Local Files and Generated Artifacts

Do not treat these as source changes unless the user explicitly asks:

- `backend/.env`
- `backend/.venv/`
- `backend/meetings.db`
- `backend/__pycache__/`
- `frontend/node_modules/`
- `frontend/dist/`

Keep secrets out of commits and documentation. Use `backend/.env.example` for public configuration examples.

## Code Style Notes

- Keep the app beginner-friendly and easy to read.
- Backend code is currently a single `backend/main.py`; prefer small, obvious changes unless the feature clearly requires splitting modules.
- Frontend code is currently a single Vue SFC plus `App.css`; follow the existing simple Composition API style.
- UI copy is Chinese-first. Keep user-facing validation and error messages in Chinese unless the surrounding UI changes direction.
- Use plain CSS and existing layout conventions before adding new UI libraries.

## Verification

Use the narrowest useful checks for the change:

- Backend syntax/import sanity: run from `backend/` with the virtualenv active if available.
- Frontend build: `cd frontend && npm run build`.
- For user-facing frontend changes, run the dev server and verify in the browser when practical.

## Maintenance Rule

If a future task reveals a repeated pitfall, changed command, changed interface contract, changed port, new required environment variable, or any repository-specific convention worth remembering, update this `AGENTS.md` proactively in the same task.
