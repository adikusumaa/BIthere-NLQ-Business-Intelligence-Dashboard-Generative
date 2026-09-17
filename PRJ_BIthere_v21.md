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


Addendum v2 — Fitur F-13: Iterative Dashboard Editor (Conversational Patch-Based Editing)
Incremental Chart Editing · Patch-Based Update · Conversational Refinement · Version Control · Live Preview · Tetap Berbasis Metabase

📖 Project Description (Update)
BIthere v2 — Addendum F-13 menambahkan kapabilitas fundamental baru pada Dashboard Builder: iterative editing tanpa regenerasi penuh.

Di versi sebelumnya (v1) dan rancangan v2 awal, Dashboard Builder bekerja secara generate-from-scratch: setiap kali user meminta perubahan, sistem akan menghapus semua chart, lalu generate ulang seluruh dashboard dari awal. Akibatnya:

User yang sudah puas dengan 5 chart tidak bisa "hanya menambah 1 chart baru" — semua harus di-generate ulang.

Perubahan warna pada 1 chart memaksa re-query dan re-render semua chart.

Filter yang sudah disetel user bisa hilang saat regenerasi.

Biaya token LLM membengkak karena setiap iterasi adalah "generate ulang dari nol".

User kehilangan kontrol granular atas dashboard mereka.

Addendum F-13 mengubah paradigma ini menjadi patch-based conversational editing:

Setiap instruksi user diterjemahkan menjadi patch (diff) terstruktur yang hanya menyentuh bagian yang ingin diubah. Sisanya tetap utuh — posisi, warna, data, filter, tidak berubah kecuali diminta.

Visi F-13: "User cukup bilang apa yang ingin diubah. Yang lain dibiarkan apa adanya."

Contoh Interaksi Real
text
[Iterasi 1]
User: "Buat dashboard fraud dengan KPI cards, monthly trend, dan top 10 states."
Bot:  ✓ Dashboard v1 dibuat dengan 3 chart.

[Iterasi 2 — TAMBAH CHART]
User: "Tambahkan chart bar di atas chart 'Top 10 States' 
       dengan judul 'Fraud by Card Brand', warna biru."
Bot:  ✓ Patch applied. Chart baru ditambahkan di posisi diminta.
     3 chart lama tetap utuh.

[Iterasi 3 — TUKAR POSISI]
User: "Tukar posisi antara 'Monthly Trend' dan 'Fraud by Card Brand'."
Bot:  ✓ Patch applied. Hanya posisi 2 chart yang ditukar.

[Iterasi 4 — UBAH WARNA]
User: "Ubah warna 'Monthly Trend' jadi merah."
Bot:  ✓ Patch applied. Hanya warna 1 chart yang diubah.

[Iterasi 5 — TAMBAH FILTER]
User: "Tambahkan filter 'card_brand' yang berlaku untuk semua chart."
Bot:  ✓ Patch applied. Filter baru ditambahkan.
     Semua chart, warna, posisi tetap seperti sebelumnya.

[Iterasi 6 — HAPUS CHART]
User: "Hapus chart 'Top 10 States'."
Bot:  ✓ Patch applied. Chart dihapus, chart lain bergeser otomatis.

[Iterasi 7 — ROLLBACK]
User: "Kembalikan ke versi 4."
Bot:  ✓ Dashboard di-rollback ke versi 4.
Setiap langkah hanya mengubah yang diminta. Tidak ada regenerasi penuh.

🎯 Tujuan & Keunggulan Utama (F-13)
Patch-Based Update (Bukan Regenerate)
Dashboard direpresentasikan sebagai state tree JSON di database. Setiap instruksi user menjadi patch terstruktur yang diterapkan pada state tersebut. Hanya bagian yang diminta yang berubah.

Conversational Refinement
User bisa berbicara natural: "tambahkan chart di atas X", "tukar posisi Y dan Z", "ubah warna chart ini jadi merah", "tambahkan filter card_brand". LLM menerjemahkan ke patch.

Preserve Everything Else
Chart yang tidak disebut tidak disentuh: warna, judul, query, posisi, filter, sorting — semua tetap. Ini kunci UX yang diinginkan.

Version Control & Rollback
Setiap patch = versi baru. User bisa lihat history, diff antar versi, dan rollback ke versi manapun.

Live Preview (Before/After)
Sebelum Apply, user lihat preview visual perubahan. Bisa Accept, Reject, atau Edit Manual.

Manual Edit Mode
Jika patch tidak sesuai ekspektasi, user bisa edit manual (drag/resize chart di UI, ubah properti di panel). Semua perubahan manual juga menghasilkan patch — sehingga tetap konsisten dengan state model.

Tetap Berbasis Metabase
Dashboard di-host di Metabase. Sistem kita hanya menjadi state manager + patch engine. Setiap patch diterjemahkan menjadi Metabase API call yang sesuai (update dashcard, update card, dst.).

Idempotent & Konflik-Aware
Jika patch di-apply dua kali, hasilnya sama. Jika patch konflik dengan state (misal: "hapus chart X" padahal X sudah tidak ada), sistem memberi tahu dengan jelas.

Token Efficiency
Karena hanya memproses "perubahan", konteks yang dikirim ke LLM jauh lebih kecil daripada "generate ulang dari nol". Menghemat token 5–10x.

⚡ New Feature (Tambahan)
ID	Fitur	Deskripsi	Prioritas
F-13	Iterative Dashboard Editor	Patch-based conversational editing	P0
F-13.1	Dashboard State Model	Representasi JSON lengkap dashboard (pages, cards, layout, filters)	P0
F-13.2	Intent Parser Agent	LLM → patch terstruktur (JSON)	P0
F-13.3	Patch Validator	Validasi patch terhadap state saat ini	P0
F-13.4	Patch Applier	Apply patch ke state + translate ke Metabase API	P0
F-13.5	Live Preview (Before/After)	Preview visual sebelum commit	P1
F-13.6	Version Control & Rollback	Simpan versi, diff, rollback	P0
F-13.7	Manual Edit Mode	Drag/resize/property panel di UI	P1
F-13.8	Patch History UI	Timeline perubahan + diff viewer	P2
F-13.9	Conflict Detection	Deteksi patch yang konflik dengan state	P1
F-13.10	Undo/Redo Stack	Undo/redo per patch	P2
Tabel Komponen Teknologi New Feature (F-13)
Komponen	Teknologi	Keterangan
Dashboard State Store	PostgreSQL dashboard_versions (JSONB)	Simpan state tiap versi
Patch Model	Pydantic discriminated union	10+ tipe patch terstruktur
Intent Parser Agent	Groq Llama 3.3 70B + JSON mode	NL → patch
Patch Validator	Pydantic + custom rules	Validasi semantik patch
Patch Applier	Python + JSON patch library	Apply patch ke state
Metabase Adapter	httpx async + Metabase API v0.48+	Translate patch ke API call
Diff Viewer	React Diff Viewer (jsondiffpatch)	Tampilkan before/after
Live Preview	React + iframe Metabase embed	Preview via query param ?preview=1
Version Control	Git-like branching (opsional)	Simpan setiap versi + parent_version_id
Conflict Detector	Optimistic locking (version number)	Tolak patch jika versi berubah
Manual Edit UI	react-grid-layout	Drag/resize chart
Undo/Redo Stack	Zustand + Redis	Simpan stack patch per session
Patch Audit	PostgreSQL dashboard_patches	Log semua patch + hasil
🧠 Alur Kerja Singkat (End-to-End) — F-13
6.1 Alur Iterasi Pertama (Generate Awal)
User ketik: "Buat dashboard fraud dengan 3 chart: KPI cards, monthly trend, top 10 states."

