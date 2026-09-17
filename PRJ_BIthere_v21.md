Multi-Tenant AI Business Intelligence Platform
Self-Service Onboarding · Bring-Your-Own-Keys · Bring-Your-Own-Data · Multi-Database Support · Self-Service RAG

📖 Project Description
BIthere v2 adalah evolusi dari platform analisis data berbasis AI BIthere v1 yang sudah berjalan (NLQ → SQL → Dashboard → Report). Jika v1 dirancang untuk single-user dengan konfigurasi hardcoded via .env, maka v2 dirancang untuk multi-tenant, corporate-ready, dan self-service.

Visi utama: "Clone → Configure → Upload → Query." — Empat langkah, tanpa developer.

Pengguna baru (individu, tim analis, atau klien korporat) cukup membawa API key sendiri, upload dataset sendiri, dan mendefinisikan knowledge base sendiri melalui Setup Wizard 6 langkah. Sistem langsung siap dipakai tanpa menyentuh kode atau file .env.

🎯 Tujuan & Keunggulan Utama
Self-Service Onboarding (Setup Wizard 6 Langkah)
User baru login → dibimbing melalui wizard: (1) Account & Workspace, (2) API Keys, (3) Data Source, (4) Dataset Upload, (5) Schema Builder, (6) RAG Configuration. Setelah selesai, workspace langsung siap — tanpa restart Docker, tanpa edit .env.

Bring-Your-Own-Keys (Encrypted Vault)
Setiap workspace menyimpan API key masing-masing (Groq, OpenAI, Pinecone, Metabase, Slack, Email) secara terenkripsi (Fernet) di database aplikasi. Tidak ada lagi API key global di .env. Setiap key bisa di-test, di-rotate, dan dimonitor kapan terakhir dipakai.

Dynamic Data Source Connector (Multi-Database)
Abstraction layer diperluas mendukung PostgreSQL, MySQL/MariaDB, MongoDB, SQLite, dan DuckDB. Penambahan connector baru tidak mengubah logika inti agent. Connector factory memilih driver berdasarkan tipe DB yang dipilih user.

Dataset Upload (Bring-Your-Own-Data)
User dapat meng-upload file CSV / Excel / Parquet (drag & drop), melihat preview 100 baris, mengedit tipe kolom, dan memilih target: DuckDB lokal (analitik cepat) atau push ke Supabase workspace. Untuk dataset besar / real-time, user bisa connect ke database existing mereka.

Schema Builder (DDL Generation & Review)
Sistem auto-generate DDL (CREATE TABLE) dari sampel data, termasuk deteksi primary key, foreign key, index suggestion, dan partition suggestion untuk tabel besar. User bisa review & edit DDL di Monaco Editor sebelum Apply. Ini memastikan pembuatan tabel diperhatikan, bukan hanya insert data.

RAG Self-Service (Knowledge Base)
User bisa membuat RAG mereka sendiri melalui 3 sumber metadata: (1) Schema metadata (auto-generate dari Schema Builder), (2) Business Glossary (upload CSV atau isi form manual), (3) Query History (auto dari query sukses). Semua metadata di-embed ke namespace Pinecone per workspace (workspace_{id}), menjamin isolasi data antar tenant.

Multi-Tenant Isolation
Isolasi penuh per workspace di setiap layer: JWT claim (workspace_id), Row-Level Security (RLS) di database aplikasi, namespace Pinecone terpisah, Redis key prefix (ws:{workspace_id}:), folder upload terpisah, dan audit log per workspace.

Workspace & Role Management
Multi-user per workspace dengan role: owner / admin / analyst / viewer. Admin bisa invite user via email, mengelola role, melihat usage stats, dan menelusuri audit logs.

Rate Limit Handler & Cost Tracking
Setiap panggilan ke layanan eksternal (Groq, OpenAI, Pinecone) melewati queue + exponential backoff (tenacity). Ketika rate limit tercapai, user melihat pesan jelas ("Layanan AI sedang sibuk, coba lagi dalam beberapa detik") dan sistem tidak crash. Usage token & biaya estimasi dicatat per workspace.

⚡ New Feature
ID	Fitur	Deskripsi	Prioritas
F-01	Setup Wizard	Onboarding 6 langkah self-service	P0
F-02	Integration Manager	Input, test, rotate API key per layanan	P0
F-03	Dynamic Data Source	PostgreSQL, MySQL, MongoDB, SQLite, DuckDB	P0
F-04	Dataset Upload	CSV/Excel/Parquet dengan preview & type editor	P0
F-05	Schema Builder	Generate DDL, edit, apply, rollback	P0
F-06	Knowledge Base (RAG)	Kelola schema, glossary, query history	P1
F-07	Workspace Management	Multi-user, role, invite, audit	P0
F-08	Usage & Audit	Log aktivitas + statistik + biaya	P2
F-09	Encrypted Vault	Simpan secret aman (Fernet)	P0
F-10	Multi-Tenant Isolation	RLS + namespace + Redis prefix	P0
F-11	Rate Limit Handler	Backoff + queue + info ke user	P2
F-12	Billing (Opsional)	Plan free/pro/enterprise	P3
Tabel Komponen Teknologi New Feature
Komponen	Teknologi	Keterangan
Secret Vault	Fernet (cryptography)	Enkripsi API key per workspace, master key di env server
Connector Factory	asyncpg, aiomysql, motor, aiosqlite, duckdb	Multi-database support
File Upload	FastAPI UploadFile + pandas + openpyxl	CSV, Excel, Parquet (via pyarrow)
Analytics Engine (upload)	DuckDB	Query cepat untuk dataset upload < 10 juta baris
DDL Generator	SQLAlchemy Core + custom inference	Auto-generate CREATE TABLE dari sampel
DDL Editor UI	Monaco Editor	Syntax highlight SQL
ERD Viewer	Mermaid.js / Reactflow	Diagram relasi antar tabel
Encryption at Rest	Fernet symmetric + MASTER_ENCRYPTION_KEY	Semua secret di DB aplikasi
Multi-Tenant RLS	Supabase Row-Level Security	Policy workspace_id = auth.jwt()->>'workspace_id'
Pinecone Namespace	Pinecone namespaces	workspace_{uuid}/schema, /glossary, /query_history
Redis Prefix	redis.asyncio + key prefix	ws:{workspace_id}:query:{hash}
File Storage	MinIO (opsional, S3-compatible)	Untuk dataset upload besar
Rate Limiter	tenacity + asyncio.Semaphore	Retry dengan exponential backoff
Usage Metering	Custom counter di Redis + tabel usage_events	Token, request, biaya estimasi per workspace
Audit Log	PostgreSQL audit_logs	Filter by user, action, tanggal
Wizard State	Zustand + persist ke workspaces.setup_progress	Resume kapan saja
🧠 Alur Kerja Singkat (End-to-End)
Registrasi — User baru mendaftar via Supabase Auth, sistem membuat workspace default.

