# BIthere - AI Business Intelligence Analyst

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

**BIthere** is an AI-powered Business Intelligence platform that enables non‑technical users to query enterprise data using natural language (NLQ). It automatically generates interactive dashboards, delivers actionable insights, and optimizes performance through a multi‑agent architecture and intelligent caching — all designed for big data scale.

---

## Key Features

- **Natural Language Query (NLQ)**  
  Ask questions in Indonesian or English; BIthere translates them into SQL (or NoSQL) queries without manual coding.

- **Multi‑Agent Orchestration (LangGraph)**  
  Seven specialized agents collaborate sequentially:
  - Planner Agent
  - Query Generator Agent
  - Validator Agent
  - Query Optimizer Agent
  - Insight Analyzer Agent
  - Dashboard Builder Agent
  - Report Sender Agent

- **RAG‑Powered Metadata Understanding**  
  Retrieval‑Augmented Generation over database schema, business glossary, and historical queries ensures context‑aware query generation.

- **Auto‑Dashboard Generation**  
  Automatically creates visualizations in Metabase from query results, returning embeddable dashboards.

- **Actionable Insights & Reporting**  
  Summarizes data into business insights and sends reports to Slack or Email (PDF via WeasyPrint).

- **Dynamic Database Connectors**  
  Supports PostgreSQL, MySQL, and MongoDB through an abstraction layer. Primary data source: Supabase (PostgreSQL).

- **Intelligent Caching Layer**  
  Redis caches query results, LLM responses, embeddings, and dashboard configs with TTL and automatic invalidation.

- **Query Optimization for Big Data**  
  Indexing, partitioning, materialized views, sampling, and `EXPLAIN ANALYZE` ensure performance on 1‑million‑row datasets.

- **MCP Server Integration**  
  Exposes tools (`fetch_data`, `send_slack`, `send_email`, `render_dashboard`, `export_pdf`) via Model Context Protocol for secure agent‑tool interaction.

- **Role‑Based Access Control**  
  Supabase Auth with `admin` and `analyst` roles; admin can invite and manage users.

- **Streaming Chat**  
  Server‑Sent Events (SSE) deliver real‑time token streaming in the chat interface.

---

## Tech Stack

### Frontend
- **Framework:** React (Vite)
- **State Management:** Zustand
- **API / SSE:** fetch + EventSource
- **Auth:** Supabase Auth client

### Backend
- **Language:** Python 3.10+
- **API Framework:** FastAPI + Uvicorn
- **Agent Orchestration:** LangGraph
- **LLM:** Groq API (Llama 3.3 70B)
- **Embedding:** Google AI Studio (`text-embedding-004`)
- **Vector DB:** Pinecone
- **Database Source:** Supabase (PostgreSQL) – dataset with 1M transactions
- **Cache:** Redis
- **Visualization:** Metabase
- **PDF Generation:** WeasyPrint
- **MCP Tools:** Custom Python server

### Infrastructure
- **Containerization:** Docker Compose
- **Auth:** Supabase Auth + JWT
- **Streaming:** Server‑Sent Events (SSE)

---

## System Architecture

    User Input (chat message)
    │
    ▼
    ┌─────────────────────────────────────────────────────────┐
    │                   FastAPI Backend                       │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │   Auth Middleware (Supabase JWT)                  │  │
    │  └───────────────────────────────────────────────────┘  │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │   LangGraph Orchestrator                          │  │
    │  │                                                   │  │
    │  │   Planner → RAG (Pinecone) → Cache Check          │  │
    │  │      ↓                                            │  │
    │  │   Query Generator → Validator → Optimizer         │  │
    │  │      ↓                                            │  │
    │  │   Query Executor (Supabase)                       │  │
    │  │      ↓                                            │  │
    │  │   Insight Analyzer (Groq LLM)                     │  │
    │  │      ↓                                            │  │
    │  │   Dashboard Builder (Metabase)                    │  │
    │  │      ↓                                            │  │
    │  │   Report Sender (Slack/Email/PDF)                 │  │
    │  └───────────────────────────────────────────────────┘  │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │   MCP Tools Server                                │  │
    │  │   fetch_data, send_slack, send_email,            │  │
    │  │   render_dashboard, export_pdf                    │  │
    │  └───────────────────────────────────────────────────┘  │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │   Redis Cache (query, LLM, embedding, dashboard)  │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
    │
    ▼
    Streaming Response (SSE) → React Frontend