Planner Agent → intent = create_dashboard.

Dashboard Builder Agent → generate state v1 (JSON lengkap).

Metabase Adapter → buat dashboard + cards via Metabase API.

State Store → simpan sebagai version 1.

Frontend → render iframe Metabase.

User lihat hasil.

6.2 Alur Iterasi Berikutnya (Patch)
User ketik: "Tambahkan chart bar di atas 'Top 10 States' dengan judul 'Fraud by Card Brand', warna biru."

Planner Agent → intent = edit_dashboard, target = add_card.

Dashboard State Loader → load state versi terakhir (v1).

Intent Parser Agent (Groq) → menerima (instruksi + state v1) → output patch JSON:

json
{
  "patch_type": "ADD_CARD",
  "target_page": "page-1",
  "insert_before": "card-top10states",
  "card": {
    "type": "bar",
    "title": "Fraud by Card Brand",
    "sql": "SELECT card_brand, COUNT(*) FROM ...",
    "style": { "color": "#3b82f6" }
  }
}
Patch Validator → cek: apakah card-top10states ada? Apakah SQL valid? Apakah title unik? → OK.

Live Preview → generate "state v2 (draft)" → render preview di UI (Metabase preview mode).

User klik Accept.

Patch Applier → apply patch ke state → hasil state v2.

Metabase Adapter → translate patch ke Metabase API:

POST /api/card (buat card baru)

POST /api/dashboard/:id/cards (tambahkan ke dashboard)

PUT /api/dashboard/:id/cards (update layout jika perlu reorder)

State Store → simpan sebagai version 2 (parent = version 1).

Frontend → re-render iframe.

6.3 Alur Manual Edit
User drag chart "Monthly Trend" ke posisi lain.

Frontend generate patch MOVE_CARD dan kirim ke backend.

Patch Validator → cek posisi baru valid (tidak overlap).

Patch Applier → apply + call Metabase API.

State Store → simpan versi baru.

6.4 Alur Rollback
User klik "Rollback ke versi 4".

State Store → load state versi 4.

Diff antara versi saat ini dan versi 4 → generate reverse patches.

Patch Applier → apply reverse patches → state saat ini = state versi 4.

Metabase Adapter → sinkronkan (hapus card yang ditambahkan setelah v4, kembalikan warna, dst.).

State Store → simpan sebagai versi baru (version 4-rollback, parent = versi saat ini).

🛠️ Tech Stack Ringkasan (Tambahan F-13)
Kategori	Teknologi
State Store	PostgreSQL JSONB (dashboard_versions)
Patch Format	Pydantic discriminated union
NL → Patch	Groq Llama 3.3 70B (JSON mode)
Patch Apply	Python (custom + jsonpatch)
Metabase Sync	httpx async + Metabase API
Diff Viewer	jsondiffpatch + React component
Layout Editor	react-grid-layout (drag/resize)
Preview Render	Metabase embed with preview param
Version Control	Custom (parent_version_id, branch opsional)
Conflict Detection	Optimistic locking (version integer)
Undo/Redo	Zustand + Redis stack
Audit	PostgreSQL dashboard_patches
Struktur Folder (Tambahan)
text
bithere/
├── backend/
│   └── app/
│       └── dashboard/                    # NEW: F-13 module
│           ├── state_model.py            # DashboardState Pydantic
│           ├── patch_model.py            # Patch discriminated union
│           ├── patch_validator.py        # Validasi patch
│           ├── patch_applier.py          # Apply patch ke state
│           ├── intent_parser.py          # LLM → patch
│           ├── state_store.py            # Simpan/load versi
│           ├── version_control.py        # Rollback, diff, history
│           ├── conflict_detector.py      # Optimistic lock
│           ├── metabase_adapter.py       # State → Metabase API
│           └── tests/
│               ├── test_patch_model.py
│               ├── test_patch_validator.py
│               ├── test_patch_applier.py
│               ├── test_intent_parser.py
│               ├── test_version_control.py
│               └── test_metabase_adapter.py
├── frontend/
│   └── src/
│       ├── components/
│       │   └── dashboard-editor/         # NEW
│       │       ├── DashboardEditor.jsx
│       │       ├── PatchHistoryPanel.jsx
│       │       ├── DiffViewer.jsx
│       │       ├── LivePreview.jsx
│       │       ├── ManualEditCanvas.jsx  # react-grid-layout
│       │       └── PropertyPanel.jsx     # edit warna, judul, dsb.
│       └── pages/
│           └── DashboardEditorPage.jsx   # NEW
└── scripts/
    └── migrations/
        └── 003_dashboard_versions.sql    # NEW