Setup Wizard — User melewati 6 langkah: account, API keys, data source, upload dataset, schema builder, RAG config.

Upload Dataset — User drag & drop CSV/Excel → sistem sniff delimiter, preview 100 baris, deteksi tipe kolom.

Schema Builder — Sistem generate DDL → user review/edit → klik Apply Schema → tabel terbuat, data ter-insert.

RAG Ingest (auto) — Sistem auto-embed schema metadata → upsert ke Pinecone namespace workspace_{id}/schema.

Upload Glossary — User upload glossary.csv atau isi form manual → sistem embed → upsert ke workspace_{id}/glossary.

Chat NLQ — User mengetik pertanyaan → Planner Agent → RAG retrieval (dari namespace workspace) → cache check.

Query Pipeline — Query Generator → Validator → Optimizer → Executor (via connector yang dipilih user).

Insight & Dashboard — Insight Analyzer (Groq LLM dengan API key user) → Dashboard Builder (Metabase user).

Report & Audit — Report Sender (Slack/Email user) → semua aktivitas dicatat di audit_logs per workspace.

Streaming Response — Jawaban + dashboard di-stream via SSE ke frontend.

🛠️ Tech Stack Ringkasan
Kategori	Teknologi
LLM	Groq (Llama 3.3 70B) — API key per workspace
Embedding	OpenAI text-embedding-3-small — API key per workspace
Vector DB	Pinecone — namespace per workspace
Database Sumber	PostgreSQL / MySQL / MongoDB / SQLite / DuckDB (user choice)
Database Aplikasi	Supabase (PostgreSQL) + RLS multi-tenant
Cache	Redis (dengan prefix workspace)
Secret Vault	Fernet (symmetric encryption)
Backend	FastAPI + LangGraph
Frontend	React + Vite + Zustand
Visualisasi	Metabase (per workspace)
PDF Generator	WeasyPrint
MCP Tools	Custom Python Server
Auth	Supabase Auth + JWT (workspace claim)
Streaming	SSE
File Upload	FastAPI + pandas + DuckDB
DDL Editor	Monaco Editor + ERD viewer
Rate Limiter	tenacity + asyncio.Semaphore
Deployment	Docker Compose (+ MinIO opsional)
Struktur Folder v2
text
bithere/
├── backend/
│   ├── app/
│   │   ├── agents/               # LangGraph agents (Planner, Generator, Validator, dll.)
│   │   ├── api/                  # FastAPI routes (auth, chat, dashboard, report, users)
│   │   ├── connectors/           # Database connectors (Postgres, MySQL, Mongo, SQLite, DuckDB)
│   │   ├── core/                 # Config, logging, auth, encryption
│   │   ├── mcp/                  # MCP tool server
│   │   ├── rag/                  # RAG pipeline, embedding, Pinecone client
│   │   ├── services/             # Cache, Metabase adapter, report generator
│   │   ├── workspace/            # NEW: Workspace, Secrets, Datasets, Schema Builder
│   │   └── main.py               # FastAPI entry point
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/           # Chat, Dashboard, Login, Wizard, Integration cards
│   │   ├── pages/                # Setup Wizard, Integrations, Datasets, Schema Builder,
│   │   │                         # Knowledge Base, Chat, Dashboard, Admin
│   │   ├── services/             # API calls, SSE stream
│   │   ├── store/                # Zustand (authStore, workspaceStore, chatStore)
│   │   └── App.jsx
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml            # Backend, frontend, Redis, Metabase, (MinIO opsional)
├── .env.example                  # Template environment variable (platform-level)
├── README.md
└── scripts/                      # Seed data, setup Pinecone, setup Metabase,
                                  # migrations (workspace tables)
6. Kebutuhan Fungsional
6.1 Fungsional v1 (Dipertahankan)
ID	Kebutuhan	Deskripsi
FR-01	Natural Language Query	User bertanya dengan bahasa alami → sistem generate SQL → eksekusi → insight
FR-02	Auto-Dashboard	Sistem generate dashboard Metabase dari hasil query
FR-03	Actionable Insight	Setiap hasil diringkas jadi insight bisnis (executive summary + key findings + recommended actions)
FR-04	Report Delivery	Kirim laporan via Email, Slack, atau PDF
FR-05	Multi-Agent Orchestration	Planner, Generator, Validator, Optimizer, Analyzer, Builder, Sender
FR-06	Authentication & RBAC	Login via Supabase, role admin/analyst
FR-07	Audit Trail	Semua query & aksi tercatat
6.2 Fungsional v2 (Baru)
ID	Kebutuhan	Deskripsi	Prioritas
FR-08	Workspace CRUD	User dapat membuat, memilih, dan mengganti workspace	P0
FR-09	Setup Wizard	Onboarding 6 langkah dengan progress persistence	P0
FR-10	Integration Manager	Input, test, rotate API key per layanan per workspace	P0
FR-11	Dynamic Data Source	User pilih tipe DB (Postgres/MySQL/Mongo/SQLite/DuckDB) + connection string	P0
FR-12	Dataset Upload	Upload CSV/Excel/Parquet + preview + edit tipe kolom	P0
FR-13	Schema Builder	Auto-generate DDL → review/edit di Monaco → Apply/Rollback	P0
FR-14	Glossary CRUD	Kelola istilah bisnis via form atau upload CSV	P1
FR-15	Auto RAG Ingest	Auto-embed schema & glossary ke Pinecone namespace workspace	P0
FR-16	Re-ingest Metadata	Tombol rebuild namespace Pinecone	P1
FR-17	Multi-User Workspace	Invite user, atur role (owner/admin/analyst/viewer)	P0
FR-18	Usage Metering	Catat token, request, biaya estimasi per workspace	P2
FR-19	Rate Limit Handling	Backoff + queue, info ke user saat limit tercapai	P2
FR-20	Auto-Enrichment Glossary	Sistem sarankan istilah baru dari query history	P3
7. Kebutuhan Non-Fungsional (Non-Functional Requirements)
7.1 Performa (Performance)
NFR-01: Latensi Chat Streaming
Parameter	Target	Metrik Pengukuran
Time to First Token (TTFT)	< 2 detik	Waktu dari user mengetik prompt hingga token pertama muncul di chat.
Alasan:

Standar UX percakapan AI: user tidak mau menunggu lebih dari 2 detik untuk melihat respons pertama.

Groq Llama 3.3 70B sangat cepat (inference < 1 detik untuk token pertama), sehingga target 2 detik realistis.

Di v2, TTFT harus tetap terjaga meski ada overhead tambahan: workspace context resolution + decrypt API key + namespace-scoped Pinecone query.

NFR-02: Latensi Query
Jenis Query	Target (tanpa cache)	Target (dengan cache)	Catatan
Query sederhana (1 tabel, filter index)	< 3 detik	< 1 detik	SELECT dengan WHERE pada kolom terindeks
Query kompleks (join 2–3 tabel, agregasi)	< 10 detik	< 1 detik	Butuh index, partisi, atau materialized view
Alasan:

Dengan cache: Redis lokal, akses < 10 ms. 1 detik sudah longgar.

Tanpa cache: Query analitik di PostgreSQL 1 juta baris dengan index baik biasanya < 1 detik di cloud.

v2: Query pada DuckDB lokal (hasil upload) umumnya lebih cepat karena data co-located dengan compute.

NFR-03: Latensi Onboarding
Parameter	Target	Metrik
Time to First Query (TTFQ)	< 15 menit	Waktu dari registrasi hingga user bisa query pertama
Upload + Schema Apply	< 3 menit untuk file 100 MB	Termasuk sniff, preview, DDL generate, insert
Alasan:

Onboarding adalah titik kritis untuk user friendliness. Jika > 15 menit, user cenderung drop-off.

Untuk file 100 MB dengan ~500k baris, batch insert + DuckDB columnar format harusnya < 3 menit.

NFR-04: Throughput (Konkurensi)
Parameter	Target	Metrik
Concurrent Users per Instance	Minimal 10 request bersamaan tanpa degradasi	Request per detik sebelum latensi > 2x
Concurrent Workspaces	50 workspace aktif	Workspace dengan aktivitas query per hari
Alasan:

MVP dijalankan lokal/docker. 10 concurrent user cukup untuk demo tim.

50 workspace aktif menargetkan penggunaan corporate skala kecil-menengah.

7.2 Skalabilitas (Scalability)
NFR-05: Arsitektur Modular & Horizontal Scaling
Parameter	Deskripsi
Modularitas	Setiap komponen (backend, Redis, Metabase, MinIO) dapat di-scale horizontal
Stateless Backend	Backend stateless (kecuali session di Redis), memungkinkan multi-instance
Namespace Isolation	Workspace baru tidak memerlukan deploy baru, cukup namespace Pinecone + RLS
Alasan:

Komponen berat (LLM, embedding, vector DB) di cloud, komponen lokal bisa ditambah instance.

Namespace-based isolation memungkinkan penambahan tenant tanpa migrasi infrastruktur.

7.3 Keamanan (Security)
NFR-06: Keamanan Query
Parameter	Deskripsi
SQL Injection Prevention	Validator Agent memastikan query aman dari SQL Injection
Operasi Destruktif	Block DROP, DELETE tanpa WHERE, TRUNCATE
Allowlist Operasi	Hanya SELECT yang diizinkan dari NLQ
Per-Workspace Isolation	User workspace A tidak bisa query DB workspace B
Alasan:

NLQ berbahaya karena user bisa tidak sengaja meminta query destruktif.

Isolasi workspace adalah syarat mutlak untuk corporate.

NFR-07: Keamanan API Key (Encrypted Vault)
Parameter	Deskripsi
Enkripsi at Rest	Fernet symmetric encryption dengan MASTER_ENCRYPTION_KEY
Tidak Pernah Dikirim ke Frontend	Frontend hanya lihat masked value (sk-****1234)
Audit Log	Setiap update API key tercatat di audit_logs
Rotasi	User bisa rotate key tanpa downtime
Fallback (opsional)	Jika workspace tidak set key, fallback ke key platform (untuk demo)
Alasan:

Multi-tenant berarti banyak API key di satu DB — harus dienkripsi.

Frontend tidak boleh pernah lihat raw key (XSS mitigation).

NFR-08: Isolasi Multi-Tenant
Layer	Strategi
JWT Claim	workspace_id di custom claim Supabase
Application DB (RLS)	Policy workspace_id = auth.jwt()->>'workspace_id'
Source DB	Connection string per workspace (user bawa sendiri)
Pinecone	Namespace workspace_{uuid}
Redis	Key prefix ws:{workspace_id}:
File Storage	Folder uploads/{workspace_id}/
Logs	Setiap log menyertakan workspace_id
Alasan:

Kebocoran data antar tenant = kegagalan fatal untuk produk corporate.

Defense-in-depth: isolation di setiap layer.

7.4 Caching & Optimasi
NFR-09: Caching
Parameter	Deskripsi
Query Result Cache	Redis, TTL 1 jam, key ws:{id}:query:{hash}
LLM Response Cache	Semantic cache untuk pertanyaan identik/mirip
Embedding Cache	Cache embedding metadata, TTL 24 jam
Dashboard Config Cache	TTL 1 jam
Metadata Cache	TTL 6 jam
Invalidasi Otomatis	Hapus saat skema workspace berubah
Alasan:

Tujuan utama project: optimasi performa & biaya.

Prefix workspace menjamin cache tidak tercampur antar tenant.

TTL mencegah cache basi.

NFR-10: Optimasi Token
Parameter	Deskripsi
Prompt Compression	Kurangi konteks tidak relevan sebelum kirim ke LLM
Output JSON Terstruktur	Struktur mengurangi token tidak perlu
Chunking Metadata	Chunk efisien agar tidak overload
Alasan:

Token = biaya & latensi. Semakin sedikit token, semakin cepat & murah.

Penting di v2 karena user bayar API key sendiri — mereka sensitif terhadap biaya.

NFR-11: Optimasi Embedding
Parameter	Deskripsi
Model Embedding	OpenAI text-embedding-3-small (efisien, murah, cepat)
Caching	Embedding di-cache di Redis
Batching	Batch embedding saat ingest
Namespace per Workspace	Isolasi + memudahkan delete/rebuild
Alasan:

Model small = murah + cepat + hemat storage Pinecone (dimensi 1536).

Untuk metadata pendek & terstruktur, akurasi model small sudah cukup.

7.5 Observability & Error Handling
NFR-12: Observability (Logging)
Parameter	Deskripsi
Format Log	[PROCESS], [INFO], [SUCCESS], [WARNING], [ERROR]
Struktur Log	JSON, menyertakan workspace_id, user_id, request_id
Cakupan	Setiap request, error, agent call, MCP tool call
Dilarang	Emoji di dalam log
Alasan:

Di multi-tenant, debugging tanpa workspace_id = mustahil.

Log JSON mudah diparsing oleh tools (ELK, Loki).

NFR-13: Error Handling
Parameter	Deskripsi
User-Friendly Error	Bahasa jelas, tanpa stack trace mentah
Retry Mechanism	Retry untuk API eksternal (Groq, OpenAI, Pinecone)
Rate Limit Handling	Backoff + queue, pesan informatif
Graceful Degradation	Jika Metabase down, chat tetap bisa query
Alasan:

User bisnis tidak paham stack trace.

Rate limit free tier Groq/OpenAI sering tercapai → wajib handling.

7.6 Maintainability & Portability
NFR-14: Portability (Docker Compose)
Parameter	Deskripsi
Deployment	docker compose up --build
Konfigurasi	Cukup clone, isi .env platform-level, jalankan
Komponen	Backend, frontend, Redis, Metabase, (MinIO) dalam satu command
Alasan:

Evaluator / user non-teknis harus bisa menjalankan dengan mudah.

NFR-15: Maintainability (Clean Code)
Parameter	Deskripsi
Standar Kode	PEP8 (Python), Prettier (JS/JSX), ESLint, Ruff/Flake8
Modularitas	Setiap agent & setiap halaman frontend terpisah
Self-Documenting	Nama fungsi & variabel menjelaskan tujuan
Single Responsibility	Satu fungsi/class satu tugas
Function Length	Idealnya ≤ 20–30 baris
Alasan:

Portofolio harus mudah dibaca orang lain.

Modularitas memudahkan penambahan connector/agent/halaman baru.

NFR-16: Kompatibilitas Database
Parameter	Deskripsi
Dynamic Connector	PostgreSQL, MySQL, MongoDB, SQLite, DuckDB
Abstraction Layer	Penambahan connector baru tidak mengubah logika inti
Dialect Translation	Auto-translate SQL antar dialect (LIMIT, date functions)
Alasan:

Persyaratan corporate: klien punya DB berbeda-beda.

Dynamic connector = nilai jual utama v2.

7.7 Kepatuhan Rate Limit
NFR-17: Kepatuhan Rate Limit Layanan Eksternal
Parameter	Deskripsi
Retry Strategy	tenacity dengan exponential backoff
Concurrency Cap	asyncio.Semaphore (maks 5 concurrent per layanan)
User Feedback	Pesan jelas: "Layanan AI sedang sibuk, coba lagi dalam beberapa detik"
Cache Priority	Cache tetap aktif → meminimalkan panggilan API
Per-Workspace Isolation	Rate limit workspace A tidak menghambat workspace B
Alasan:

Groq, OpenAI, Pinecone free tier punya RPM & TPM limit.

Tanpa penanganan, request gagal tiba-tiba, UX buruk, error tidak jelas.

Di multi-tenant, satu workspace "berisik" tidak boleh mengganggu yang lain.

📊 Ringkasan NFR
ID	NFR	Target Utama
NFR-01	Latensi Chat Streaming	< 2 detik (TTFT)
NFR-02	Latensi Query	< 3 detik (sederhana) / < 10 detik (kompleks)
NFR-03	Latensi Onboarding	TTFQ < 15 menit
NFR-04	Throughput	10 concurrent users / 50 workspaces
NFR-05	Skalabilitas	Modular, horizontal scaling, namespace isolation
NFR-06	Keamanan Query	SQL Injection prevention, SELECT only
NFR-07	Keamanan API Key	Fernet encryption, audit, rotate
NFR-08	Isolasi Multi-Tenant	RLS + namespace + Redis prefix
NFR-09	Caching	Redis, TTL, invalidasi otomatis, per workspace
NFR-10	Optimasi Token	Prompt compression, output JSON
NFR-11	Optimasi Embedding	text-embedding-3-small, cache, batch
NFR-12	Observability	Logging terstruktur (JSON + workspace_id)
NFR-13	Error Handling	User-friendly, retry, graceful degradation
NFR-14	Portability	Docker Compose
NFR-15	Maintainability	Clean Code, modular
NFR-16	Kompatibilitas Database	5 jenis DB via connector factory
NFR-17	Rate Limit	Backoff + queue + user feedback
8. Manajemen State atau Alur Logika (State Management / Logic Flow)
Bagian ini menjelaskan bagaimana state/status dikelola di seluruh sistem, dari percakapan, alur agent, cache, workspace context, hingga frontend.

8.1 Session Persistence (Redis + Supabase)
Aspek	Penyimpanan	Alasan
Sesi aktif (percakapan, state LangGraph)	Redis (key ws:{id}:session:{sid})	Cepat, TTL, data sementara
Riwayat permanen (query_history, hasil analisis)	Supabase (RLS per workspace)	Audit, auto-enrichment, analisis historis
Workspace context	Redis cache + DB lookup	Hindari query DB tiap request
Alur Session ID:

Session ID (UUID) dibuat di frontend saat user mulai chat pertama kali.

State agent disimpan di Redis dengan TTL 1 jam (diperpanjang jika aktif).

Setelah percakapan selesai, ringkasan/query final disimpan ke Supabase query_history.

8.2 Workspace Context Resolution
Setiap request ke backend melewati middleware workspace context:

Langkah	Proses
1	Verifikasi JWT Supabase
2	Ekstrak workspace_id dari custom claim
3	Load workspace metadata (cache Redis → fallback DB)
4	Decrypt API key yang diperlukan dari vault
5	Set context: connector aktif, Pinecone namespace, Redis prefix
6	Teruskan ke endpoint handler
8.3 LangGraph State (Redis Checkpoint)
Aturan	Deskripsi
Checkpointer	LangGraph simpan state di Redis dengan prefix workspace
State Update	Setiap langkah agent menulis state terbaru
Resume	Server restart → lanjut dari checkpoint terakhir
TTL	1 jam
State berisi:

text
prompt, session_id, workspace_id,
metadata_context, generated_query, query_result,
insight, dashboard_config, final_response,
connector_type, dialect
8.4 Frontend State (Zustand + Local State)
Jenis State	Tools	Data yang Disimpan
Global State	Zustand	authStore (user, token), workspaceStore (activeWorkspace, integrations, datasets), chatStore (messages, isStreaming, sessionId), wizardStore (step, form data)
Local State	useState	Input form, toggle UI
Alasan pakai Zustand: ringan, mudah sinkronisasi antar komponen (chat bubble, dashboard panel, navbar) tanpa prop drilling.

Alur update streaming di frontend:

Langkah	Aksi
1	User kirim prompt → tambah pesan user ke messages
2	Set isStreaming = true
3	Buka koneksi SSE ke /api/chat (dengan workspace_id di header)
4	Event token → append ke pesan AI terakhir
5	Event dashboard → simpan embedUrl ke activeDashboardUrl
6	Event insight → tampilkan insight
7	Event error → tampilkan error, isStreaming = false
8	Stream selesai → isStreaming = false, simpan sesi ke Supabase
8.5 Alur Agent (Linear)
Langkah	Agent / Proses	Input	Output
0	Workspace Context (middleware)	JWT	workspace_id, connector, namespace, keys
1	Planner Agent	Prompt + session state	Maksud, kebutuhan visualisasi/aksi
2	RAG Retrieval	Maksud + workspace namespace	Konteks metadata relevan
3	Cache Check	Prompt + metadata	Cache hit/miss
4	Query Generator (jika miss)	Metadata + prompt + dialect	Query SQL/aggregation
5	Validator Agent	Query	Query aman atau tolak
6	Query Optimizer	Query tervalidasi	Query dioptimalkan
7	Query Executor	Query final + connector	Hasil data
8	Insight Analyzer	Hasil data + prompt	Insight teks
9	Dashboard Builder (jika diminta)	Hasil data + konfigurasi	Dashboard URL
10	Report Sender (jika diminta)	Insight + URL	Laporan terkirim
11	Response Builder	Semua output	Stream final + tulis cache
Catatan:

Jika cache hit di langkah 3, langkah 4–7 dilewati.

Setiap langkah menggunakan API key & koneksi dari workspace aktif.

8.6 Cache Flow
Titik pengecekan cache: setelah RAG Retrieval dan sebelum Query Generator.

Kondisi	Aksi
Cache hit penuh	Kirim langsung respons dari cache
Cache hit query result	Ambil hasil query, lanjut ke Insight Analyzer
Cache miss	Generate → execute → simpan query result + insight
Cache Keys (dengan prefix workspace):

Key Pattern	Isi
ws:{id}:query:{hash}	Hasil query
ws:{id}:llm:{hash}	Respons LLM
ws:{id}:embedding:{hash}	Embedding metadata
ws:{id}:dashboard:{id}	Konfigurasi dashboard
ws:{id}:session:{sid}	State percakapan aktif
Invalidasi Cache:

Mekanisme	Deskripsi
TTL Otomatis	1 jam untuk query/LLM, 24 jam untuk embedding
Manual	Saat skema workspace berubah → hapus ws:{id}:metadata:* dan ws:{id}:query:*
Workspace Delete	Hapus semua key dengan prefix ws:{id}:
8.7 Wizard State
Aspek	Implementasi
Progress	Disimpan di workspaces.setup_progress (JSONB)
Step Data	Disimpan sementara di Zustand + persist ke DB saat step selesai
Resume	User bisa logout & login lagi, wizard lanjut dari step terakhir
Skip	Step opsional (Slack, Email) bisa di-skip
9. Instruksi Eksekusi dan Pengujian (Setup & Testing Instructions)
9.1 Struktur Folder Test
text
test/
├── test_auth.py               # Autentikasi JWT & role
├── test_workspace.py          # NEW: Workspace CRUD & isolation
├── test_secrets.py            # NEW: Encrypted vault (Fernet)
├── test_connectors.py         # NEW: Postgres/MySQL/Mongo/SQLite/DuckDB
├── test_upload.py             # NEW: Dataset upload + type detection
├── test_schema_builder.py     # NEW: DDL generation + apply + rollback
├── test_rag_ingest.py         # NEW: Ingest schema & glossary ke Pinecone
├── test_query_generator.py    # NLQ → SQL
├── test_validator.py          # Keamanan query
├── test_optimizer.py          # Optimasi query
├── test_rag_retrieval.py      # Retrieval metadata Pinecone
├── test_caching.py            # Redis cache (dengan prefix workspace)
├── test_dashboard.py          # Pembuatan dashboard Metabase
├── test_report.py             # Kirim laporan PDF/Slack/Email
├── test_chat_e2e.py           # Alur chat end-to-end
├── test_mcp_tools.py          # MCP tools langsung
└── test_rate_limit.py         # NEW: Backoff & queue
9.2 Cara Menjalankan Test
Aktifkan environment — pastikan semua env variable platform-level di .env sudah terisi.

Jalankan semua test:

bash
pytest test/
Jalankan test spesifik:

bash
pytest test/test_workspace.py
Jalankan test dengan output detail:

bash
pytest test/ -v -s
Catatan:

Test akan memanggil API eksternal nyata. Pastikan kuota & rate limit tersedia.

Untuk test_chat_e2e.py, jalankan saat internet stabil.

Untuk test multi-tenant, gunakan fixture workspace terpisah.

9.3 Daftar Test (Fungsional)
File Test	Yang Diuji	Skenario Utama
test_auth.py	Register, login, me	Admin invite → user login → ambil profil
test_workspace.py	Workspace CRUD + isolation	Buat 2 workspace, cek data tidak bercampur
test_secrets.py	Encrypted vault	Simpan key → decrypt → cocok
test_connectors.py	5 connector	Test connection ke tiap DB
test_upload.py	Upload CSV/Excel	Sniff → preview → type detect
test_schema_builder.py	DDL generator	Generate → apply → rollback
test_rag_ingest.py	Ingest Pinecone	Embed schema + glossary → upsert
test_query_generator.py	NLQ ke SQL	Input pertanyaan → output SQL sesuai skema
test_validator.py	Keamanan query	Tolak DROP, DELETE tanpa WHERE; izinkan SELECT
test_optimizer.py	Optimasi query	Query kompleks dioptimalkan
test_rag_retrieval.py	RAG metadata	Ambil konteks relevan dari Pinecone
test_caching.py	Redis cache	Simpan & ambil, TTL, prefix workspace
test_dashboard.py	Metabase	Buat dashboard/card dari query result
test_report.py	Report delivery	Generate PDF & kirim ke Slack/Email
test_chat_e2e.py	Alur penuh	Prompt → streaming → jawaban + dashboard
test_mcp_tools.py	MCP tools	Panggil semua tools
test_rate_limit.py	Rate limit	Simulasi limit → backoff & pesan ke user
9.4 Pengujian Manual
Untuk fitur yang belum masuk test otomatis, gunakan langkah manual:

Registrasi → daftar akun baru → cek workspace default terbuat.

Setup Wizard → ikuti 6 langkah → pastikan bisa resume saat logout.

Integrations → input API key Groq/OpenAI/Pinecone → Test Connection → status hijau.

Upload Dataset → upload sample.csv → cek preview → apply schema.

Knowledge Base → upload glossary.csv → cek istilah masuk → Re-ingest.

Chat NLQ → tanyakan "Berapa total transaksi fraud bulan lalu?" → lihat streaming.

Dashboard → minta "Tampilkan dashboard fraud per bulan" → lihat embed Metabase.

Kirim laporan → minta kirim ke Slack/Email → cek terkirim.

Cache → ulangi pertanyaan sama → pastikan respons lebih cepat.

Multi-Tenant → buat workspace kedua → pastikan data & cache tidak bercampur.

📌 LANGKAH IMPLEMENTASI v2
Tandai setiap langkah yang sudah selesai dengan mengubah [ ] menjadi [x].

TAHAP 1: PERSIAPAN DAN FONDASI MULTI-TENANT
Tujuan: Menyiapkan struktur multi-tenant, environment, dan skema DB aplikasi v2.

Langkah 1.1 — Inisialisasi Repository dan Struktur Folder v2

□ Buat folder baru: backend/app/workspace/
□ Buat subfolder: workspace/secrets/, workspace/datasets/, workspace/schema_builder/
□ Buat folder frontend baru: frontend/src/pages/wizard/, integrations/, datasets/, schema-builder/, knowledge-base/
□ Update .gitignore (tambah uploads/, *.duckdb, master.key)
□ File yang dibuat: struktur folder baru, .gitignore diupdate
Langkah 1.2 — Menyiapkan Environment Variables Platform-Level (.env.example v2)

