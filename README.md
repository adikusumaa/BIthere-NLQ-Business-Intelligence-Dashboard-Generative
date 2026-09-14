# BIthere

**AI Business Intelligence Analyst**

*Natural Language Query · Auto-Dashboard Generation · Actionable Insights · Multi-Agent Orchestration · Big Data Optimization*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-blue.svg)](https://reactjs.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-purple.svg)](https://langchain.com/langgraph)
[![Groq](https://img.shields.io/badge/Groq-Llama_3.3_70B-orange.svg)](https://groq.com/)
[![Pinecone](https://img.shields.io/badge/Pinecone-Vector_DB-black.svg)](https://pinecone.io/)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-green.svg)](https://supabase.com/)
[![Redis](https://img.shields.io/badge/Redis-Cache-red.svg)](https://redis.io/)
[![Metabase](https://img.shields.io/badge/Metabase-Dashboard-blue.svg)](https://metabase.com/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)](https://docker.com/)

---

## Executive Summary

BIthere is an AI-powered Business Intelligence platform that enables non-technical users to query enterprise data using natural language and receive interactive dashboards, executive insights, and deliverable reports in a single workflow.

The system is designed for organizations where business users depend on data analysts to answer routine questions. It eliminates that dependency by translating a plain-language question into a validated SQL query, executing it against a live data warehouse, generating a ranked visualization dashboard, and delivering the result through email, Slack, or PDF.

---

## Key Highlights & Interface Preview

| Authentication & NL Prompt | Generated Dashboard & Insight |
| :--- | :--- |
| ![Login Page](img/Login%20Page.png)<br>*Secure JWT-based session login* | ![Dashboard Created](img/dashboard%20created.png)<br>*Auto-generated visualization dashboard* |
| ![User Prompting](img/user%20promting.png)<br>*Natural language query entry* | ![Insight](img/Insight.png)<br>*AI-generated executive summary & findings* |

---

## Business Impact

| Metric | Manual Baseline | With BIthere | Improvement |
| :--- | :--- | :--- | :--- |
| Time to first insight | 4 to 48 hours (analyst queue) | Under 15 seconds | Over 99 percent reduction |
| Dashboard creation | 2 to 4 hours per dashboard | Under 90 seconds | Over 98 percent reduction |
| Report delivery | Manual email or export | Automated with screenshots and PDF | Zero manual effort |
| Cost per query | Analyst hourly rate | Under 0.01 USD (with caching) | Over 99 percent reduction |
| Cache hit rate | Not applicable | 60 to 70 percent in steady state | Direct API cost reduction |

---

## Key Features

### 1. Natural Language Query (NLQ)
Users type questions such as "How many fraud transactions occurred in January 2010?" or "Show me the monthly fraud trend by card brand" and the system produces a validated SQL query without manual intervention.

The NLQ pipeline includes:
* Intent classification (query, dashboard, report, or combined)
* Retrieval-Augmented Generation over the database schema and business glossary
* Schema-aware SQL generation with anti-hallucination guardrails
* Safety validation (SELECT only, no destructive statements)
* Automatic optimization (index-aware filters, LIMIT injection)
* Execution against PostgreSQL with automatic retry on connection drop

### 2. Auto-Dashboard Generation
The system converts a single natural-language prompt into a fully populated, interactive multi-page dashboard hosted on Metabase.

Supported capabilities:
* Multi-page dashboards with tab navigation
* Up to 17 charts per dashboard (KPI cards, bar, line, area, donut, funnel, scatter, waterfall, table, gauge)
* Global filters bound to every chart on every page
* Click-through cross-filtering between charts
* Automatic public embed URL generation
* Persistent storage of dashboard configuration in PostgreSQL

### 3. Actionable Insights
Every query result is summarized into a concise executive insight by a dedicated agent. The output follows a consistent structure:
* Executive summary (one paragraph)
* Key findings (three to five bullet points)
* Recommended actions (one to three items)

### 4. Multi-Agent Orchestration (LangGraph)
A LangGraph workflow coordinates seven specialized agents:

| Agent | Responsibility |
| :--- | :--- |
| Planner Agent | Analyzes intent and determines required actions |
| Guard Agent | Rejects out-of-scope or ambiguous questions |
| RAG Retrieval | Fetches relevant schema and glossary context from Pinecone |
| Cache Check | Resolves Redis cache hits for query, LLM response, and dashboard configuration |
| Query Generator | Produces a schema-correct SQL query |
| Validator | Enforces safety rules and blocks destructive statements |
| Query Optimizer | Rewrites query for index usage and avoids full table scans |
| Query Executor | Runs the query with auto-reconnect on connection loss |
| Insight Analyzer | Produces the executive insight |
| Dashboard Builder | Generates Metabase dashboard configuration |
| Report Sender | Dispatches reports through email, Slack, or PDF |
| Response Builder | Streams the final answer and writes cache |

### 5. Retrieval-Augmented Generation (RAG)
Metadata, table schemas, column descriptions, historical queries, and the business glossary are embedded and stored in Pinecone. Retrieval combines semantic similarity with keyword matching, and the resulting context is injected into the query generation prompt.

### 6. Caching and Cost Optimization

| Cache Layer | Key Pattern | TTL | Purpose |
| :--- | :--- | :--- | :--- |
| Query Result | query:{hash} | 1 hour | Skip SQL execution for repeated prompts |
| LLM Response | llm:{hash} | 1 hour | Skip LLM calls for identical inputs |
| Embedding | embedding:{hash} | 24 hours | Skip embedding API calls |
| Dashboard Config | dashboard:{id} | 1 hour | Skip dashboard regeneration |
| Metadata | metadata:{table} | 6 hours | Fast schema lookup |

### 7. Report Delivery
Insights and dashboards can be delivered through three channels:
* Email with inline dashboard screenshots and an attached PDF report
* Slack notifications with dashboard URL
* PDF export with a consultant-grade template

### 8. Role-Based Access Control

| Role | Permissions |
| :--- | :--- |
| Admin | Invite users, manage roles, access audit logs, view system usage |
| Analyst | Query data, generate dashboards, send reports |

### 9. Audit Trail and Governance
Every user action is recorded and available for review:
* Query history with prompt, generated SQL, status, and timestamp
* Ingestion logs for metadata synchronization
* Dashboard configuration snapshots
* User activity timeline

### 10. Dynamic Database Connectors
An abstraction layer allows the system to connect to PostgreSQL, MySQL, or MongoDB without changing the core agent logic.

---

## Additional Interface Screenshots

### Chat Interface
![Chat Page](img/Chat%20page.png)  
*Streaming chat interface with support for multiple conversation sessions.*

### Multi-Page Dashboard & Filtering
![Dashboard Page 2](img/dashboard%20page%202.png)  
*Second page of the dashboard with detailed segment analysis.*

![Filtering Dashboard](img/Flltering%20dashboard.png)  
*Global filters bound to every chart across all pages.*

![Mastercard Filtering](img/mastercard%20filtering.png)  
*Clicking a chart segment automatically applies the corresponding filter.*

### Report Delivery & Notifications
![Export PDF, Email, Slack](img/Export%20pdf%2C%20email%2C%20slack.png)  
*Reports dispatched through email, Slack, or exported as PDF.*

![Slack Notif](img/slack%20notif.png)  
*Real-time Slack alerts with dashboard URL and summary.*

![On iPhone Email](img/on%20iphone%20email.jpeg)  
*Email report rendered on mobile with inline dashboard screenshots.*

### Admin & User Management
![Admin Page](img/Admin%20page.png)  
*User management with role control, invitation flow, and audit visibility.*

![Adding User](img/Adding%20user.png)  
*Admin-only workflow for inviting new users with role assignment.*

---

## System Architecture

```text
User Input (Natural Language)
│
▼
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Backend                      │
│  ┌───────────────────────────────────────────────────┐  │
│  │   Auth Middleware (Supabase JWT)                  │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │   LangGraph Orchestrator                          │  │
│  │                                                   │  │
│  │   Planner → Guard → RAG → Cache Check             │  │
│  │      ↓                                            │  │
│  │   Query Generator → Validator → Optimizer         │  │
│  │      ↓                                            │  │
│  │   Query Executor (Supabase PostgreSQL)            │  │
│  │      ↓                                            │  │
│  │   Insight Analyzer (Groq Llama 3.3 70B)           │  │
│  │      ↓                                            │  │
│  │   Dashboard Builder (Metabase API)                │  │
│  │      ↓                                            │  │
│  │   Report Sender (Slack, Email, PDF)               │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │   MCP Tool Server                                 │  │
│  │   fetch_data, send_slack, send_email,             │  │
│  │   render_dashboard, export_pdf                    │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │   Redis Cache                                     │  │
│  │   query, llm, embedding, dashboard, metadata      │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
│
▼
Streaming Response (SSE) → React Frontend
```

---

## Tech Stack

| Category | Technology |
| :--- | :--- |
| LLM | Groq (Llama 3.3 70B) |
| Embedding | OpenAI text-embedding-3-small |
| Vector Database | Pinecone |
| Source Database | Supabase (PostgreSQL) |
| Cache | Redis |
| Backend | FastAPI, LangGraph |
| Frontend | React, Vite |
| Visualization | Metabase |
| PDF Generation | WeasyPrint, FPDF2 fallback |
| Report Delivery | Slack Webhook, Resend, SMTP |
| Auth | Supabase Auth with JWT |
| Streaming | Server-Sent Events (SSE) |
| Deployment | Docker Compose |

---

## Dataset

The platform is demonstrated against a fintech fraud dataset loaded into Supabase:

| Table | Rows | Description |
| :--- | :--- | :--- |
| users | 1,219 | Customer profiles with age, income, credit score |
| cards | 4,061 | Card details with brand, type, limit, and dark web status |
| transactions | 1,000,000 | Card transactions with date, amount, merchant, and location |
| fraud_labels | 1,000,000 | Fraud labels per transaction |
| mcc_codes | 109 | Merchant Category Codes and descriptions |

---

## Installation and Setup

### Prerequisites
* Docker and Docker Compose
* Node.js 18 or later
* Python 3.10 or later
* Supabase account
* Pinecone account
* Groq API key
* OpenAI API key
* Resend API key or SMTP credentials
* Slack incoming webhook (optional)

### 1. Clone the Repository
```bash
git clone [https://github.com/adikusumaa/BIthere_NLQ-Chatbot-Dashboard-Generation.git](https://github.com/adikusumaa/BIthere_NLQ-Chatbot-Dashboard-Generation.git)
cd BIthere_NLQ-Chatbot-Dashboard-Generation
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and populate all required values:
```env
SUPABASE_URL=[https://your-project.supabase.co](https://your-project.supabase.co)
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_DB_URL=postgresql://postgres.your-ref:password@aws-0-region.pooler.supabase.com:5432/postgres

PINECONE_API_KEY=your-pinecone-key
PINECONE_INDEX_NAME=bithere-metadata

GROQ_API_KEY=your-groq-key
OPENAI_API_KEY=your-openai-key

REDIS_URL=redis://localhost:6379/0

METABASE_URL=http://localhost:3000
METABASE_USERNAME=admin@bithere.local
METABASE_PASSWORD=your-metabase-password

RESEND_API_KEY=your-resend-key
RESEND_FROM=onboarding@resend.dev

SLACK_WEBHOOK_URL=your-slack-webhook

JWT_SECRET=your-jwt-secret
```

### 3. Initialize the Database
Run the application schema script in the Supabase SQL Editor:
```bash
scripts/setup_supabase.sql
```
Load the fintech dataset:
```bash
python scripts/Upload_Supabase.py
```

### 4. Create the Pinecone Index
Create an index named `bithere-metadata` with dimensions matching the embedding model and metric set to cosine.

### 5. Run Metadata Ingestion
```bash
python scripts/ingest_metadata.py
```

### 6. Start the Application Stack
```bash
docker compose up --build
```

Services will be available at:

| Service | URL |
| :--- | :--- |
| Backend API | http://localhost:8000 |
| API Documentation | http://localhost:8000/docs |
| Frontend | http://localhost:5173 |
| Metabase | http://localhost:3000 |

---

## Usage

### Query Data with Natural Language
```text
How many fraud transactions occurred in January 2010?
```
```text
What is the average credit score of users who experienced fraud?
```
```text
Show me the top 10 merchant cities by fraud count.
```

### Generate a Dashboard
```text
Build a fraud analytics dashboard with two pages. Page one should 
show KPI cards, monthly trend, and top 10 states. Page two should 
show card brand, chip usage, and MCC category breakdown. Add global 
filters for card brand, merchant state, chip usage, and card type.
```

### Generate and Deliver a Report
```text
Analyze fraud in January 2010, build a two-page dashboard with 
monthly trend and breakdown by card brand, then send the report 
to my email.
```

---

## Testing

Run all tests:
```bash
pytest test/
```
Run a specific test module:
```bash
pytest test/test_query_generator.py -v -s
```

---

## Security and Compliance

| Aspect | Implementation |
| :--- | :--- |
| Authentication | Supabase Auth with JWT validation |
| Authorization | Role-based access control (admin, analyst) |
| Query Safety | Validator agent enforces SELECT-only queries |
| SQL Injection | Parameter sanitization and allowlist validation |
| Secrets Management | Environment variables with .gitignore protection |
| Audit Trail | Complete query history and ingestion logs |
| Data Isolation | Row-level security on application tables |
| Rate Limit Handling | Exponential backoff with retry policy |
| Error Handling | User-friendly messages with internal logging |

---

## Roadmap

| Phase | Description | Status |
| :--- | :--- | :--- |
| 1 | Preparation and Foundation | Completed |
| 2 | Backend Core | Completed |
| 3 | RAG and Embedding | Completed |
| 4 | Agent Orchestration | Completed |
| 5 | MCP Server and Tools | Completed |
| 6 | API Routes | Completed |
| 7 | Frontend Application | Completed |
| 8 | End-to-End Integration | Completed |
| 9 | Testing | In Progress |
| 10 | Finalization and Documentation | In Progress |

---

## Future Enhancements
* Semantic cache for LLM responses
* Multi-tenant architecture with per-client data isolation
* Cost and token usage dashboard
* Natural language dashboard refinement
* Additional database connectors (MySQL, MongoDB)
* SSO integration for enterprise deployment

---

## Contributing
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -m 'Add AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

---

## License
Distributed under the MIT License. Developed by Adi Kusuma.