6. Kebutuhan Fungsional (Tambahan)
6.3 Fungsional v2 — F-13 (Iterative Dashboard Editor)
ID	Kebutuhan	Deskripsi	Prioritas
FR-21	Dashboard State Model	Sistem menyimpan state dashboard sebagai JSON terstruktur (pages, cards, layout, filters)	P0
FR-22	Patch Generation	Sistem menerjemahkan instruksi NL user menjadi patch terstruktur (JSON)	P0
FR-23	Patch Types	Sistem mendukung minimal 10 tipe patch: ADD_CARD, REMOVE_CARD, MOVE_CARD, RESIZE_CARD, CHANGE_COLOR, CHANGE_TITLE, CHANGE_CHART_TYPE, ADD_FILTER, REMOVE_FILTER, UPDATE_SQL	P0
FR-24	Patch Validation	Sebelum apply, patch divalidasi terhadap state saat ini (referential integrity, uniqueness, SQL validity)	P0
FR-25	Patch Application	Patch di-apply ke state → hasil state baru	P0
FR-26	Preserve Non-Targeted	Chart/property yang tidak disebut dalam patch tidak berubah sama sekali	P0
FR-27	Metabase Sync	Setiap patch diterjemahkan menjadi Metabase API call yang sesuai	P0
FR-28	Version Control	Setiap patch menghasilkan versi baru (parent_version_id)	P0
FR-29	Rollback	User dapat rollback ke versi manapun	P0
FR-30	Diff Viewer	UI menampilkan diff (before/after) antar versi	P1
FR-31	Live Preview	Sebelum commit, user dapat melihat preview visual patch	P1
FR-32	Manual Edit	User dapat drag/resize chart dan edit properti di UI; perubahan ini juga jadi patch	P1
FR-33	Conflict Detection	Sistem mendeteksi dan menolak patch yang konflik dengan versi terkini	P1
FR-34	Undo/Redo	User dapat undo/redo patch dalam session	P2
FR-35	Patch History	UI menampilkan timeline semua patch yang pernah diterapkan	P2
FR-36	Idempotency	Apply patch yang sama dua kali → hasil sama	P0
FR-37	Rollback Metabase	Rollback state → Metabase ikut di-rollback (hapus/restore cards)	P0
FR-38	Manual Override	User dapat edit patch yang diusulkan LLM sebelum apply	P2
7. Kebutuhan Non-Fungsional (Tambahan)
7.8 Performa, Keandalan, dan Konsistensi (F-13)
NFR-18: Latensi Patch Apply
Jenis Patch	Target Latensi	Catatan
Patch tanpa Metabase call (misal: preview saja)	< 500 ms	Hanya state manipulation
Patch dengan 1 Metabase API call	< 2 detik	CREATE/UPDATE card
Patch dengan banyak Metabase call (reorder semua)	< 5 detik	Batch + parallel
Rollback (reverse patch)	< 5 detik	Multiple API calls
Alasan:

User iteratif — kalau tiap perubahan 10+ detik, iterasi jadi menyiksa.

Preview harus < 500 ms karena ini murni JSON manipulation.

Sync ke Metabase memakan waktu karena HTTP round-trip.

Optimasi:

Optimasi	Deskripsi
Batch Metabase API	Gabungkan beberapa update jadi satu PUT /api/dashboard/:id
Parallel API calls	Untuk update independent (2 card berbeda), jalankan paralel
Optimistic UI	Frontend update dulu, backend async sync
Debounce manual edit	Drag/resize user di-debounce 500 ms sebelum kirim patch
NFR-19: Konsistensi State (State Consistency)
Parameter	Deskripsi
Atomic Apply	Patch apply dalam transaction — kalau gagal, rollback ke state sebelumnya
Optimistic Lock	Setiap patch menyertakan base_version. Jika versi sudah berubah, patch ditolak dengan konflik.
Idempotency	Apply patch yang sama 2x → hasil identik (pakai patch hash)
Reconciliation	Jika Metabase state berbeda dari state store, sistem bisa reconcile (sync ulang)
Alasan:

Multi-tab user bisa membuka dashboard yang sama → rawan konflik.

Metabase bisa gagal di tengah apply → harus atomic.

Reconciliation memastikan state store & Metabase selalu sinkron.

NFR-20: Preservasi Non-Targeted Fields
Parameter	Deskripsi
Preserve by Default	Field yang tidak disebut patch tidak boleh berubah
Whitelist Update	Patch hanya bisa update field di whitelist (misal: ADD_CARD hanya tambah card, tidak ubah card lain)
Diff Verification	Setelah apply, sistem bisa verifikasi: field non-targeted sama dengan sebelumnya
Alasan:

Ini inti dari F-13. Kalau kita salah preserve, user frustrasi.

Whitelist mencegah patch "bocor" mengubah sesuatu yang tidak diminta.

NFR-21: Reliability Rollback
Parameter	Deskripsi
Rollback Accuracy	Rollback ke versi N harus menghasilkan state yang identik dengan versi N
Metabase Reconciliation	Setelah rollback, Metabase harus sinkron (hapus/tambah card)
Rollback Time	< 10 detik untuk dashboard dengan 20 card
Rollback Audit	Rollback dicatat sebagai patch baru (ROLLBACK_TO_VERSION)
Alasan:

Rollback adalah "escape hatch" — harus benar-benar reliable.

User butuh kepercayaan bahwa rollback tidak akan merusak state.

NFR-22: Token Efficiency (Patch Mode)
Parameter	Deskripsi
Context Size	Context yang dikirim ke LLM = state ringkas (ringkasan, bukan full JSON)
Token Reduction	Target: 5x lebih hemat dibanding generate-from-scratch
Patch Output	Output LLM = patch JSON kecil (bukan full dashboard)
Cache	Cache patch per (instruction + state hash)
Alasan:

Generate ulang = kirim schema + state lengkap → mahal.

Patch mode = kirim hanya ringkasan state + instruksi → murah.

Caching patch = iterasi identik di workspace lain gratis.

NFR-23: Concurrency Safety
Parameter	Deskripsi
Optimistic Lock	Setiap patch menyertakan base_version. Jika tidak cocok, tolak.
Lock on Apply	Selama apply, dashboard di-lock (mutex di Redis)
Timeout Lock	Lock timeout 30 detik (untuk handle crash)
Conflict Resolution	User bisa "force apply" dengan merge, atau rollback dulu
Alasan:

Multi-user workspace bisa edit bersamaan.

Concurrent edits tanpa lock = data corrupt.

NFR-24: Auditability Patch
Parameter	Deskripsi
Patch Log	Semua patch dicatat: user, timestamp, patch content, result
Diff History	Bisa lihat diff antar versi kapan saja
Undo Trail	Bisa lihat siapa mengubah apa kapan
Retention	Minimal 90 hari
Alasan:

Corporate butuh audit trail.

Debugging issue dashboard butuh history.

NFR-25: Preview Isolation
Parameter	Deskripsi
Preview = Sandbox	Preview tidak mengubah Metabase asli
Preview Storage	Preview disimpan di Redis (TTL 10 menit)
Preview Cleanup	Setelah commit atau timeout, preview dihapus
Preview Renders	Preview pakai Metabase embed dengan ?preview=1 (state lokal)
Alasan:

Preview harus aman — kalau user reject, tidak ada yang berubah.

Preview jangan kontaminasi state asli.

📊 Ringkasan NFR Tambahan (F-13)
ID	NFR	Target
NFR-18	Latensi Patch Apply	< 500 ms (state) / < 2 detik (1 API)
NFR-19	Konsistensi State	Atomic, optimistic lock, idempotent
NFR-20	Preservasi Non-Targeted	100% preserve field yang tidak disebut
NFR-21	Reliability Rollback	Akurat, sinkron Metabase, < 10 detik
NFR-22	Token Efficiency	5x lebih hemat dari generate-from-scratch
NFR-23	Concurrency Safety	Optimistic lock + Redis mutex
NFR-24	Auditability Patch	Log semua patch, retensi 90 hari
NFR-25	Preview Isolation	Sandbox di Redis, tidak kontaminasi state
8. Manajemen State atau Alur Logika (Tambahan)
8.8 Dashboard State Model (F-13)
Dashboard direpresentasikan sebagai JSON state tree:

json
{
  "dashboard_id": "uuid-v4",
  "workspace_id": "uuid-v4",
  "metabase_dashboard_id": 123,
  "version": 5,
  "parent_version": 4,
  "created_at": "2026-01-15T10:00:00Z",
  "pages": [
    {
      "id": "page-1",
      "name": "Overview",
      "layout_columns": 24,
      "cards": [
        {
          "id": "card-kpi-fraud",
          "title": "Total Fraud",
          "type": "scalar",
          "sql": "SELECT COUNT(*) FROM fraud_labels WHERE fraud_label = 'Yes'",
          "position": { "row": 0, "col": 0, "size_x": 6, "size_y": 3 },
          "style": {
            "color": "#3b82f6",
            "show_legend": false,
            "number_format": "comma"
          },
          "metabase": {
            "card_id": 45,
            "dashcard_id": 78
          },
          "filters_applied": ["filter-card-brand", "filter-state"]
        }
      ],
      "filters": [
        {
          "id": "filter-card-brand",
          "name": "Card Brand",
          "type": "category",
          "column": "cards.card_brand",
          "default": null,
          "metabase_parameter_id": "abc123"
        }
      ]
    }
  ],
  "metadata": {
    "generated_by": "Dashboard Builder Agent",
    "generated_at": "2026-01-15T09:55:00Z",
    "llm_tokens_used": 1250
  }
}
Field penting:

Field	Deskripsi
version	Nomor versi saat ini (increment per patch)
parent_version	Versi sebelumnya (untuk rollback)
pages[].cards[]	List chart per halaman
cards[].id	ID internal (stabil, dipakai referensi di patch)
cards[].metabase.card_id	ID card di Metabase (untuk API call)
cards[].metabase.dashcard_id	ID dashcard di Metabase
cards[].position	Posisi grid (row, col, size_x, size_y)
cards[].style	Warna, legend, format
pages[].filters	Filter global per halaman
8.9 Patch Model (F-13)
Semua patch adalah discriminated union dengan patch_type:

python
class PatchType(str, Enum):
    ADD_CARD = "ADD_CARD"
    REMOVE_CARD = "REMOVE_CARD"
    MOVE_CARD = "MOVE_CARD"
    RESIZE_CARD = "RESIZE_CARD"
    CHANGE_COLOR = "CHANGE_COLOR"
    CHANGE_TITLE = "CHANGE_TITLE"
    CHANGE_CHART_TYPE = "CHANGE_CHART_TYPE"
    UPDATE_SQL = "UPDATE_SQL"
    ADD_FILTER = "ADD_FILTER"
    REMOVE_FILTER = "REMOVE_FILTER"
    ROLLBACK_TO_VERSION = "ROLLBACK_TO_VERSION"
    COMPOSITE = "COMPOSITE"  # multiple patches sekaligus
Detail per Patch Type
Patch Type	Field	Contoh NL	Efek
ADD_CARD	page_id, card (full), insert_before (opsional), insert_after (opsional)	"Tambahkan chart di atas X"	Card baru ditambahkan
REMOVE_CARD	card_id	"Hapus chart X"	Card dihapus
MOVE_CARD	card_id, new_position	"Pindahkan X ke kanan"	Posisi berubah
SWAP_CARDS	card_id_a, card_id_b	"Tukar X dan Y"	2 card tukar posisi
RESIZE_CARD	card_id, new_size	"Perbesar X"	Ukuran berubah
CHANGE_COLOR	card_id, color	"Ubah warna X jadi merah"	Warna berubah
CHANGE_TITLE	card_id, new_title	"Ganti judul X jadi 'Penjualan'"	Judul berubah
CHANGE_CHART_TYPE	card_id, new_type	"Ubah X jadi line chart"	Tipe chart berubah
UPDATE_SQL	card_id, new_sql	"Ubah query X agar filter juga fraud"	SQL berubah
ADD_FILTER	page_id, filter, apply_to (list card_id atau "all")	"Tambahkan filter card_brand"	Filter ditambahkan
REMOVE_FILTER	filter_id	"Hapus filter X"	Filter dihapus
ROLLBACK_TO_VERSION	target_version	"Kembalikan ke versi 4"	Rollback
COMPOSITE	patches: List[Patch]	"Tambah chart A dan ubah warna B"	Multiple patches
Contoh Patch JSON
ADD_CARD:

json
{
  "patch_type": "ADD_CARD",
  "page_id": "page-1",
  "insert_before": "card-top10states",
  "card": {
    "id": "card-fraud-by-brand",
    "title": "Fraud by Card Brand",
    "type": "bar",
    "sql": "SELECT c.card_brand, COUNT(*) as total FROM transactions t JOIN cards c ON t.card_id = c.id JOIN fraud_labels f ON t.id = f.id WHERE f.fraud_label = 'Yes' GROUP BY c.card_brand ORDER BY total DESC",
    "position": { "row": 0, "col": 0, "size_x": 12, "size_y": 4 },
    "style": { "color": "#3b82f6" }
  }
}
SWAP_CARDS:

json
{
  "patch_type": "SWAP_CARDS",
  "card_id_a": "card-monthly-trend",
  "card_id_b": "card-fraud-by-brand"
}
CHANGE_COLOR:

json
{
  "patch_type": "CHANGE_COLOR",
  "card_id": "card-monthly-trend",
  "color": "#ef4444"
}
COMPOSITE:

json
{
  "patch_type": "COMPOSITE",
  "patches": [
    { "patch_type": "ADD_CARD", ... },
    { "patch_type": "CHANGE_COLOR", ... }
  ]
}
8.10 Intent Parser Agent (F-13)
Tugas: Menerima instruksi NL user + ringkasan state saat ini → output patch JSON.

Prompt Template:

text
You are a dashboard editing assistant.