□ Update .env.example dengan variabel platform-level baru:
Variabel	Deskripsi
MASTER_ENCRYPTION_KEY	Kunci Fernet untuk enkripsi API key workspace (32-byte urlsafe base64)
UPLOAD_DIR	Folder upload dataset, default ./uploads
MAX_UPLOAD_SIZE_MB	Batas upload per file, default 500
DUCKDB_DIR	Folder DuckDB per workspace, default ./duckdb
MINIO_ENDPOINT	(Opsional) S3-compatible endpoint
MINIO_ACCESS_KEY	(Opsional)
MINIO_SECRET_KEY	(Opsional)
REDIS_WORKSPACE_PREFIX	Default ws:
RATE_LIMIT_MAX_CONCURRENT	Default 5
RATE_LIMIT_BACKOFF_MAX	Default 60 (detik)
□ Catatan: API key layanan (Groq, OpenAI, Pinecone) tidak lagi di .env — disimpan per workspace di DB.
□ File yang dibuat: .env.example (v2)
Langkah 1.3 — Setup Docker Compose v2 (Tambahan MinIO Opsional)

□ Update docker-compose.yml:
□ Service minio (opsional, untuk file storage besar)
□ Volume uploads/ dan duckdb/ untuk backend
□ File yang dibuat: docker-compose.yml (v2)
Langkah 1.4 — Migrasi Skema Database Aplikasi v2

□ Buat scripts/migrations/002_workspace_tables.sql:
□ Tabel workspaces
□ Tabel workspace_members
□ Tabel workspace_secrets
□ Tabel workspace_data_sources
□ Tabel workspace_datasets
□ Tabel workspace_schemas
□ Tabel audit_logs
□ Tabel usage_events
□ Aktifkan Row-Level Security (RLS) dengan policy workspace_id = auth.jwt()->>'workspace_id'
□ Buat index pada workspace_id, user_id, created_at
□ File yang dibuat: scripts/migrations/002_workspace_tables.sql
TAHAP 2: WORKSPACE CORE & ENCRYPTED VAULT
Tujuan: Membangun fondasi multi-tenant: workspace context, enkripsi secret, dan middleware.

Langkah 2.1 — Workspace Context Middleware

□ Buat app/workspace/context.py:
□ resolve_workspace(jwt) -> WorkspaceContext
□ WorkspaceContext berisi: workspace_id, connector, pinecone_namespace, redis_prefix, decrypted_keys
□ Cache di Redis (TTL 5 menit)
□ Daftarkan sebagai FastAPI dependency di api/deps.py
□ File yang dibuat: workspace/context.py, update api/deps.py
Langkah 2.2 — Encrypted Secret Vault

□ Buat app/core/encryption.py:
□ encrypt(plain: str) -> bytes (Fernet)
□ decrypt(cipher: bytes) -> str
□ Load MASTER_ENCRYPTION_KEY dari env
□ Buat app/workspace/secrets.py:
□ set_secret(workspace_id, service, value)
□ get_secret(workspace_id, service) -> str
□ list_secrets(workspace_id) -> List[masked]
□ rotate_secret(workspace_id, service, new_value)
□ File yang dibuat: core/encryption.py, workspace/secrets.py
Langkah 2.3 — Workspace CRUD Service

□ Buat app/workspace/service.py:
□ create_workspace(owner_id, name)
□ get_workspace(workspace_id)
□ list_user_workspaces(user_id)
□ add_member(workspace_id, user_id, role)
□ update_role(workspace_id, user_id, role)
□ remove_member(workspace_id, user_id)
□ File yang dibuat: workspace/service.py
Langkah 2.4 — Integration Manager Service

□ Buat app/workspace/integrations.py:
□ test_groq(key) -> bool
□ test_openai(key) -> bool
□ test_pinecone(key, index, env) -> bool
□ test_metabase(url, user, pass) -> bool
□ test_slack(webhook) -> bool
□ test_email(resend_key) -> bool
□ File yang dibuat: workspace/integrations.py
Langkah 2.5 — Audit Log Service

□ Buat app/workspace/audit.py:
□ log_action(workspace_id, user_id, action, detail)
□ Helper: log_api_key_update, log_dataset_upload, log_schema_apply
□ File yang dibuat: workspace/audit.py
TAHAP 3: DYNAMIC DATA SOURCE CONNECTOR
Tujuan: Memperluas connector v1 menjadi 5 tipe DB dengan factory pattern.

Langkah 3.1 — Perluas BaseConnector

□ Update app/connectors/base.py:
□ test_connection() -> bool
□ get_schema() -> List[TableSchema]
□ execute_query(query) -> QueryResult
□ get_dialect() -> str
□ supports_sql() -> bool
□ File yang dibuat: update connectors/base.py
Langkah 3.2 — Implementasi MySQLConnector

□ Buat app/connectors/mysql.py menggunakan aiomysql
□ Implement get_schema dari information_schema
□ File yang dibuat: connectors/mysql.py
Langkah 3.3 — Implementasi MongoDBConnector

□ Buat app/connectors/mongodb.py menggunakan motor
□ supports_sql() = False
□ execute_query menerima aggregation pipeline (JSON)
□ File yang dibuat: connectors/mongodb.py
Langkah 3.4 — Implementasi SQLiteConnector

□ Buat app/connectors/sqlite.py menggunakan aiosqlite
□ File yang dibuat: connectors/sqlite.py
Langkah 3.5 — Implementasi DuckDBConnector

□ Buat app/connectors/duckdb.py
□ DuckDB file per workspace: duckdb/{workspace_id}.duckdb
□ File yang dibuat: connectors/duckdb.py
Langkah 3.6 — Connector Factory

□ Update app/connectors/__init__.py:
□ get_connector(workspace_id, data_source_id) -> BaseConnector
□ Cache connector instance di Redis (TTL 5 menit)
□ File yang dibuat: update connectors/__init__.py
Langkah 3.7 — Data Source Registry Service

□ Buat app/workspace/data_sources.py:
□ add_data_source(workspace_id, name, type, connection)
□ list_data_sources(workspace_id)
□ set_default(workspace_id, ds_id)
□ test_data_source(ds_id) -> bool
□ File yang dibuat: workspace/data_sources.py
TAHAP 4: DATASET UPLOAD & SCHEMA BUILDER
Tujuan: User bisa upload CSV/Excel dan sistem auto-generate DDL.

Langkah 4.1 — File Upload Handler

□ Buat app/workspace/upload.py:
□ save_upload(workspace_id, file) -> path
□ Validasi ukuran, ekstensi, MIME type
□ File yang dibuat: workspace/upload.py
Langkah 4.2 — CSV/Excel Sniffer & Preview

□ Buat app/workspace/dataset_parser.py:
□ sniff_delimiter(file)
□ detect_encoding(file)
□ preview(path, n=100)
□ detect_column_types(path)
□ File yang dibuat: workspace/dataset_parser.py
Langkah 4.3 — DDL Generator

