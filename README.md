# 🚀 BIthere
**AI Business Intelligence Analyst**  
*Natural Language Query · Auto-Dashboard · Actionable Insights · Multi-Agent Orchestration · Big Data Optimization*

---

## 📖 Project Description

**BIthere** adalah platform analisis data berbasis kecerdasan buatan yang memungkinkan pengguna non-teknis untuk berinteraksi dengan database menggunakan **bahasa alami** (Indonesia/Inggris). Sistem ini tidak hanya menjawab pertanyaan, tetapi juga secara otomatis menghasilkan dashboard interaktif, memberikan rekomendasi aksi bisnis, serta dioptimalkan untuk performa tinggi melalui arsitektur *multi-agent* dan strategi *caching* cerdas.

### 🎯 Tujuan & Keunggulan Utama

- **Natural Language Query (NLQ)**  
  Pengguna cukup bertanya seperti *"Berapa total penjualan per kategori bulan lalu?"* atau *"Tunjukkan tren stok barang yang hampir habis di gudang Jakarta"*. Sistem menerjemahkan pertanyaan tersebut menjadi query SQL tanpa intervensi manual.

- **Dynamic Database Connector**  
  Mendukung berbagai sumber data (PostgreSQL, MySQL, MongoDB) melalui *abstraction layer* yang memungkinkan penambahan konektor baru tanpa mengubah logika inti aplikasi.

- **Multi-Agent Orchestration (LangChain/LangGraph)**  
  Sistem mengadopsi paradigma *agentic AI* di mana beberapa agen cerdas berkolaborasi secara sinkron:
  - **Planner Agent** → Menganalisis maksud pertanyaan dan memecahnya menjadi subtask.
  - **Query Generator Agent** → Menghasilkan query SQL sesuai skema database.
  - **Validator Agent** → Memeriksa keamanan dan sintaks query.
  - **Query Optimizer Agent** → Menulis ulang query untuk efisiensi (index, partisi, agregasi).
  - **Insight Analyzer Agent** → Merangkum hasil data menjadi insight bisnis yang strategis.
  - **Dashboard Builder Agent** → Membuat konfigurasi dashboard (JSON) dan terintegrasi dengan Metabase API.
  - **Report Sender Agent** → Mengirim laporan/insight ke Slack atau Email melalui MCP tools.

- **RAG (Retrieval-Augmented Generation) untuk Metadata & Business Glossary**  
  Memanfaatkan **Pinecone** (vector DB cloud) untuk menyimpan embedding dari skema tabel, deskripsi kolom, query historis, dan istilah bisnis. Proses *hybrid retrieval* (semantic + keyword) memastikan konteks yang paling relevan selalu tersedia sebelum query di-generate, meningkatkan akurasi NLQ secara signifikan. Embedding menggunakan **OpenAI text-embedding-3-small** yang murah dan cepat.

- **Auto-Dashboard dengan Metabase**  
  Dashboard Builder Agent secara otomatis menghasilkan visualisasi (chart, filter, layout) dalam format JSON dan memanggil Metabase API untuk membuat dashboard/card secara instan. Frontend menampilkannya melalui embed URL/iframe, dengan adapter yang memungkinkan migrasi ke Apache Superset atau ECharts tanpa mengubah logika inti.

- **Optimasi Token & Embedding**  
  Menggunakan model embedding efisien (text-embedding-3-small) dan menerapkan *token reduction* melalui output JSON terstruktur, *prompt compression*, dan *chunking* metadata yang efisien.

### ⚡ Optimasi Performa & Caching (Nilai Tambah Utama)

Sistem ini dirancang untuk respons cepat dengan strategi caching komprehensif:

- **Query Result Cache** → Menyimpan hasil query ke Redis dengan key berbasis hash dari prompt, parameter, dan versi skema.
- **Embedding & LLM Response Cache** → Menghindari pemanggilan API embedding/LLM berulang untuk pertanyaan identik (*semantic cache*).
- **Dashboard Config Cache** → Menyimpan konfigurasi JSON dashboard yang sudah dibuat untuk mencegah regenerasi.
- **Metadata Cache** → Menyimpan skema dan business glossary di Redis untuk akses cepat.

### 🔌 MCP Server & Integrasi Eksternal

Menyediakan *tools* standar seperti `fetch_data`, `send_slack`, `send_email`, `render_dashboard`, dan `export_pdf` yang memungkinkan agen memanggil layanan eksternal secara aman dan terkontrol.

---

## 🏗️ System Architecture & Deployment

Proyek ini menerapkan arsitektur **hybrid** (lokal + cloud) yang ringan dan hemat biaya. Komponen berat (LLM, embedding, vector DB) menggunakan layanan cloud dengan free tier, sementara komponen pendukung berjalan di Docker lokal.

### Tabel Komponen Teknologi

