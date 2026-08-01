<div align="center">
# Customer Complaint Management System
### AI-Assisted Complaint Intake for API & FDF Quality Assurance

An AI-powered Customer Complaint module for a pharmaceutical Quality Management System (QMS).
QA staff can log a complaint manually, or **drop in the source document / email and let an AI
agent extract and pre-fill the form**, then ask a chat assistant follow-up questions about the
complaint — all while keeping a clear audit trail of what was AI-suggested vs. human-confirmed.

[![Frontend](https://img.shields.io/badge/Frontend-React%20%2B%20Redux-61DAFB?logo=react&logoColor=black)](#)
[![Backend](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white)](#)
[![AI](https://img.shields.io/badge/AI%20Agent-LangGraph-1C3C3C)](#)
[![LLM](https://img.shields.io/badge/LLM-Groq-orange)](#)
[![Database](https://img.shields.io/badge/Database-MySQL-4479A1?logo=mysql&logoColor=white)](#)
[![License](https://img.shields.io/badge/License-MIT-lightgrey)](#)

</div>

---

## 📖 Table of Contents
 
- [Overview](#-overview)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Complaint Intake Flow](#-complaint-intake-flow)
- [AI Risk Assessment](#-ai-risk-assessment)
- [Repository Layout](#-repository-layout)
- [Getting Started](#-getting-started)
  - [Option A — Docker (recommended)](#option-a--docker-recommended)
  - [Option B — Run Locally](#option-b--run-locally)
- [Database Setup](#-database-setup-mysql-or-postgresql)
  - [MySQL](#mysql)
  - [PostgreSQL](#postgresql)
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
2. A **LangGraph agent**, backed by **Groq's `openai/gpt-oss-20b`**, extracts structured fields
   (customer, product, batch/lot, dates, severity, priority, etc.) and returns them as JSON.
3. The **React form auto-populates**, visually flagging which fields came from the AI so a
   reviewer knows exactly what to double-check before saving.
4. A **chat assistant** (Groq's `llama-3.3-70b-versatile`) is available alongside the form to
   answer follow-up questions about the complaint, with the conversation persisted for the audit
   trail.
5. The same assistant can **add or edit form fields directly from a chat message** — e.g. typing
   "set severity to Critical" or "the batch number is AMX-2026-0417" updates the form live, with
   the same AI-provenance badge as document extraction.
6. On demand, an **AI risk assessment** agent evaluates the current complaint and returns a
   structured risk level, key concerns, and recommended next actions to help a reviewer triage
   faster.
## 🛠 Tech Stack
 
| Layer            | Technology                                                                     |
| ---------------- | ------------------------------------------------------------------------------ |
| Frontend         | React 18, Redux Toolkit, Tailwind CSS, Google**Inter** font              |
| Backend          | Python, FastAPI, SQLAlchemy                                                    |
| AI Agent         | LangGraph (extraction validate/retry loop, chat + field-edit detection, risk assessment) |
| LLMs             | Groq —`openai/gpt-oss-20b` (extraction), `llama-3.3-70b-versatile` (chat & risk assessment) |
| Database         | MySQL **or** PostgreSQL — fully portable via a single`DATABASE_URL`         |
| Containerization | Docker + Docker Compose                                                        |
 
## 🏗 Architecture
 
```mermaid
flowchart LR
    subgraph UI["🖥️ Frontend — frontend (React + Redux)"]
        A1[Complaint Form]
        A2[AI Intake Assistant Panel]
        A3[Redux Store]
    end
 
    subgraph API["⚙️ Backend — backend (FastAPI)"]
        B1["/api/complaints — CRUD"]
        B2["/api/ai/extract"]
        B3["/api/ai/chat"]
        B4["/api/ai/risk-assessment"]
    end
 
    subgraph AGENTS["🤖 LangGraph Agents"]
        C1["extraction_agent.py
        extract → validate → retry/finalize
        (Groq openai/gpt-oss-20b)"]
        C2["chat_agent.py
        parse_updates → respond
        (Groq llama-3.3-70b-versatile)"]
        C3["risk_agent.py
        assess
        (Groq llama-3.3-70b-versatile)"]
    end
 
    subgraph DB["🗄️ Database — MySQL or PostgreSQL"]
        D1[(complaints)]
        D2[(attachments)]
        D3[(chat_messages)]
    end
 
    A1 <--> A3
    A2 <--> A3
    A3 <-- "REST / multipart JSON" --> B1
    A3 <-- "REST / multipart JSON" --> B2
    A3 <-- "REST / multipart JSON" --> B3
    A3 <-- "REST / multipart JSON" --> B4
 
    B2 --> C1
    B3 --> C2
    B4 --> C3
 
    B1 <--> D1
    B1 <--> D2
    B2 --> D1
    B3 --> D3
    B4 --> D1
 
    style UI fill:#61DAFB22,stroke:#61DAFB
    style API fill:#00968822,stroke:#009688
    style AGENTS fill:#1C3C3C22,stroke:#1C3C3C
    style DB fill:#4479A122,stroke:#4479A1
```
 
## 🔄 Complaint Intake Flow
 
End-to-end walk-through of what happens when a QA reviewer submits a raw complaint document,
from upload through to a saved, auditable record:
 
```mermaid
flowchart TD
    START([QA reviewer has a raw complaint
    PDF / DOCX / TXT / EML]) --> UPLOAD["Upload or paste document
    in AI Intake Assistant panel"]
 
    UPLOAD --> PARSE["Backend document parser
    extracts raw text"]
 
    PARSE --> EXTRACT["extraction_agent.py
    (LangGraph + Groq openai/gpt-oss-20b)"]
 
    EXTRACT --> VALIDATE{Validate
    extracted fields}
    VALIDATE -- "invalid / incomplete" --> RETRY["Retry extraction
    with corrective prompt"]
    RETRY --> EXTRACT
    VALIDATE -- "valid" --> FINALIZE["Finalize structured JSON
    (customer, product, batch/lot,
    dates, severity, priority)"]
 
    FINALIZE --> PREFILL["React form auto-populates
    fields tagged with 'AI' badge"]
 
    PREFILL --> REVIEW{QA reviewer
    checks each field}
    REVIEW -- "edits a field" --> UNFLAG["AI badge removed
    on edited field"]
    UNFLAG --> REVIEW
    REVIEW -- "asks chat to add/edit a field" --> CHATEDIT["chat_agent.py parse_updates
    applies field to form
    (same AI badge treatment)"]
    CHATEDIT --> REVIEW
    REVIEW -- "requests risk assessment" --> RISK["risk_agent.py
    returns risk level, concerns,
    recommended actions"]
    RISK --> REVIEW
    REVIEW -- "confirms all fields" --> SAVE["Click 'Save Complaint'"]
 
    SAVE --> PERSIST["Persist Complaint + Attachment
    + ai_populated_fields to database"]
 
    PERSIST --> TRIAGE["Record enters
    'Pending Triage' status"]
 
    TRIAGE --> CHAT["Optional: ask chat assistant
    follow-up questions
    (e.g. 'Does this need a CAPA?')"]
    CHAT --> CHATLOG["Response + question
    persisted to ComplaintChatMessage
    for audit trail"]
 
    CHATLOG --> DONE([Complaint logged,
    traceable, audit-ready])
    TRIAGE --> DONE
```
 
## 🩺 AI Risk Assessment
 
Alongside extraction and chat, the AI panel has a **"Generate Risk Assessment"** button that
gives a QA reviewer a fast, structured read on how serious a complaint looks, before or after
it's saved.
 
### How it works
 
`backend/app/services/risk_agent.py` is a single-node LangGraph app that takes the complaint's
current field values (product, batch/lot, quantity affected, complaint type, description,
severity, priority) and prompts Groq's `llama-3.3-70b-versatile` — the larger reasoning model,
since this task needs judgment rather than extraction — with a QMS-flavored system prompt asking
for a **conservative, evidence-based** assessment.
 
```mermaid
flowchart LR
    TRIGGER(["Reviewer clicks
    'Generate Risk Assessment'"]) --> SRC{Complaint
    already saved?}
    SRC -- "yes" --> BYID["Look up complaint
    by complaint_id"]
    SRC -- "no" --> BYFIELDS["Use current
    in-progress form fields"]
    BYID --> ASSESS["risk_agent.py
    assess node
    (Groq llama-3.3-70b-versatile)"]
    BYFIELDS --> ASSESS
    ASSESS --> RESULT["Structured JSON:
    risk_level, summary,
    key_concerns, recommended_actions,
    regulatory_flag"]
    RESULT --> CARD["Rendered as a
    risk card in the AI panel"]
```
 
### What it returns
 
```json
{
  "risk_level": "Major",
  "summary": "Visible discoloration in ~15% of capsules from a single batch, with intact packaging and no reported adverse events, suggests a manufacturing or stability issue affecting product quality.",
  "key_concerns": [
    "Discoloration may indicate a stability or degradation issue",
    "Remaining unaffected stock from the same batch is still in circulation"
  ],
  "recommended_actions": [
    "Initiate a batch investigation, including relevant stability data review",
    "Quarantine remaining stock from the batch pending disposition"
  ],
  "regulatory_flag": false
}
```
 
- **`risk_level`** — `Critical` / `High` / `Medium` / `Low`
- **`regulatory_flag`** — set to `true` only for things that plausibly warrant regulatory
  reportability review (adverse events, sterility/identity failures, potential recalls) — the
  model is instructed to be conservative here rather than over-flag
- The UI colors the risk badge accordingly and shows a separate purple "Regulatory Review
  Suggested" badge when `regulatory_flag` is true
### API
 
```
POST /api/ai/risk-assessment
```
Accepts either `complaint_id` (form field, for a saved complaint) **or** `fields_json` (a JSON
string of the current in-progress form fields, so it works before the complaint is saved) — you
provide one or the other, not both.
 
### Important framing
 
Like the rest of the AI features in this project, the risk assessment is a **drafting aid, not a
compliance decision**. The system prompt explicitly frames it that way, and the UI doesn't let a
risk assessment auto-change the complaint's severity/priority or status — a human reviewer still
confirms those before the record leaves `Pending Triage`, consistent with the audit-trail
philosophy described in [QMS Design Notes](#-qms-design-notes).
 
## 📁 Repository Layout
 
```
complaint-mgmt-system/
├── frontend/                   React + Redux frontend
│   ├── src/components/         ComplaintForm, AIAssistantPanel, form fields
│   ├── src/store/               Redux slices (complaint, aiAssistant)
│   └── src/api/client.js        Backend API calls
│
├── backend/                     FastAPI backend
│   ├── app/models/              SQLAlchemy models (Complaint, Attachment, ChatMessage)
│   ├── app/routers/              /api/complaints and /api/ai routes
│   ├── app/services/             extraction_agent.py, chat_agent.py, risk_agent.py,
│   │                              document_parser.py
│   └── tests/                   Pytest suite
│
├── sample-data/                 Sample complaint PDF for testing extraction
├── docker-compose.yml           Database + backend + frontend, one command
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
 
Stop everything with `docker compose down` (add `-v` to also wipe the database volume — always
do this if you switch database engines, see below, since the volume format isn't interchangeable
between MySQL and PostgreSQL).
 
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
 
You'll need a MySQL or PostgreSQL instance running locally — see [Database Setup](#-database-setup-mysql-or-postgresql)
below for either.
 
## 🗄 Database Setup (MySQL or PostgreSQL)
 
The backend is fully portable between the two — same models, same migrations-free `create_all`
startup, same code. Pick whichever you have available; only `DATABASE_URL` changes.
 
### MySQL
 
**1. Create the database, a dedicated user, and grant privileges:**
```sql
CREATE DATABASE complaint_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'complaint_app'@'%' IDENTIFIED BY 'change_this_password';
GRANT ALL PRIVILEGES ON complaint_db.* TO 'complaint_app'@'%';
FLUSH PRIVILEGES;
```
 
**2. Set `backend/.env`:**
```
DATABASE_URL=mysql+pymysql://complaint_app:change_this_password@localhost:3306/complaint_db
```
 
**3. Docker Compose:** the `db` service uses `mysql:8.0` (image, env vars
`MYSQL_DATABASE`/`MYSQL_USER`/`MYSQL_PASSWORD`, port `3306`, volume mounted at
`/var/lib/mysql`), and the `backend` service's `DATABASE_URL` points at
`mysql+pymysql://...@db:3306/complaint_db` — `db` is the internal Compose network hostname, not
`localhost`.
 
**Note:** MySQL 8's default auth plugin needs the `cryptography` Python package for `pymysql` to
authenticate — already included in `requirements.txt`.
 
### PostgreSQL
 
**1. Create the database, a dedicated user, and grant privileges** (via `psql` or pgAdmin's Query Tool):
```sql
CREATE DATABASE complaint_db;
CREATE USER complaint_app WITH PASSWORD 'change_this_password';
GRANT ALL PRIVILEGES ON DATABASE complaint_db TO complaint_app;
GRANT ALL ON SCHEMA public TO complaint_app;
```
 
**2. Set `backend/.env`:**
```
DATABASE_URL=postgresql+psycopg2://complaint_app:change_this_password@localhost:5432/complaint_db
```
 
**3. Docker Compose:** `db` service uses `postgres:16-alpine`, env vars `POSTGRES_DB` /
`POSTGRES_USER` / `POSTGRES_PASSWORD`, port `5432`, volume mounted at
`/var/lib/postgresql/data`, and the `backend` service's `DATABASE_URL` should point at
`postgresql+psycopg2://...@db:5432/complaint_db` (again, `db` — not `localhost` — from inside the
container).
 
**pgAdmin 4:** Register a server pointing at `localhost:5432` (or your remote host), then
right-click **Databases → Create → Database…** to create `complaint_db` through the UI instead
of the SQL above, if you prefer a GUI.
 
> **Switching between MySQL and PostgreSQL under Docker:** the two engines store data on disk in
> completely incompatible formats. If you switch `docker-compose.yml`'s `db` service from one to
> the other, you **must** run `docker compose down -v` first to wipe the old volume — otherwise
> the new engine will fail to start against a data directory it doesn't recognize.
 
## 🔑 Environment Variables
 
**`backend/.env`**
 
| Variable                  | Description                                                        |
| ------------------------- | ------------------------------------------------------------------ |
| `DATABASE_URL`          | MySQL: `mysql+pymysql://user:password@host:3306/complaint_db` <br> PostgreSQL: `postgresql+psycopg2://user:password@host:5432/complaint_db` |
| `FRONTEND_ORIGIN`       | Allowed CORS origin, e.g.`http://localhost:5173`                 |
| `GROQ_API_KEY`          | Your key from[console.groq.com/keys](https://console.groq.com/keys) |
| `GROQ_EXTRACTION_MODEL` | Default:`openai/gpt-oss-20b`                                     |
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
   or *"set priority to High"* to see chat-driven field edits in action.
6. Click **Generate Risk Assessment** to see the structured risk card for the current complaint.
If the backend or Groq key isn't reachable, the UI automatically falls back to a mock extraction
so the demo still works end-to-end.
 
## ✅ Testing
 
```bash
cd backend
pytest tests/ -v
```
 
Covers complaint create/read/list/filter/update/delete and the 404 path, using an isolated
SQLite database so no live MySQL/PostgreSQL connection is required to run tests.
 
## 📋 QMS Design Notes
 
- **Traceability:** Section 1–2 of the form (origin, product/batch ID) support tracing a
  complaint back to a specific batch/lot for impact assessment.
- **Triage:** Severity/Priority (Section 4) are AI-suggested but require human confirmation
  before a record moves out of `Pending Triage` — the AI is a drafting aid, not an autonomous
  decision-maker. This applies equally to AI risk assessments — they inform triage, they don't
  set it automatically.
- **Audit trail:** `ai_populated_fields` on each complaint record, plus a persisted chat log
  (`ComplaintChatMessage`), keep it clear which values were machine-suggested vs. human-confirmed
  — important for data integrity in a regulated environment. Chat-driven field edits go through
  the same `ai_populated_fields` tracking as document extraction.
## 🗺 Roadmap
 
- [ ] Alembic migrations instead of `create_all` for production environments
- [ ] Auth / role-based access (QA reviewer vs. submitter)
- [ ] Per-field confidence scores surfaced in the UI
- [ ] Streaming extraction progress over SSE/WebSocket
- [ ] Persist risk assessment history per complaint (currently generated on demand, not stored)
---
 
<div align="center">
Built for a pharmaceutical API & FDF Quality Assurance Module assignment.
</div>
 