□ Buat app/workspace/schema_builder/ddl_generator.py:
□ generate_ddl(table_name, columns) -> str
□ Deteksi primary key (auto increment / uuid)
□ Deteksi foreign key dari konvensi nama ({table}_id)
□ Sarankan index untuk kolom sering difilter
□ Sarankan partition untuk tabel besar (> 10 juta baris)
□ File yang dibuat: workspace/schema_builder/ddl_generator.py
Langkah 4.4 — DDL Executor (Apply & Rollback)

□ Buat app/workspace/schema_builder/executor.py:
□ apply_ddl(workspace_id, dataset_id, ddl) -> bool
□ bulk_insert(workspace_id, dataset_id, data, batch_size=1000)
□ rollback(workspace_id, dataset_id)
□ Semua operasi dalam transaction
□ File yang dibuat: workspace/schema_builder/executor.py
Langkah 4.5 — Dataset Catalog Service

□ Buat app/workspace/datasets.py:
□ create_dataset(workspace_id, name, source_type, path)
□ list_datasets(workspace_id)
□ delete_dataset(workspace_id, dataset_id)
□ get_dataset_preview(workspace_id, dataset_id, n=100)
□ File yang dibuat: workspace/datasets.py
TAHAP 5: RAG SELF-SERVICE (KNOWLEDGE BASE)
Tujuan: User bisa kelola metadata RAG sendiri (schema, glossary, query history).

Langkah 5.1 — Pinecone Namespace Manager

□ Update app/rag/pinecone_client.py:
□ upsert(vectors, namespace)
□ query(vector, namespace, top_k)
□ delete_namespace(namespace)
□ list_namespaces()
□ Namespace convention: workspace_{uuid}/schema, workspace_{uuid}/glossary, workspace_{uuid}/query_history
□ File yang dibuat: update rag/pinecone_client.py
Langkah 5.2 — Schema Ingestor

□ Buat app/rag/ingest_schema.py:
□ Baca metadata tabel & kolom dari workspace
□ Chunking per tabel, per kolom
□ Embed dengan OpenAI workspace key
□ Upsert ke namespace workspace_{id}/schema
□ File yang dibuat: rag/ingest_schema.py
Langkah 5.3 — Glossary Ingestor (Manual + CSV)

□ Buat app/rag/ingest_glossary.py:
□ ingest_from_csv(workspace_id, csv_path)
□ ingest_from_form(workspace_id, terms: List[dict])
□ add_term(workspace_id, term, definition, category, synonyms)
□ update_term, delete_term
□ Embed → upsert ke namespace workspace_{id}/glossary
□ File yang dibuat: rag/ingest_glossary.py
Langkah 5.4 — Query History Ingestor (Auto)

□ Buat app/rag/ingest_query_history.py:
□ Setelah query sukses → simpan prompt + SQL + hasil summary
□ Embed prompt → upsert ke namespace workspace_{id}/query_history
□ File yang dibuat: rag/ingest_query_history.py
Langkah 5.5 — Auto-Enrichment Service

□ Buat app/rag/auto_enrich.py:
□ Ekstrak istilah baru dari prompt user
□ Counter di Redis (ws:{id}:term:{term})
□ Jika > ambang (default 5) → sarankan ke user
□ Endpoint /api/knowledge-base/approve-term
□ File yang dibuat: rag/auto_enrich.py
Langkah 5.6 — Re-ingest Endpoint

□ Buat endpoint POST /api/knowledge-base/reingest
□ Trigger: ingest schema + glossary + query history → namespace workspace
□ Log ke ingestion_logs
□ File yang dibuat: update api/routes/knowledge_base.py
TAHAP 6: API ROUTES v2
Tujuan: Endpoint baru untuk workspace, integrasi, dataset, schema, knowledge base.

Langkah 6.1 — Workspace Routes

□ GET /api/workspaces — list workspace user
□ POST /api/workspaces — buat workspace
□ GET /api/workspaces/{id} — detail workspace
□ DELETE /api/workspaces/{id} — hapus workspace (owner only)
□ File yang dibuat: api/routes/workspaces.py
Langkah 6.2 — Integration Routes

□ GET /api/integrations — list integration + status
□ POST /api/integrations/{service} — simpan API key
□ POST /api/integrations/{service}/test — test connection
□ DELETE /api/integrations/{service} — hapus API key
□ File yang dibuat: api/routes/integrations.py
Langkah 6.3 — Data Source Routes

□ GET /api/data-sources
□ POST /api/data-sources
□ PUT /api/data-sources/{id}
□ DELETE /api/data-sources/{id}
□ POST /api/data-sources/{id}/test
□ File yang dibuat: api/routes/data_sources.py
Langkah 6.4 — Dataset Routes

□ POST /api/datasets/upload — upload file
□ GET /api/datasets
□ GET /api/datasets/{id}/preview
□ DELETE /api/datasets/{id}
□ File yang dibuat: api/routes/datasets.py
Langkah 6.5 — Schema Builder Routes

□ POST /api/schema-builder/generate-ddl
□ POST /api/schema-builder/validate-ddl
□ POST /api/schema-builder/apply
□ POST /api/schema-builder/rollback
□ File yang dibuat: api/routes/schema_builder.py
Langkah 6.6 — Knowledge Base Routes

□ GET /api/knowledge-base/schema
□ GET /api/knowledge-base/glossary
□ POST /api/knowledge-base/glossary — tambah istilah
□ PUT /api/knowledge-base/glossary/{id}
□ DELETE /api/knowledge-base/glossary/{id}
□ POST /api/knowledge-base/glossary/upload-csv
□ POST /api/knowledge-base/reingest
□ File yang dibuat: api/routes/knowledge_base.py
Langkah 6.7 — Wizard State Routes

□ GET /api/wizard/state
□ POST /api/wizard/step/{step}
□ POST /api/wizard/complete
□ File yang dibuat: api/routes/wizard.py
Langkah 6.8 — Update Chat Route untuk Workspace

□ Update POST /api/chat agar menerima workspace_id di header
□ Pakai connector, namespace, dan API key dari workspace
□ File yang dibuat: update api/routes/chat.py
TAHAP 7: FRONTEND v2
Tujuan: Halaman baru untuk onboarding, integrasi, dataset, schema builder, knowledge base.

Langkah 7.1 — Setup Halaman Baru

□ Buat struktur folder:
□ src/pages/wizard/
□ src/pages/integrations/
□ src/pages/datasets/
□ src/pages/schema-builder/
□ src/pages/knowledge-base/
□ src/pages/workspace/
□ File yang dibuat: struktur folder baru
Langkah 7.2 — Workspace Selector & Store

□ Buat store/workspaceStore.js (Zustand)
□ Buat komponen WorkspaceSwitcher.jsx di navbar
□ Simpan activeWorkspace di localStorage + Zustand
□ File yang dibuat: store/workspaceStore.js, components/WorkspaceSwitcher.jsx
Langkah 7.3 — Setup Wizard UI