| Komponen | Teknologi | Keterangan |
|----------|-----------|-------------|
| **LLM Chat** | Groq API (Llama 3.3 70B) | Free tier, streaming cepat, latensi rendah |
| **Embedding** | OpenAI text-embedding-3-small | API murah, akurasi tinggi |
| **Vector DB** | Pinecone | Cloud, tanpa beban lokal, skalabel |
| **Database Sumber** | Supabase (PostgreSQL) | Cloud, 100rb baris (MVP) |
| **Cache** | Redis | Docker lokal, ringan (~100MB) |
| **Backend** | FastAPI + LangGraph | Docker lokal, logika agent dan orchestration |
| **Frontend** | React + Vite | Docker lokal, antarmuka chat & dashboard |
| **Visualisasi** | Metabase | Docker lokal, terhubung ke Supabase via connection string |
| **PDF Report** | WeasyPrint | Konversi HTML → PDF untuk laporan |
| **MCP Tools** | Custom tool server (Python) | fetch_data, send_slack, send_email, render_dashboard, export_pdf |
| **Auth** | JWT sederhana | Single user (MVP) |
| **Streaming** | SSE (Server-Sent Events) | Chat streaming real-time |
| **Deployment** | Docker Compose | Backend, frontend, Redis, Metabase |

> **Catatan Biaya:** Groq, Pinecone, dan OpenAI menyediakan free tier yang cukup untuk MVP. Biaya operasional sangat rendah, bahkan mendekati nol untuk penggunaan development dan demo.

Dengan arsitektur ini, beban komputasi berat (LLM inference, embedding, vector search) sepenuhnya ditangani oleh layanan cloud, sementara komponen ringan dan caching berjalan di lokal. Hal ini memungkinkan pengembangan cepat, deployment fleksibel, dan biaya infrastruktur minimal.

---

### 🧠 Alur Kerja Singkat (End-to-End)

1. **Pengguna** mengetik pertanyaan di chat (frontend React).
2. **Planner Agent** (backend FastAPI + LangGraph) menganalisis maksud dan kebutuhan visualisasi.
3. **RAG** mencari metadata relevan di Pinecone (vektor embedding dari OpenAI).
4. Sistem mengecek **cache Redis** (Query, Embedding, Dashboard Config) untuk menghindari komputasi ulang.
5. Jika tidak ada cache, **Query Generator** membuat SQL → **Validator** memeriksa keamanan → **Optimizer** menulis ulang untuk performa.
6. Data dieksekusi dari **Supabase** (PostgreSQL) dan hasilnya dikembalikan.
7. **Insight Analyzer** merangkum hasil menjadi insight bisnis (dengan bantuan Groq LLM).
8. **Dashboard Builder** membuat/ mengambil dashboard dari cache dan berinteraksi dengan **Metabase API**.
9. Jika diminta, **Report Sender** mengirim laporan ke Slack/Email (atau export PDF via WeasyPrint).
10. Jawaban dan dashboard ditampilkan secara **streaming real-time** ke pengguna melalui SSE.

---

### 🛠️ Tech Stack Ringkasan

| Kategori | Teknologi |
|----------|-----------|
| **LLM** | Groq (Llama 3.3 70B) |
| **Embedding** | OpenAI text-embedding-3-small |
| **Vector DB** | Pinecone |
| **Database** | Supabase (PostgreSQL) |
| **Cache** | Redis |
| **Backend** | FastAPI + LangGraph |
| **Frontend** | React + Vite |
| **Visualisasi** | Metabase |
| **PDF Generator** | WeasyPrint |
| **MCP Tools** | Custom Python Server |
| **Auth** | JWT |
| **Streaming** | SSE |
| **Deployment** | Docker Compose |


bithere/
├── backend/
│   ├── app/
│   │   ├── agents/               # LangGraph agents
│   │   ├── api/                  # FastAPI routes
│   │   ├── connectors/           # Database connectors (PostgreSQL, MySQL, MongoDB)
│   │   ├── core/                 # Config, logging, auth
│   │   ├── mcp/                  # MCP tool server
│   │   ├── rag/                  # RAG pipeline, embedding, Pinecone client
│   │   ├── services/             # Cache (Redis), Metabase adapter, report generator
│   │   └── main.py               # FastAPI entry point
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/           # Chat, Dashboard, Login
│   │   ├── pages/
│   │   ├── services/             # API calls, SSE stream
│   │   └── App.jsx
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml            # Backend, frontend, Redis, Metabase
├── .env.example                  # Template environment variable
├── README.md
└── scripts/                      # Seed data, setup Pinecone, setup Metabase

---

> **📌 Catatan:** Bagian ini adalah **Deskripsi Project** dan **Arsitektur Deployment** berdasarkan komponen terbaru. Untuk bagian selanjutnya (Panduan Instalasi, Konfigurasi Environment, Struktur Folder, dan Cara Menjalankan) akan menyusul di update README berikutnya.