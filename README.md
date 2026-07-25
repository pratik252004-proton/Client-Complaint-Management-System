<div align="center">

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Repository Layout](#-repository-layout)
- [Getting Started](#-getting-started)
  - [Option A — Docker (recommended)](#option-a--docker-recommended)
  - [Option B — Run Locally](#option-b--run-locally)
- [Environment Variables](#-environment-variables)
- [Trying It Out](#-trying-it-out)
- [Testing](#-testing)
- [QMS Design Notes](#-qms-design-notes)
- [Roadmap](#-roadmap)

---

## 🔍 Overview

Pharmaceutical manufacturers handling **API** (Active Pharmaceutical Ingredient) and **FDF**
(Finished Dosage Form) products are required to log, triage, and investigate customer complaints
as part of their Quality Management System (broadly aligned with **ICH Q10** and **21 CFR
211.198** complaint-handling expectations). In practice, most complaints arrive as free-text
emails or scanned letters, and QA staff spend a lot of time manually transcribing them into a
structured record.

This project automates that transcription step:

1. A QA reviewer **uploads or pastes** the raw complaint (PDF, DOCX, TXT, EML, or plain text).
2. A **LangGraph agent**, backed by **Groq's `gemma2-9b-it`**, extracts structured fields
   (customer, product, batch/lot, dates, severity, priority, etc.) and returns them as JSON.
3. The **React form auto-populates**, visually flagging which fields came from the AI so a
   reviewer knows exactly what to double-check before saving.
4. A **chat assistant** (Groq's `llama-3.3-70b-versatile`) is available alongside the form to
   answer follow-up questions about the complaint, with the conversation persisted for the audit
   trail.

## 🛠 Tech Stack

| Layer            | Technology                                                               |
| ---------------- | ------------------------------------------------------------------------ |
| Frontend         | React 18, Redux Toolkit, Tailwind CSS, Google**Inter** font        |
| Backend          | Python, FastAPI, SQLAlchemy                                              |
| AI Agent         | LangGraph (state machine with validate/retry loop)                       |
| LLMs             | Groq —`gemma2-9b-it` (extraction), `llama-3.3-70b-versatile` (chat) |
| Database         | MySQL (also supports PostgreSQL — swap via`DATABASE_URL`)             |
| Containerization | Docker + Docker Compose                                                  |

## 🏗 Architecture

```
┌───────────────────────┐        REST / multipart           ┌────────────────────────────┐
│   React + Redux UI    │ ──────────────────────────────>   │   FastAPI Backend          │
│  (phase1-ui)          |  <──────────────────────────────  │   (phase2-backend)         │
│                       │        JSON responses             │                            |
│ • Complaint form      │                                   │   /api/complaints  (CRUD)  │
│ • AI Intake Assistant │                                   │   /api/ai/extract          │
│ • Redux state         │                                   │   /api/ai/chat             │
└───────────────────────┘                                   └─────────────┬──────────────┘
                                                                          │
                                                     ┌────────────────────┴─────────────────────┐
                                                     │           LangGraph Agents               │
                                                     |                                          │
                                                     |   extraction_agent.py                    │
                                                     |   extract ─▶ validate ─▶ retry/finalize │
                                                     |   (Groq gemma2-9b-it)                    │
                                                     |                                          │
                                                     |   chat_agent.py                          │
                                                     |   respond (Groq llama-3.3-70b-versatile) │
                                                     └────────────────────┬─────────────────────┘
                                                                          | 
                                                                ┌─────────┴─────────┐
                                                                |   MySQL Database  │
                                                                |   complaints,     │
                                                                |   attachments,    │
                                                                |   chat_messages   │
                                                                └───────────────────┘
```

## 📁 Repository Layout

```
complaint-mgmt-system/
├── frontend/                    React + Redux frontend
│   ├── src/components/          ComplaintForm, AIAssistantPanel, form fields
│   ├── src/store/               Redux slices (complaint, aiAssistant)
│   └── src/api/client.js        Backend API calls
│
├── backend/                     FastAPI backend
│   ├── app/models/              SQLAlchemy models (Complaint, Attachment, ChatMessage)
│   ├── app/routers/             /api/complaints and /api/ai routes
│   ├── app/services/            LangGraph agents + document parser
│   └── tests/                   Pytest suite
│
├── sample-data/                 Sample complaint PDF for testing extraction
├── docker-compose.yml           MySQL + backend + frontend, one command
└── README.md
```

## 🚀 Getting Started

### Option A — Docker (recommended)

**Prerequisites:** Docker Desktop (or Docker Engine + Compose plugin)

```bash
git clone <this-repo-url>
cd complaint-mgmt-system

cp backend/.env.example backend/.env
# then edit backend/.env and set GROQ_API_KEY

docker compose up --build
```

| Service          | URL                              |
| ---------------- | -------------------------------- |
| Frontend         | http://localhost:5173            |
| Backend API docs | http://localhost:8000/docs       |
| Health check     | http://localhost:8000/api/health |

Stop everything with `docker compose down` (add `-v` to also wipe the database volume).

### Option B — Run Locally

**Backend**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # set DATABASE_URL + GROQ_API_KEY
uvicorn app.main:app --reload
```

**Frontend** (separate terminal)

```bash
cd frontend
npm install
cp .env.example .env      # VITE_API_BASE=http://localhost:8000
npm run dev
```

You'll need a MySQL instance running locally — see [`.env.example`](backend/.env.example)
for the connection string format.

## 🗄 Database Setup (MySQL)

If you're not using Docker (see Option A below, which provisions MySQL for you), you'll need a
local MySQL instance with a dedicated database and user before starting the backend.

```sql
CREATE DATABASE complaint_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'complaint_app'@'localhost' IDENTIFIED BY 'Your_Password';
GRANT ALL PRIVILEGES ON complaint_db.* TO 'complaint_app'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

Update `DATABASE_URL` in `backend/.env` to match:

```
DATABASE_URL=mysql+pymysql://complaint_app:Your_Password@localhost:3306/complaint_db
```

## 🔑 Environment Variables

**`backend/.env`**

| Variable                  | Description                                                        |
| ------------------------- | ------------------------------------------------------------------ |
| `DATABASE_URL`          | `mysql+pymysql://user:password@host:3306/complaint_db`           |
| `FRONTEND_ORIGIN`       | Allowed CORS origin, e.g.`http://localhost:5173`                 |
| `GROQ_API_KEY`          | Your key from[console.groq.com/keys](https://console.groq.com/keys) |
| `GROQ_EXTRACTION_MODEL` | Default:`gemma2-9b-it`                                           |
| `GROQ_CHAT_MODEL`       | Default:`llama-3.3-70b-versatile`                                |
| `MAX_UPLOAD_MB`         | Max upload size for complaint documents (default`10`)            |

**`frontend/.env`**

| Variable          | Description                                     |
| ----------------- | ----------------------------------------------- |
| `VITE_API_BASE` | Backend base URL, e.g.`http://localhost:8000` |

## 🧪 Trying It Out

1. Open the app and go to the **AI Complaint Intake Assistant** panel on the right.
2. Upload [`sample-data/sample_customer_complaint.pdf`](sample-data/sample_customer_complaint.pdf) —
   a realistic complaint letter about a batch quality defect — or drag/drop your own PDF, DOCX,
   TXT, or EML.
3. Watch the extraction progress bar, then check the **left-hand form** — fields populated by the
   AI are highlighted with an "AI" badge.
4. Review/correct any fields (this removes the AI badge on that field), then click **Save
   Complaint**.
5. Try the chat box at the bottom of the AI panel — e.g. *"Does this look like it needs a CAPA?"*

If the backend or Groq key isn't reachable, the UI automatically falls back to a mock extraction
so the demo still works end-to-end.

## ✅ Testing

```bash
cd backend
pytest tests/ -v
```

Covers complaint create/read/list/filter/update/delete and the 404 path, using an isolated
SQLite database so no live MySQL connection is required to run tests.

## 📋 QMS Design Notes

- **Traceability:** Section 1–2 of the form (origin, product/batch ID) support tracing a
  complaint back to a specific batch/lot for impact assessment.
- **Triage:** Severity/Priority (Section 4) are AI-suggested but require human confirmation
  before a record moves out of `Pending Triage` — the AI is a drafting aid, not an autonomous
  decision-maker.
- **Audit trail:** `ai_populated_fields` on each complaint record, plus a persisted chat log
  (`ComplaintChatMessage`), keep it clear which values were machine-suggested vs. human-confirmed
  — important for data integrity in a regulated environment.

## 🗺 Roadmap

- [X] Alembic migrations instead of `create_all` for production environments
- [X] Auth / role-based access (QA reviewer vs. submitter)
- [X] Per-field confidence scores surfaced in the UI
- [X] Streaming extraction progress over SSE/WebSocket

---

<div align="center">
Built for a pharmaceutical API & FDF Quality Assurance Module assignment.
</div>