CURRENT DASHBOARD STATE (summary):
- Page 1 "Overview" has 3 cards:
  * card-kpi-fraud: "Total Fraud" (scalar, position row=0 col=0)
  * card-monthly-trend: "Monthly Trend" (line, position row=3 col=0, color=#3b82f6)
  * card-top10states: "Top 10 States" (bar, position row=3 col=12, color=#10b981)
- Filters: none

USER INSTRUCTION:
"Tambahkan chart bar di atas 'Top 10 States' dengan judul 'Fraud by Card Brand', warna biru."

TASK:
Generate a SINGLE patch JSON that:
1. Only modifies what user explicitly asked.
2. Preserves everything else.
3. Uses valid card_id references.
4. Follows the patch schema.

OUTPUT (JSON only):
{
  "patch_type": "...",
  ...
}
Aturan Penting untuk LLM:

Preserve-first — jangan ubah yang tidak diminta.

Stable ID reference — gunakan card_id yang ada di state.

Valid patch_type — harus salah satu dari 13 tipe.

SQL harus SELECT-only — validasi keamanan.

Position conflict — saat menambahkan, geser card lain jika perlu (auto-shift).

JSON mode — output harus JSON, bukan teks.

8.11 Patch Validator (F-13)
Tugas: Validasi patch sebelum apply.

Aturan Validasi:

Aturan	Deskripsi	Contoh Pelanggaran
Referential Integrity	Semua card_id, page_id, filter_id harus ada di state	Patch MOVE_CARD dengan card_id yang tidak ada
Uniqueness	Title card harus unik dalam 1 page	ADD_CARD dengan title yang sudah dipakai
SQL Safety	SQL harus SELECT-only	UPDATE_SQL dengan DROP TABLE
Position Validity	Posisi tidak overlap (kecuali auto-shift)	MOVE_CARD ke posisi yang bentrok
Size Validity	Size dalam batas (min 2x2, max 24 kolom)	RESIZE_CARD size_x = 30
Color Format	Hex color valid	CHANGE_COLOR warna "biru" (bukan hex)
Filter Reference	ADD_FILTER column harus ada di schema	ADD_FILTER "card_brand" padahal kolom tidak ada
Version Match	base_version harus = state version saat ini	Patch dari versi lama
No Recursive Composite	Composite tidak boleh berisi composite	Nested COMPOSITE
Output: Valid atau Invalid(reason).

8.12 Patch Applier (F-13)
Tugas: Apply patch ke state → hasil state baru.

Alur:

text
1. Load state saat ini (state_old)
2. Deep copy ke state_new
3. Berdasarkan patch_type:
   a. ADD_CARD:
      - Insert card ke page
      - Auto-shift card lain jika perlu (grid layout)
      - Generate metabase API call: POST /api/card, POST /api/dashboard/:id/cards
   b. REMOVE_CARD:
      - Hapus card dari page
      - Auto-merge space (grid reflow)
      - Generate: DELETE /api/dashboard/:id/cards/:dashcard_id
   c. SWAP_CARDS:
      - Tukar posisi 2 card
      - Generate: PUT /api/dashboard/:id/cards (batch update)
   d. dst.
4. Verifikasi: field non-targeted sama? (diff check)
5. Simpan state_new sebagai versi baru
6. Return state_new + API calls to execute
8.13 Metabase Adapter (F-13)
Tugas: Translate patch ke Metabase API call.

Mapping Patch → Metabase API:

Patch Type	Metabase API Call
ADD_CARD	POST /api/card (buat card) + POST /api/dashboard/:id/cards (attach)
REMOVE_CARD	DELETE /api/dashboard/:id/cards/:dashcard_id + DELETE /api/card/:id (opsional)
MOVE_CARD	PUT /api/dashboard/:id/cards (batch update semua posisi)
SWAP_CARDS	PUT /api/dashboard/:id/cards (batch update 2 card)
RESIZE_CARD	PUT /api/dashboard/:id/cards (update size)
CHANGE_COLOR	PUT /api/card/:id (update visualization_settings)
CHANGE_TITLE	PUT /api/card/:id (update name)
CHANGE_CHART_TYPE	PUT /api/card/:id (update display)
UPDATE_SQL	PUT /api/card/:id (update dataset_query)
ADD_FILTER	POST /api/dashboard/:id (update parameters) + PUT /api/dashboard/:id/cards (bind parameters to cards)
REMOVE_FILTER	PUT /api/dashboard/:id (remove parameter)
ROLLBACK_TO_VERSION	Multiple calls (hapus/restore cards)
Batch Optimization:

Untuk patch yang menyentuh banyak card (misal: auto-shift setelah ADD_CARD), batch dalam 1 request:

http
PUT /api/dashboard/123/cards
Content-Type: application/json

{
  "cards": [
    { "id": 78, "row": 0, "col": 0, "size_x": 6, "size_y": 4 },
    { "id": 79, "row": 0, "col": 6, "size_x": 6, "size_y": 4 },
    { "id": 80, "row": 4, "col": 0, "size_x": 12, "size_y": 4 }
  ]
}
8.14 Version Control (F-13)
Tabel DB:

sql
CREATE TABLE dashboard_versions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dashboard_id    UUID NOT NULL,
    workspace_id    UUID NOT NULL,
    version         INTEGER NOT NULL,
    parent_version  INTEGER,
    state_json      JSONB NOT NULL,
    patch_applied   JSONB,
    created_by      UUID,
    created_at      TIMESTAMPTZ DEFAULT now(),
    UNIQUE (dashboard_id, version)
);

CREATE TABLE dashboard_patches (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dashboard_id    UUID NOT NULL,
    from_version    INTEGER NOT NULL,
    to_version      INTEGER NOT NULL,
    patch_json      JSONB NOT NULL,
    patch_hash      TEXT NOT NULL,
    status          TEXT,  -- applied / rejected / failed
    error_message   TEXT,
    created_by      UUID,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_versions_dashboard ON dashboard_versions(dashboard_id, version DESC);
CREATE INDEX idx_patches_dashboard ON dashboard_patches(dashboard_id, created_at DESC);
Rollback Flow:

text
1. User minta rollback ke versi N.
2. Load state versi N.
3. Bandingkan dengan state saat ini → generate diff.
4. Diff → generate reverse patches.
5. Apply reverse patches → state = state versi N.
6. Sync ke Metabase.
7. Simpan sebagai versi baru (version = N+1, parent = current).
8. Log di dashboard_patches (patch_type = ROLLBACK_TO_VERSION).
8.15 Live Preview (F-13)
Konsep:

Sebelum commit patch, generate state draft dan simpan di Redis dengan TTL 10 menit.

Frontend render preview via Metabase embed (state draft di-embed sebagai query param).

User lihat before/after side-by-side atau toggle.

Tombol: Accept (apply patch) · Reject (buang draft) · Edit Manual (buka manual editor).

Preview Key: ws:{id}:dashboard:{dashboard_id}:preview:{preview_id}

8.16 Conflict Detection (F-13)
Optimistic Locking:

Setiap patch yang dikirim dari frontend wajib menyertakan base_version:

json
{
  "patch": { ... },
  "base_version": 5
}
Backend:

python
current_version = load_current_version(dashboard_id)
if base_version != current_version:
    raise ConflictError(
        f"Dashboard sudah diupdate ke versi {current_version}. "
        f"Patch Anda untuk versi {base_version}. Silakan refresh."
    )
Resolution Options:

Refresh & Retry — user load versi terbaru, ulangi patch.

Force Apply — user paksa apply dengan merge (risiko konflik).

Rollback First — user rollback dulu ke versi base_version, lalu apply.

8.17 Manual Edit Mode (F-13)
UI:

Canvas drag/resize (react-grid-layout)

Property panel (warna, judul, tipe chart)

Tombol Add/Remove card

Flow:

User drag card → frontend calculate new position.

Frontend generate patch MOVE_CARD → kirim ke backend (debounce 500 ms).

Backend validasi & apply → Metabase sync.

Frontend update state.

Semua manual edit = patch → konsisten dengan conversational edit.

8.18 Undo/Redo Stack (F-13)
Redis key: ws:{id}:dashboard:{dashboard_id}:session:{session_id}:undo_stack

Stack berisi: List of patch + state hash.

Undo:

Pop patch terakhir dari undo_stack.

Generate reverse patch.

Push ke redo_stack.

Apply reverse patch.

Redo:

Pop patch dari redo_stack.

Apply patch.

Push kembali ke undo_stack.

8.19 Cost & Token Optimization (F-13)
Comparison:

Mode	Context Size	Output Size	Total Token
Generate-from-scratch (v1)	Schema (~2000) + state (~3000)	Full dashboard (~4000)	~9000
Patch-based (F-13)	Schema (~2000) + state summary (~500) + instruction (~50)	Patch (~300)	~2850
Hemat: ~3.2x.

Dengan caching patch hash → hemat sampai 10x untuk iterasi identik.

9. Instruksi Eksekusi dan Pengujian (Tambahan)
9.5 Struktur Folder Test (Tambahan F-13)
text
test/
├── test_dashboard_state.py         # NEW: State model
├── test_patch_model.py             # NEW: Patch Pydantic model
├── test_intent_parser.py           # NEW: NL → patch
├── test_patch_validator.py         # NEW: Validasi patch
├── test_patch_applier.py           # NEW: Apply patch
├── test_metabase_adapter.py        # NEW: Patch → Metabase API
├── test_version_control.py         # NEW: Rollback & diff
├── test_conflict_detection.py      # NEW: Optimistic lock
├── test_preservation.py            # NEW: Non-targeted field preserved
├── test_dashboard_editor_e2e.py    # NEW: Full iterasi
└── test_idempotency.py             # NEW: Patch 2x = sama
9.6 Daftar Test (F-13)
File Test	Yang Diuji	Skenario Utama
test_dashboard_state.py	State model	Load, save, update state
test_patch_model.py	Patch schema	Validasi tipe patch & field
test_intent_parser.py	NL → patch	"Tambah chart X" → ADD_CARD patch
test_patch_validator.py	Validasi	Referential integrity, SQL safety
test_patch_applier.py	Apply	ADD_CARD → state bertambah
test_metabase_adapter.py	API mapping	Patch → API call benar
test_version_control.py	Rollback	Rollback ke v4 → state = v4
test_conflict_detection.py	Optimistic lock	Patch versi lama → ditolak
test_preservation.py	Preserve non-targeted	ADD_CARD tidak ubah warna card lain
test_dashboard_editor_e2e.py	Full iterasi	7 iterasi berturut-turut
test_idempotency.py	Idempotency	Apply patch 2x → sama
9.7 Pengujian Manual (F-13)
Generate awal → "Buat dashboard fraud dengan 3 chart."

ADD_CARD → "Tambahkan chart bar di atas 'Top 10 States'."

SWAP_CARDS → "Tukar 'Monthly Trend' dengan 'Fraud by Card Brand'."

CHANGE_COLOR → "Ubah warna 'Monthly Trend' jadi merah."

ADD_FILTER → "Tambahkan filter card_brand."

RESIZE_CARD → "Perbesar 'Top 10 States'."

REMOVE_CARD → "Hapus 'Fraud by Card Brand'."

Rollback → "Kembalikan ke versi 3."

Undo → Tekan Ctrl+Z → patch terakhir di-undo.

Conflict → Buka 2 tab, edit di tab A, edit di tab B → tab B dapat pesan konflik.

Manual Edit → Drag chart di UI → otomatis patch.

Preview → Setiap patch tampil preview dulu → Accept/Reject.

📌 LANGKAH IMPLEMENTASI v2 — Tambahan (F-13)
Tandai [ ] → [x] saat selesai.

TAHAP 11: DASHBOARD STATE MODEL
Tujuan: Membangun fondasi state-based dashboard.

Langkah 11.1 — Definisi DashboardState Pydantic Model

□ Buat app/dashboard/state_model.py:
□ DashboardState (pages, cards, filters, version)
□ Page, Card, Filter (nested)
□ Position, Style (value objects)
□ JSON schema export untuk LLM prompt
□ File yang dibuat: dashboard/state_model.py
Langkah 11.2 — Definisi Patch Pydantic Model (Discriminated Union)

□ Buat app/dashboard/patch_model.py:
□ Base Patch dengan patch_type
□ 13 tipe patch: ADD_CARD, REMOVE_CARD, MOVE_CARD, SWAP_CARDS, RESIZE_CARD, CHANGE_COLOR, CHANGE_TITLE, CHANGE_CHART_TYPE, UPDATE_SQL, ADD_FILTER, REMOVE_FILTER, ROLLBACK_TO_VERSION, COMPOSITE
□ CompositePatch dengan list patch
□ JSON schema export untuk LLM prompt
□ File yang dibuat: dashboard/patch_model.py
Langkah 11.3 — Migrasi Database Dashboard Versions

□ Buat scripts/migrations/003_dashboard_versions.sql:
□ Tabel dashboard_versions
□ Tabel dashboard_patches
□ Index pada dashboard_id, version, created_at
□ RLS policy per workspace
□ File yang dibuat: scripts/migrations/003_dashboard_versions.sql
Langkah 11.4 — State Store Service

□ Buat app/dashboard/state_store.py:
□ save_version(dashboard_id, state, patch, user_id) -> version
□ load_version(dashboard_id, version) -> DashboardState
□ load_latest(dashboard_id) -> DashboardState
□ list_versions(dashboard_id) -> List[VersionSummary]
□ get_patches(dashboard_id) -> List[PatchLog]
□ File yang dibuat: dashboard/state_store.py
TAHAP 12: INTENT PARSER AGENT
Tujuan: Menerjemahkan NL → patch.

Langkah 12.1 — Prompt Template Intent Parser

□ Buat app/dashboard/prompts/intent_parser.md:
□ Instruksi preserve-first
□ Contoh 13 tipe patch
□ Schema patch dalam JSON
□ Aturan: SELECT-only, stable ID, dst.
□ File yang dibuat: dashboard/prompts/intent_parser.md
Langkah 12.2 — Intent Parser Agent

□ Buat app/dashboard/intent_parser.py:
□ parse_instruction(instruction, state_summary) -> Patch
□ Panggil Groq LLM (API key workspace) dengan JSON mode
□ Parse output → Pydantic Patch
□ Error handling: jika LLM output tidak valid, retry 1x, else fallback
□ Cache patch per (instruction_hash + state_hash) di Redis
□ File yang dibuat: dashboard/intent_parser.py
Langkah 12.3 — State Summarizer

□ Buat app/dashboard/state_summarizer.py:
□ summarize_state(state) -> str (untuk prompt LLM)
□ Ringkas: nama page, daftar card (id, title, type, position), filters
□ Token-optimized (~500 token untuk dashboard 20 card)
□ File yang dibuat: dashboard/state_summarizer.py
TAHAP 13: PATCH VALIDATOR & APPLIER
Tujuan: Validasi & apply patch ke state.

Langkah 13.1 — Patch Validator

□ Buat app/dashboard/patch_validator.py:
□ validate(patch, current_state) -> ValidationResult
□ Referential integrity (card_id, page_id, filter_id)
□ Uniqueness (title)
□ SQL safety (SELECT-only)
□ Position validity (grid)
□ Size validity
□ Color format (hex)
□ Version match
□ No recursive composite
□ File yang dibuat: dashboard/patch_validator.py
Langkah 13.2 — Patch Applier

□ Buat app/dashboard/patch_applier.py:
□ apply(state, patch) -> (new_state, metabase_calls)
□ Deep copy state → apply patch
□ Auto-shift grid untuk ADD_CARD
□ Reflow untuk REMOVE_CARD
□ Return list Metabase API calls yang harus dieksekusi
□ Verifikasi non-targeted fields preserved
□ File yang dibuat: dashboard/patch_applier.py
Langkah 13.3 — Grid Layout Engine

□ Buat app/dashboard/grid.py:
□ auto_shift(cards, new_card) -> List[Position]
□ reflow(cards) -> List[Position]
□ check_overlap(pos_a, pos_b) -> bool
□ find_free_position(cards, size) -> Position
□ File yang dibuat: dashboard/grid.py
Langkah 13.4 — Preservation Checker

□ Buat app/dashboard/preservation.py:
□ verify_preservation(old_state, new_state, patch) -> bool
□ Field yang tidak disebut patch → harus sama
□ File yang dibuat: dashboard/preservation.py
TAHAP 14: METABASE ADAPTER
Tujuan: Translate patch ke Metabase API call.

Langkah 14.1 — Metabase Client Extension

□ Update app/services/metabase.py:
□ create_card(card_config) -> card_id
□ update_card(card_id, updates)
□ delete_card(card_id)
□ add_card_to_dashboard(dashboard_id, card_id, position) -> dashcard_id
□ update_dashcards(dashboard_id, updates: List)
□ delete_dashcard(dashboard_id, dashcard_id)
□ update_dashboard(dashboard_id, updates)
□ File yang dibuat: update services/metabase.py
Langkah 14.2 — Patch → Metabase Adapter

□ Buat app/dashboard/metabase_adapter.py:
□ patch_to_api_calls(patch, state) -> List[MetabaseCall]
□ Mapping per patch type
□ Batch optimization untuk reorder
□ Retry & error handling
□ File yang dibuat: dashboard/metabase_adapter.py
Langkah 14.3 — Sync Verification

□ Buat app/dashboard/sync_verifier.py:
□ verify_sync(dashboard_id, state) -> bool
□ Bandingkan state store vs Metabase
□ Reconciliation: perbaiki perbedaan
□ File yang dibuat: dashboard/sync_verifier.py
TAHAP 15: VERSION CONTROL & CONFLICT
Tujuan: Rollback, diff, conflict detection.

Langkah 15.1 — Version Control Service

□ Buat app/dashboard/version_control.py:
□ rollback(dashboard_id, target_version, user_id) -> new_state
□ diff(version_a, version_b) -> Diff
□ reverse_patch(diff) -> Patch
□ Log ke dashboard_patches
□ File yang dibuat: dashboard/version_control.py
Langkah 15.2 — Conflict Detector

□ Buat app/dashboard/conflict_detector.py:
□ check_conflict(dashboard_id, base_version) -> bool
□ Raise ConflictError jika versi tidak cocok
□ File yang dibuat: dashboard/conflict_detector.py
Langkah 15.3 — Lock Manager

□ Buat app/dashboard/lock.py:
□ Redis mutex per dashboard (TTL 30 detik)
□ Context manager with lock(dashboard_id):
□ File yang dibuat: dashboard/lock.py
Langkah 15.4 — Undo/Redo Service

□ Buat app/dashboard/undo_redo.py:
□ Stack di Redis per session
□ push_undo(session_id, patch)
□ undo(session_id) -> Patch
□ redo(session_id) -> Patch
□ File yang dibuat: dashboard/undo_redo.py
TAHAP 16: API ROUTES v2 (F-13)
Tujuan: Endpoint untuk dashboard editing.

Langkah 16.1 — Dashboard State Routes

□ GET /api/dashboards/{id}/state — state terkini
□ GET /api/dashboards/{id}/versions — list versi
□ GET /api/dashboards/{id}/versions/{v} — state versi V
□ GET /api/dashboards/{id}/patches — log patch
□ File yang dibuat: api/routes/dashboard_state.py
Langkah 16.2 — Patch Routes

□ POST /api/dashboards/{id}/patch/parse — NL → patch (untuk preview)
□ POST /api/dashboards/{id}/patch/preview — preview patch
□ POST /api/dashboards/{id}/patch/apply — apply patch
□ POST /api/dashboards/{id}/patch/reject — reject preview
□ File yang dibuat: api/routes/dashboard_patch.py
Langkah 16.3 — Version Routes

□ POST /api/dashboards/{id}/rollback — rollback ke versi
□ GET /api/dashboards/{id}/diff?v1=3&v2=5 — diff antar versi
□ File yang dibuat: api/routes/dashboard_version.py
Langkah 16.4 — Undo/Redo Routes

□ POST /api/dashboards/{id}/undo
□ POST /api/dashboards/{id}/redo
□ File yang dibuat: api/routes/dashboard_undo.py
Langkah 16.5 — Manual Edit Routes

□ POST /api/dashboards/{id}/manual-edit — patch dari drag/resize UI
□ File yang dibuat: api/routes/dashboard_manual.py
TAHAP 17: FRONTEND v2 (F-13)
Tujuan: UI dashboard editor.

Langkah 17.1 — Dashboard Editor Layout

□ Buat pages/DashboardEditorPage.jsx:
□ Split view: chat (kiri) + preview (kanan)
□ Panel patch history (bawah atau sidebar)
□ Property panel (kanan)
□ File yang dibuat: pages/DashboardEditorPage.jsx
Langkah 17.2 — Chat Panel untuk Editing

□ Buat components/dashboard-editor/ChatPanel.jsx:
□ Input instruksi NL
□ Tampilkan patch yang diusulkan (JSON viewer)
□ Tombol Accept / Reject / Edit Manual
□ File yang dibuat: components/dashboard-editor/ChatPanel.jsx
Langkah 17.3 — Live Preview

□ Buat components/dashboard-editor/LivePreview.jsx:
□ Iframe Metabase (preview mode)
□ Toggle before/after
□ Highlight area yang berubah
□ File yang dibuat: components/dashboard-editor/LivePreview.jsx
Langkah 17.4 — Diff Viewer

□ Buat components/dashboard-editor/DiffViewer.jsx:
□ Gunakan jsondiffpatch
□ Tampilkan before/after state
□ Highlight per-field
□ File yang dibuat: components/dashboard-editor/DiffViewer.jsx
Langkah 17.5 — Patch History Panel

□ Buat components/dashboard-editor/PatchHistoryPanel.jsx:
□ Timeline patch
□ Tombol rollback per versi
□ Filter by user, tanggal
□ File yang dibuat: components/dashboard-editor/PatchHistoryPanel.jsx
Langkah 17.6 — Manual Edit Canvas

□ Buat components/dashboard-editor/ManualEditCanvas.jsx:
□ react-grid-layout
□ Drag/resize card
□ Auto-generate patch saat drag selesai (debounce 500 ms)
□ File yang dibuat: components/dashboard-editor/ManualEditCanvas.jsx
Langkah 17.7 — Property Panel

□ Buat components/dashboard-editor/PropertyPanel.jsx:
□ Edit warna, judul, tipe chart
□ Setiap perubahan → generate patch
□ File yang dibuat: components/dashboard-editor/PropertyPanel.jsx
Langkah 17.8 — Undo/Redo Bar

□ Buat components/dashboard-editor/UndoRedoBar.jsx:
□ Tombol Ctrl+Z / Ctrl+Y
□ Keyboard shortcut handler
□ File yang dibuat: components/dashboard-editor/UndoRedoBar.jsx
Langkah 17.9 — Update Routing

□ Tambah route /dashboard/:id/edit
□ File yang dibuat: update App.jsx
TAHAP 18: INTEGRASI & TESTING (F-13)
Tujuan: End-to-end verification.

Langkah 18.1 — Integrasi Chat → Patch

□ Planner Agent dikenali intent edit_dashboard
□ Chat route deteksi apakah intent = create atau edit
□ Jika edit → load state → Intent Parser → patch → apply → sync
□ File yang dibuat: update api/routes/chat.py, update agents/planner.py
Langkah 18.2 — Tulis Unit Test F-13

□ test_dashboard_state.py
□ test_patch_model.py
□ test_intent_parser.py
□ test_patch_validator.py
□ test_patch_applier.py
□ test_metabase_adapter.py
□ test_version_control.py
□ test_conflict_detection.py
□ test_preservation.py
□ test_idempotency.py
□ File yang dibuat: 10 file test
Langkah 18.3 — E2E Test F-13

□ test_dashboard_editor_e2e.py:
□ Iterasi 1: generate dashboard
□ Iterasi 2: ADD_CARD
□ Iterasi 3: SWAP_CARDS
□ Iterasi 4: CHANGE_COLOR
□ Iterasi 5: ADD_FILTER
□ Iterasi 6: REMOVE_CARD
□ Iterasi 7: rollback ke v3
□ Verify state akhir = v3
□ File yang dibuat: test/test_dashboard_editor_e2e.py
Langkah 18.4 — Pengujian Manual F-13

□ 12 skenario manual (lihat 9.7)
□ Dokumentasi screenshot
Langkah 18.5 — Optimasi Token

□ Ukur token generate-from-scratch vs patch-based
□ Target: 3x lebih hemat
□ Tuning prompt jika perlu
Langkah 18.6 — Dokumentasi F-13

□ Update README dengan section "Iterative Dashboard Editing"
□ Tambah contoh interaksi
□ Sertakan screenshot before/after
□ Update PRJ
📊 PROGRESS SUMMARY v2 (Dengan F-13)
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
Tahap 11	Dashboard State Model (F-13)	⬜ Belum
Tahap 12	Intent Parser Agent (F-13)	⬜ Belum
Tahap 13	Patch Validator & Applier (F-13)	⬜ Belum
Tahap 14	Metabase Adapter (F-13)	⬜ Belum
Tahap 15	Version Control & Conflict (F-13)	⬜ Belum
Tahap 16	API Routes F-13	⬜ Belum
Tahap 17	Frontend F-13	⬜ Belum
Tahap 18	Integrasi & Testing F-13	⬜ Belum
📌 Cara Menggunakan Addendum Ini
Copy seluruh konten addendum ini.

Letakkan di PRJ_BIthere_v2.md setelah Tahap 10 (bagian akhir dokumen).

Nomor tahap dilanjutkan dari Tahap 10 → Tahap 11 s/d 18.

Nomor FR dilanjutkan dari FR-20 → FR-21 s/d 38.

Nomor NFR dilanjutkan dari NFR-17 → NFR-18 s/d 25.

Update tabel Progress Summary di README utama agar mencakup F-13.

🎯 Kesimpulan F-13
Fitur Iterative Dashboard Editor mengubah cara user berinteraksi dengan dashboard:

Sebelum (v1)	Sesudah (F-13)
Generate ulang seluruh dashboard tiap iterasi	Patch hanya bagian yang diubah
Chart lama bisa hilang saat regenerasi	Semua chart preserved
Filter reset saat iterasi	Filter tetap, bisa ditambah
Biaya token mahal	3–10x lebih hemat
User kehilangan kontrol	User kontrol penuh
Tidak ada versi	Version control + rollback
Tidak ada preview	Live preview before/after
Inilah yang membuat BIthere v2 benar-benar "user friendly" dan "corporate-ready" — bukan hanya bisa query, tapi bisa berkolaborasi iteratif dengan user seperti asisten manusia.

"Ubah hanya yang ingin diubah. Sisanya biarkan apa adanya."

Dokumen ini adalah Addendum F-13 dari PRJ_BIthere_v2.md. Letakkan sebagai bagian akhir dokumen atau sebagai file terpisah PRJ_BIthere_v2_Addendum_F13.md di folder root repository.