□ Buat pages/wizard/SetupWizard.jsx dengan stepper 6 langkah
□ Buat komponen per step:
□ Step1Account.jsx
□ Step2ApiKeys.jsx
□ Step3DataSource.jsx
□ Step4DatasetUpload.jsx
□ Step5SchemaBuilder.jsx
□ Step6KnowledgeBase.jsx
□ Buat store/wizardStore.js (Zustand + persist)
□ File yang dibuat: 7 file di pages/wizard/ + store/wizardStore.js
Langkah 7.4 — Integrations Page

□ Buat pages/integrations/IntegrationsPage.jsx
□ Buat komponen IntegrationCard.jsx (per service)
□ Field masked display, Test button, Save, Rotate
□ File yang dibuat: 2 file di pages/integrations/
Langkah 7.5 — Datasets Page

□ Buat pages/datasets/DatasetsPage.jsx
□ Komponen UploadZone.jsx (drag & drop)
□ Komponen DatasetPreview.jsx (100 baris)
□ Komponen ColumnTypeEditor.jsx
□ File yang dibuat: 4 file di pages/datasets/
Langkah 7.6 — Schema Builder Page

□ Buat pages/schema-builder/SchemaBuilderPage.jsx
□ Integrasi Monaco Editor untuk DDL
□ Integrasi Mermaid.js atau Reactflow untuk ERD
□ Tombol Validate, Apply, Rollback
□ File yang dibuat: pages/schema-builder/SchemaBuilderPage.jsx + komponen pendukung
Langkah 7.7 — Knowledge Base Page

□ Buat pages/knowledge-base/KnowledgeBasePage.jsx dengan tab:
□ Tab Schema
□ Tab Glossary (CRUD + CSV upload)
□ Tab Query History
□ Tombol Re-ingest
□ File yang dibuat: pages/knowledge-base/KnowledgeBasePage.jsx + komponen tab
Langkah 7.8 — Update Routing & Navbar

□ Update App.jsx dengan route baru:
□ /wizard
□ /integrations
□ /datasets
□ /schema-builder
□ /knowledge-base
□ Update navbar dengan menu sesuai role
□ File yang dibuat: update App.jsx
TAHAP 8: INTEGRASI END-TO-END
Tujuan: Menghubungkan semua komponen v2 dan memastikan alur onboarding → chat → report berjalan.

Langkah 8.1 — Alur Onboarding End-to-End

□ Registrasi → workspace default terbuat
□ Wizard step 1–6 → selesai → redirect ke chat
□ Pengujian manual: onboarding dari nol < 15 menit
Langkah 8.2 — Alur Chat dengan Workspace Context

□ Dari frontend, user kirim prompt + workspace_id
□ Backend resolve workspace → connector → namespace → API keys
□ LangGraph berjalan dengan context workspace
□ Cache pakai prefix workspace
□ Pengujian manual: 2 workspace paralel, cek tidak bercampur
Langkah 8.3 — Docker Compose Final v2

□ Pastikan semua service berjalan
□ Volume uploads/ dan duckdb/ ter-mount
□ MinIO (opsional) berjalan
□ Uji docker compose up --build dari nol
TAHAP 9: TESTING
Tujuan: Memastikan setiap fitur v2 berfungsi dan isolasi multi-tenant terjaga.

Langkah 9.1 — Tulis Unit & Integration Test v2

□ test_workspace.py — CRUD + isolasi
□ test_secrets.py — Fernet encrypt/decrypt
□ test_connectors.py — 5 connector
□ test_upload.py — CSV/Excel sniff + preview
□ test_schema_builder.py — DDL generate + apply + rollback
□ test_rag_ingest.py — Ingest ke Pinecone
□ test_rate_limit.py — Backoff + queue
□ Semua test v1 diupdate agar pakai workspace context
Langkah 9.2 — Jalankan Test

□ pytest test/ -v -s
□ Perbaiki error hingga semua lolos
Langkah 9.3 — Test Isolasi Multi-Tenant

□ Buat 2 workspace dengan dataset berbeda
□ Query di workspace A → pastikan tidak lihat data workspace B
□ Cek Redis key prefix
□ Cek Pinecone namespace
□ Cek RLS di Supabase
TAHAP 10: FINALISASI DAN DOKUMENTASI
Tujuan: Menyempurnakan dokumentasi, README, dan persiapan portofolio/skripsi.

Langkah 10.1 — Update README v2

□ Lengkapi PRJ v2 dengan semua bagian 1–9
□ Tambahkan bagian Roadmap Implementasi ini
□ Sertakan cara menjalankan, testing, dan screenshot
□ Tambahkan section "Multi-Tenant Setup" dan "Bring-Your-Own-Keys"
Langkah 10.2 — Optimasi dan Review

□ Review NFR: pastikan latensi, caching, rate limit, isolasi terpenuhi
□ Profiling query dan optimasi jika perlu
□ Bersihkan kode, hapus komentar tidak perlu, pastikan standar
Langkah 10.3 — Commit Final

□ Push ke GitHub (branch main untuk stabil, dev untuk pengembangan)
□ Buat release tag v2.0.0
□ Update LICENSE dan kontributor jika perlu
📊 PROGRESS SUMMARY v2
Tahap	Deskripsi	Status
Tahap 1	Persiapan dan Fondasi Multi-Tenant	⬜ Belum
Tahap 2	Workspace Core & Encrypted Vault	⬜ Belum
Tahap 3	Dynamic Data Source Connector	⬜ Belum
Tahap 4	Dataset Upload & Schema Builder	⬜ Belum
Tahap 5	RAG Self-Service (Knowledge Base)	⬜ Belum
Tahap 6	API Routes v2	⬜ Belum
Tahap 7	Frontend v2	⬜ Belum
Tahap 8	Integrasi End-to-End	⬜ Belum
Tahap 9	Testing	⬜ Belum
Tahap 10	Finalisasi dan Dokumentasi	⬜ Belum
📌 Cara Menggunakan Checklist Ini
Tandai setiap langkah yang sudah selesai dengan mengubah [ ] menjadi [x].

Update progres secara berkala saat menyelesaikan setiap task.

Gunakan sebagai panduan agar tidak ada langkah yang terlewat.

Review PROGRESS SUMMARY setiap akhir minggu.

🚀 STATUS PROYEK SAAT INI
v1: ✅ Selesai (Backend, Frontend, Dockerized, berjalan lancar).

v2: 🟡 Perencanaan

☑ Menyusun konsep user-friendly & corporate-ready
☑ Menyusun daftar fitur baru (F-01 s/d F-12)
☑ Menyusun NFR v2 (NFR-01 s/d NFR-17)
☑ Menyusun langkah implementasi (Tahap 1–10)
□ Mulai eksekusi Tahap 1
Selanjutnya → Tahap 1: Persiapan dan Fondasi Multi-Tenant