---

## Dataset

**Source:** Supabase (PostgreSQL)  
**Scale:** 1,000,000 transactions + 1,000,000 fraud labels

| Table | Rows | Description |
| :--- | :--- | :--- |
| `users` | 1,219 | Customer profiles (age, income, credit score, etc.) |
| `cards` | 4,061 | Card details (brand, type, limit, dark web status) |
| `mcc_codes` | 109 | Merchant Category Codes (MCC) and descriptions |
| `transactions` | 1,000,000 | Card transactions (date, amount, merchant, city, MCC, errors) |
| `fraud_labels` | 1,000,000 | Fraud label per transaction (Yes / No) |

---

## Installation & Setup

### Prerequisites
- Docker & Docker Compose
- Supabase account (free tier)
- Pinecone account
- Groq API key
- Google AI Studio API key
- Slack webhook (optional)
- SMTP credentials (optional)

### 1. Clone the Repository

    git clone https://github.com/yourusername/BIthere.git
    cd BIthere

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and fill in all required values:

    SUPABASE_URL=your_supabase_url
    SUPABASE_ANON_KEY=your_supabase_anon_key
    SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
    PINECONE_API_KEY=your_pinecone_api_key
    PINECONE_ENVIRONMENT=your_pinecone_environment
    PINECONE_INDEX_NAME=bithere-metadata
    GROQ_API_KEY=your_groq_api_key
    GOOGLE_API_KEY=your_google_ai_studio_key
    REDIS_URL=redis://redis:6379/0
    METABASE_URL=http://metabase:3000
    METABASE_USERNAME=admin@example.com
    METABASE_PASSWORD=your_metabase_password
    JWT_SECRET=your_jwt_secret
    SMTP_HOST=smtp.example.com
    SMTP_PORT=587
    SMTP_USER=your_smtp_user
    SMTP_PASSWORD=your_smtp_password
    SLACK_WEBHOOK_URL=your_slack_webhook
    TEST_MODE=live

### 3. Setup Database Schema
Run `scripts/setup_supabase.sql` in Supabase SQL editor to create application tables (`profiles`, `query_history`, `dashboard_configs`, `business_glossary`, `ingestion_logs`).

### 4. Setup Pinecone Index
Create index:
- Name: `bithere-metadata`
- Dimensions: 768
- Metric: cosine

### 5. Run Metadata Ingestion

    python scripts/ingest_metadata.py

This reads the database schema and business glossary (`scripts/seed_glossary.csv`), generates embeddings using Google AI Studio, and upserts them to Pinecone.

### 6. Start Services with Docker Compose

    docker compose up --build

Services:
- Backend → http://localhost:8000
- Frontend → http://localhost:5173
- Redis → localhost:6379
- Metabase → http://localhost:3000

---

## Testing

All tests are placed in the `test/` directory and run against real external services (ensure API keys and rate limits are available).

    pytest test/                 # all tests
    pytest test/test_auth.py     # specific module
    pytest test/ -v -s           # verbose output

Test files:

| File | Focus |
| :--- | :--- |
| `test_auth.py` | Authentication & role |
| `test_query_generator.py` | NLQ to SQL |
| `test_validator.py` | SQL safety |
| `test_optimizer.py` | Query optimization |
| `test_rag_retrieval.py` | Pinecone metadata retrieval |
| `test_caching.py` | Redis cache |
| `test_dashboard.py` | Metabase dashboard creation |
| `test_report.py` | Report delivery |
| `test_chat_e2e.py` | End‑to‑end chat |
| `test_mcp_tools.py` | MCP tools |

---

## Implementation Roadmap

| Phase | Description | Status |
| :--- | :--- | :--- |
| 1 | Preparation & Foundation | Completed |
| 2 | Backend Core | In Progress |
| 3 | RAG & Embedding | Not Started |
| 4 | Agent Orchestration (LangGraph) | Not Started |
| 5 | MCP Server & Tools | Not Started |
| 6 | API Routes | Not Started |
| 7 | Frontend (React + Vite) | Not Started |
| 8 | Integration End‑to‑End | Not Started |
| 9 | Testing | Not Started |
| 10 | Finalization & Documentation | Not Started |

---

## Contributing

Contributions are welcome! To contribute:
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

---

## License

Distributed under the MIT License. See `LICENSE` for more information.

---

*Developed by Adi Kusuma*