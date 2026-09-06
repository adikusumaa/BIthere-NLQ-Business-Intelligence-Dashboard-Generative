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

## 📊 Skema Data dan Kontrak API

---

### 5.1 Database Sumber (Supabase PostgreSQL – Dataset Fintech/Risk)

Dataset yang digunakan adalah data transaksi kartu kredit dan label fraud yang terdiri dari **5 tabel utama** dengan total **1 juta transaksi**.

| Tabel | Jumlah Baris | Deskripsi |
| :--- | :--- | :--- |
| `users` | 1,219 | Data nasabah (umur, pendapatan, skor kredit, dll.) |
| `cards` | 4,061 | Data kartu kredit/debit yang dimiliki nasabah |
| `mcc_codes` | 109 | Kode MCC (Merchant Category Code) dan deskripsi kategori merchant |
| `transactions` | 1,000,000 | Transaksi kartu (tanggal, jumlah, merchant, lokasi, dll.) |
| `fraud_labels` | 1,000,000 | Label fraud per transaksi (Yes / No) |

---

#### Detail Kolom per Tabel

<details>
<summary><strong>users</strong></summary>

| Kolom | Tipe | Deskripsi |
| :--- | :--- | :--- |
| `id` | integer | Primary key |
| `current_age` | integer | Usia nasabah saat ini |
| `retirement_age` | integer | Usia pensiun |
| `birth_year` | integer | Tahun lahir |
| `birth_month` | integer | Bulan lahir |
| `gender` | text | Jenis kelamin (Male / Female) |
| `address` | text | Alamat lengkap |
| `latitude` | float | Koordinat lintang |
| `longitude` | float | Koordinat bujur |
| `per_capita_income` | float | Pendapatan per kapita daerah |
| `yearly_income` | float | Pendapatan tahunan nasabah |
| `total_debt` | float | Total utang |
| `credit_score` | integer | Skor kredit |
| `num_credit_cards` | integer | Jumlah kartu kredit yang dimiliki |

</details>

<details>
<summary><strong>cards</strong></summary>

| Kolom | Tipe | Deskripsi |
| :--- | :--- | :--- |
| `id` | integer | Primary key |
| `client_id` | integer | Foreign key → `users.id` |
| `card_brand` | text | Brand kartu (Visa, Mastercard, Discover) |
| `card_type` | text | Tipe kartu (Credit / Debit / Prepaid) |
| `credit_limit` | float | Batas kredit |
| `acct_open_date` | date | Tanggal pembukaan akun |
| `card_on_dark_web` | boolean | Status kartu bocor di dark web |

</details>

<details>
<summary><strong>mcc_codes</strong></summary>

| Kolom | Tipe | Deskripsi |
| :--- | :--- | :--- |
| `mcc_code` | integer | Primary key. Kode MCC (contoh: 5812) |
| `description` | text | Deskripsi kategori (contoh: *Eating Places and Restaurants*) |

</details>

<details>
<summary><strong>transactions</strong></summary>

| Kolom | Tipe | Deskripsi |
| :--- | :--- | :--- |
| `id` | integer | Primary key |
| `date` | timestamp | Waktu transaksi |
| `client_id` | integer | Foreign key → `users.id` |
| `card_id` | integer | Foreign key → `cards.id` |
| `amount` | numeric | Jumlah transaksi |
| `use_chip` | text | Metode transaksi (Swipe / Online / Chip) |
| `merchant_id` | integer | ID merchant |
| `merchant_city` | text | Kota merchant |
| `merchant_state` | text | Negara bagian merchant |
| `mcc` | integer | Kode MCC transaksi |
| `errors` | text | Keterangan error (jika ada) |

</details>

<details>
<summary><strong>fraud_labels</strong></summary>

| Kolom | Tipe | Deskripsi |
| :--- | :--- | :--- |
| `id` | integer | Primary key (sama dengan `transactions.id`) |
| `fraud_label` | text | Yes / No |

</details>

> **Catatan:** Join antar tabel dilakukan secara dinamis oleh **Query Generator Agent** berdasarkan permintaan NLQ dari pengguna.

---

### 5.2 Database Aplikasi (Supabase PostgreSQL – Auth & Metadata)

Selain data sumber, BIthere memiliki skema terpisah untuk keperluan autentikasi dan metadata aplikasi.

#### Daftar Tabel Aplikasi

| Tabel | Deskripsi |
| :--- | :--- |
| `profiles` | Menyimpan data user (`id`, `email`, `role`) |
| `query_history` | Riwayat prompt & query yang dihasilkan |
| `dashboard_configs` | Konfigurasi dashboard yang dibuat (termasuk embed URL) |
| `business_glossary` | Istilah bisnis yang didefinisikan manual / otomatis |
| `ingestion_logs` | Log proses ingest metadata ke Pinecone |

---

#### Detail Kolom per Tabel Aplikasi

<details>
<summary><strong>profiles</strong></summary>

| Kolom | Tipe | Deskripsi |
| :--- | :--- | :--- |
| `id` | uuid | Primary key (dari Supabase Auth) |
| `email` | text | Email user |
| `role` | text | `admin` / `analyst` |
| `created_at` | timestamptz | Waktu pembuatan |

</details>

<details>
<summary><strong>query_history</strong></summary>

| Kolom | Tipe | Deskripsi |
| :--- | :--- | :--- |
| `id` | serial | Primary key |
| `user_id` | uuid | Foreign key → `profiles.id` |
| `prompt` | text | Pertanyaan user |
| `generated_query` | text | Query SQL/NoSQL yang dihasilkan |
| `status` | text | `success` / `error` |
| `created_at` | timestamptz | Waktu eksekusi |

</details>

<details>
<summary><strong>dashboard_configs</strong></summary>

| Kolom | Tipe | Deskripsi |
| :--- | :--- | :--- |
| `id` | serial | Primary key |
| `user_id` | uuid | Foreign key → `profiles.id` |
| `metabase_dashboard_id` | integer | ID dashboard di Metabase |
| `config_json` | jsonb | Konfigurasi visualisasi (chart, layout) |
| `embed_url` | text | URL embed Metabase |
| `created_at` | timestamptz | Waktu pembuatan |

</details>

---

### 5.3 Pinecone Index (Vector Database)

| Atribut | Nilai |
| :--- | :--- |
| **Index Name** | `bithere-metadata` |
| **Namespaces** | `schema` (metadata tabel/kolom), `glossary` (istilah bisnis), `query_history` (riwayat prompt) |
| **Embedding Model** | OpenAI `text-embedding-3-small` |
| **Metadata Fields** | `type`, `name`, `table`, `description`, `text`, `embedding` |

---

### 5.4 Redis Cache Keys

| Key Pattern | Tipe Data | TTL | Deskripsi |
| :--- | :--- | :--- | :--- |
| `query:{hash}` | String | 1 jam | Hasil query SQL |
| `llm:{hash}` | String | 1 jam | Respons LLM (semantic cache) |
| `embedding:{hash}` | String | 24 jam | Embedding metadata |
| `dashboard:{id}` | String | 1 jam | Konfigurasi dashboard JSON |
| `metadata:{table}` | String | 6 jam | Cache schema tabel |

> **Invalidasi:** Saat skema berubah atau data signifikan diperbarui, cache dihapus otomatis.

---

### 5.5 Business Glossary (Hybrid)

Metode pengelolaan istilah bisnis:

| Metode | Deskripsi |
| :--- | :--- |
| **Manual Seed Awal** | Istilah penting didefinisikan manual dalam file `scripts/seed_glossary.csv` dan di-embed ke Pinecone namespace `glossary`. Contoh: `fraud`, `chargeback`, `high risk transaction`, `MCC`, `merchant`. |
| **Auto-enrichment** | Setiap kali user mengajukan pertanyaan yang mengandung istilah baru, sistem otomatis menambahkannya ke glossary setelah divalidasi (frekuensi kemunculan > ambang batas). Istilah tersebut di-embed dan disimpan di Pinecone. |
| **Penyimpanan** | Semua istilah disimpan dalam namespace `glossary` di Pinecone dengan metadata: `term`, `definition`, `category`, `created_at`. |

---

## 🔐 API Authentication & Authorization

### Konsep Dasar

BIthere adalah aplikasi internal yang hanya dapat diakses oleh **user terdaftar**. Autentikasi menggunakan **Supabase Auth**. Backend FastAPI hanya memverifikasi token JWT dari Supabase.

---

### 1. Admin Invite User (Register)
[Admin Login] → [Halaman Admin] → [Klik Invite User]

text

| Langkah | Deskripsi |
| :--- | :--- |
| 1 | Frontend mengirim `POST /api/auth/register` dengan body `{ email, role }` |
| 2 | Backend memverifikasi token admin (role = `admin`) |
| 3 | Backend memanggil Supabase Auth Admin API untuk membuat user (email + password sementara) |
| 4 | Backend menyimpan user ke tabel `profiles` (`id`, `email`, `role`) |
| 5 | Backend mengirim respons sukses ke frontend |

---

### 2. User Login
[User Buka Login] → [Input Email & Password]

text

| Langkah | Deskripsi |
| :--- | :--- |
| 1 | Frontend langsung memanggil Supabase Auth `signInWithPassword` (bukan lewat backend) |
| 2 | Supabase memberikan JWT token |
| 3 | Token disimpan di frontend (localStorage / memory) |

---

### 3. Akses Endpoint (Middleware Auth)
[Frontend] → [Header: Authorization: Bearer <token>] → [Backend]

text

| Langkah | Deskripsi |
| :--- | :--- |
| 1 | Setiap request ke backend, frontend kirim header `Authorization: Bearer <token>` |
| 2 | Backend memverifikasi token via Supabase |
| 3 | Jika valid → lanjut proses |
| 4 | Jika tidak valid → kirim error `401 Unauthorized` |

---

### 4. GET /api/auth/me (Get Profile)
[Frontend] → [GET /api/auth/me dengan token] → [Backend]

text

| Langkah | Deskripsi |
| :--- | :--- |
| 1 | Frontend memanggil endpoint `GET /api/auth/me` dengan token |
| 2 | Backend memverifikasi token, mengambil `user_id` |
| 3 | Backend query tabel `profiles` untuk mendapatkan `email` & `role` |
| 4 | Backend mengirim data profil ke frontend |
| 5 | Frontend menampilkan nama/role, mengatur menu sesuai role (`admin` vs `analyst`) |

---

## 🛠️ Standar Konvensi Kode (Coding Standards & Conventions)

---

### 6.1 Standar Umum

| Aspek | Standar |
| :--- | :--- |
| **Backend** | Python 3.10+ |
| **Frontend** | JavaScript (React) dengan JSX |
| **Format Kode** | PEP8 (Python), Prettier (JavaScript/JSX) |
| **Linter** | ESLint (Frontend), Ruff / Flake8 (Backend) |
| **Type Checking** | Pydantic (FastAPI), PropTypes opsional (React) |
| **Penamaan** | `snake_case` (Python), `camelCase` (JavaScript/JSX), `PascalCase` (Komponen React) |
| **Dokumentasi** | Setiap fungsi/method wajib memiliki docstring singkat (Python) atau komentar JSDoc (JS) |
| **Bahasa Komentar** | Indonesia atau Inggris, konsisten per modul |

---

### 6.2 Backend (Python / FastAPI)

#### Struktur Kode

| Aturan | Deskripsi |
| :--- | :--- |
| `__init__.py` | Setiap modul di dalam folder `app/` wajib memiliki file `__init__.py` kosong. |
| **Config** | Konfigurasi environment diakses melalui `app/core/config.py` menggunakan `pydantic-settings`. |
| **Routes** | Semua endpoint didefinisikan di `app/api/routes/`, bukan langsung di `main.py`. |
| **Services** | Logika bisnis diletakkan di `app/services/`, tidak boleh di route. |
| **Models** | Model Pydantic (schema request/response) di `app/models/`. |

#### Penamaan

| Elemen | Format | Contoh |
| :--- | :--- | :--- |
| **File** | `snake_case` | `query_generator.py` |
| **Class** | `PascalCase` | `class QueryGeneratorAgent` |
| **Function / Method** | `snake_case` | `def generate_query()` |
| **Variable** | `snake_case` | `query_result` |
| **Constant** | `UPPER_SNAKE_CASE` | `MAX_QUERY_LENGTH` |

#### Aturan FastAPI

| Aturan | Deskripsi |
| :--- | :--- |
| **Prefix & Tags** | Route file menggunakan `prefix` dan `tags` untuk dokumentasi otomatis di Swagger UI. |
| **Response Model** | Setiap endpoint wajib menentukan `response_model` untuk validasi output. |
| **Error Handling** | Menggunakan `HTTPException` dengan status code yang jelas. |
| **Middleware Auth** | Middleware autentikasi ditaruh di `api/deps.py` dan dipakai via `Depends()`. |

---

### 6.3 Frontend (React + Vite)

#### Struktur Kode

| Aturan | Deskripsi |
| :--- | :--- |
| **Komponen UI** | Komponen reusable di `src/components/`. |
| **Halaman** | Halaman aplikasi di `src/pages/`. |
| **API & SSE** | Pemanggilan API dan SSE stream di `src/services/`. |
| **State Management** | React Context atau Zustand (jika diperlukan). |
| **Styling** | Tailwind CSS (jika disepakati) atau CSS Modules. |

#### Penamaan

| Elemen | Format | Contoh |
| :--- | :--- | :--- |
| **File Komponen** | `PascalCase` | `ChatBox.jsx` |
| **File Utilitas** | `camelCase` | `apiClient.js` |
| **Komponen** | `PascalCase` | `export default function ChatBox()` |
| **Fungsi** | `camelCase` | `fetchChatHistory()` |
| **Konstanta** | `UPPER_SNAKE_CASE` | `API_BASE_URL` |

---

### 6.4 Git & Commit Convention

| Aturan | Deskripsi |
| :--- | :--- |
| **Branch** | `main` (produksi), `dev` (pengembangan), `feature/nama-fitur` (fitur baru). |
| **Commit Message** | Mengikuti format `type: subject` |

#### Format Commit Message

| Type | Contoh |
| :--- | :--- |
| `feat` | `feat: tambah endpoint chat streaming` |
| `fix` | `fix: perbaiki validasi query` |
| `docs` | `docs: update README skema data` |
| `refactor` | `refactor: ubah struktur agent` |
| `chore` | `chore: update dependencies` |
| `test` | `test: tambah unit test query generator` |
| `style` | `style: perbaiki formatting kode` |

#### File yang Tidak Boleh di-Commit

| File / Folder | Keterangan |
| :--- | :--- |
| `.env` | File environment (rahasia) |
| `node_modules/` | Dependensi frontend |
| `__pycache__/` | Cache Python |
| `*.pyc` | Compiled Python |
| `data/*.csv` | Data besar (CSV) |

> **Wajib:** Selalu buat `.env.example` sebagai template konfigurasi.

---

### 6.5 Environment Variables

| Aturan | Deskripsi |
| :--- | :--- |
| **Sumber Konfigurasi** | Semua konfigurasi sensitif (API key, URL, credential) wajib melalui environment variable, bukan hardcoded. |
| **Nama Variabel** | Konsisten dan deskriptif. |

#### Daftar Environment Variables Wajib

| Variabel | Deskripsi |
| :--- | :--- |
| `SUPABASE_URL` | URL Supabase project |
| `SUPABASE_KEY` | Service Role Key Supabase |
| `PINECONE_API_KEY` | API Key Pinecone |
| `OPENAI_API_KEY` | API Key OpenAI |
| `GROQ_API_KEY` | API Key Groq |
| `REDIS_URL` | URL koneksi Redis |
| `METABASE_URL` | URL Metabase |
| `METABASE_USERNAME` | Username Metabase |
| `METABASE_PASSWORD` | Password Metabase |
| `JWT_SECRET` | Secret key untuk JWT |

> **Template:** Semua variabel dicantumkan di `.env.example` dengan komentar singkat.

---

### 6.6 Testing Standards

| Aturan | Deskripsi |
| :--- | :--- |
| **Backend** | `pytest` untuk unit test dan integration test. |
| **Frontend** | `Vitest` + `React Testing Library` (jika ada waktu). |
| **Coverage Minimal** | Auth, query executor, caching, agent orchestration. |
| **Lokasi Test** | File test ditaruh paralel dengan modul, contoh: `test_query_generator.py`. |

#### Contoh Struktur Test

```text
backend/
├── app/
│   ├── agents/
│   │   ├── query_generator.py
│   │   └── test_query_generator.py
│   ├── api/
│   │   ├── routes/
│   │   │   └── auth.py
│   │   └── test_auth.py
│   └── services/
│       ├── cache.py
│       └── test_cache.py

6.7 Logging Standards
Aturan	Deskripsi
Format Log	[PROCESS] detail proses...
Level Log	[INFO], [PROCESS], [SUCCESS], [WARNING], [ERROR]
Dilarang	Penggunaan emoji di dalam log.
Bahasa	Indonesia atau Inggris, konsisten per modul.
Komentar	Dilarang menggunakan # komentar di dalam kode produksi.
Contoh Log yang Benar
python
# ✅ GOOD
print("[PROCESS] Starting data upload to Supabase...")
print("[INFO] Total rows to upload: 1,000,000")
print("[SUCCESS] Upload completed successfully")
print("[ERROR] Failed to connect to database")

# ❌ BAD (tidak boleh pakai emoji)
print("🚀 Starting upload...")
print("✅ Done!")
6.8 Kode yang Bersih (Clean Code)
Prinsip	Deskripsi
No Comments for Obvious Code	Tidak perlu komentar untuk kode yang sudah jelas.
Self-Documenting Code	Nama fungsi dan variabel harus sudah menjelaskan tujuannya.
Function Length	Satu fungsi idealnya tidak lebih dari 20-30 baris.
Single Responsibility	Satu fungsi/class hanya untuk satu tugas.
DRY	Don't Repeat Yourself — hindari duplikasi kode.
Contoh Kode yang Baik
python
# ✅ GOOD - Self-documenting
def generate_sql_query(user_prompt: str, context: dict) -> str:
    """Generate SQL query from natural language prompt using RAG context."""
    validated_prompt = validate_prompt(user_prompt)
    return query_generator.generate(validated_prompt, context)

# ❌ BAD - Butuh komentar karena tidak jelas
def gq(p, c):
    # generate query
    return ...
text

---

## 📌 Cara Menggunakan

1. Copy seluruh konten di atas.
2. Letakkan di `PRJ_BIthere.md` setelah bagian **Skema Data dan Kontrak API**.
3. Sesuaikan heading level (`##` → `###` atau `####`) jika diperlukan.

Sekarang bagian **Coding Standards** sudah rapi, detail, dan profesional! 🚀

=======================================================
=======================================================
## 7. Kebutuhan Non-Fungsional (Non-Functional Requirements)

Kebutuhan non-fungsional mendefinisikan **kriteria kualitas** yang harus dipenuhi oleh sistem BIthere agar dapat dioperasikan secara efektif, aman, dan efisien. Kriteria ini mencakup performa, keamanan, skalabilitas, keandalan, kemudahan penggunaan, dan kemudahan perawatan.

---

### 7.1 Performa (Performance)

#### NFR-01: Latensi Chat Streaming

| Parameter | Target | Metrik Pengukuran |
| :--- | :--- | :--- |
| **Time to First Token (TTFT)** | < 2 detik | Waktu dari user mengetik prompt hingga token pertama muncul di chat. |

**Alasan:**

- Standar UX percakapan AI: user tidak mau menunggu lebih dari 2 detik untuk melihat respons pertama.
- Groq Llama 3.3 70B sangat cepat (inference < 1 detik untuk token pertama), sehingga target 2 detik realistis.
- Angka ini memberi ruang untuk overhead backend, RAG retrieval, dan SSE streaming.

---

#### NFR-02: Latensi Query

| Jenis Query | Target Latensi (tanpa cache) | Target Latensi (dengan cache) | Catatan |
| :--- | :--- | :--- | :--- |
| Query sederhana (1 tabel, filter index) | < 3 detik | < 1 detik | SELECT dengan WHERE pada kolom terindeks |
| Query kompleks (join 2-3 tabel, agregasi) | < 10 detik | < 1 detik | Butuh index, partisi, atau materialized view |

**Alasan:**

- **Dengan cache:** Redis di lokal, akses sangat cepat (< 10 ms). 1 detik sudah sangat longgar, termasuk overhead JSON serialization.
- **Tanpa cache:** Query analitik di PostgreSQL 1 juta baris dengan index yang baik biasanya < 1 detik di cloud. Namun karena harus melewati network + LLM + agent, 5-10 detik realistis.
- Angka ini memaksa kita menerapkan optimasi (index, materialized view, sampling) agar tidak lambat.

**Optimasi yang Wajib Diterapkan:**

| Optimasi | Deskripsi |
| :--- | :--- |
| **Data Modeling** | Menerapkan skema bintang (star schema) atau snowflake untuk memisahkan dimensi dan fakta, mengurangi join tidak perlu. |
| **Indexing** | Index pada kolom yang sering difilter/dijoin (`client_id`, `card_id`, `date`, `mcc`). |
| **Partitioning** | Partisi tabel `transactions` berdasarkan tahun/bulan agar scan lebih sempit. |
| **Materialized View** | Untuk agregasi umum (total transaksi per bulan, per kategori) agar tidak hit tabel mentah. |
| **Query Optimizer Agent** | Wajib menggunakan `EXPLAIN ANALYZE` untuk memastikan query plan efisien. |

---

#### NFR-03: Throughput (Konkurensi)

| Parameter | Target | Metrik Pengukuran |
| :--- | :--- | :--- |
| **Concurrent Users** | Minimal 10 request bersamaan tanpa degradasi | Jumlah request per detik yang dapat ditangani sebelum latensi meningkat > 2x. |

**Alasan:**

- Project MVP dijalankan lokal/docker, bukan production high traffic. 10 concurrent user sudah cukup untuk demo dan simulasi tim kecil.
- Backend FastAPI asynchronous + Redis cache ringan, harusnya mampu >10 request bersamaan di laptop 8GB dengan beban yang sudah dipindah ke cloud.
- Angka 10 memberi target realistis tanpa memaksa optimasi berlebihan.

---

### 7.2 Skalabilitas (Scalability)

#### NFR-04: Arsitektur Modular & Horizontal Scaling

| Parameter | Deskripsi |
| :--- | :--- |
| **Modularitas** | Setiap komponen (backend, Redis, Metabase) dapat di-scale secara horizontal. |
| **Stateless Backend** | Backend dirancang stateless (kecuali session), memungkinkan penambahan instance. |

**Alasan:**

- Komponen berat (LLM, embedding, vector DB) sudah di cloud, komponen lokal bisa di-scale dengan menambah instance jika dibutuhkan.
- Desain modular + stateless backend memungkinkan horizontal scaling.
- Menunjukkan pemahaman system design yang baik.

---

### 7.3 Keamanan (Security)

#### NFR-05: Keamanan Query

| Parameter | Deskripsi |
| :--- | :--- |
| **SQL Injection Prevention** | Validator Agent memastikan query yang dihasilkan aman dari serangan SQL Injection. |
| **Operasi Destruktif** | Mencegah perintah `DROP`, `DELETE` tanpa `WHERE`, `TRUNCATE`, dll. |
| **Allowlist Operasi** | Hanya operasi `SELECT` yang diizinkan dari NLQ. |

**Alasan:**

- NLQ berbahaya karena user bisa tidak sengaja meminta query destruktif.
- Validator Agent + allowlist operasi (`SELECT` only) wajib untuk mencegah kerusakan data.
- JWT dari Supabase Auth memastikan hanya user sah yang bisa akses.

---

#### NFR-06: Keamanan API Key

| Parameter | Deskripsi |
| :--- | :--- |
| **Environment Variable** | Semua secret hanya lewat environment variable, tidak pernah hardcoded. |
| **.gitignore** | File `.env` di .gitignore, sediakan `.env.example` sebagai template. |
| **12-Factor App** | Mengikuti praktik standar 12-factor app untuk konfigurasi. |

**Alasan:**

- Banyak API key: Groq, OpenAI, Pinecone, Supabase. Kebocoran key bisa disalahgunakan.
- Praktik standar 12-factor app: konfigurasi lewat env.

---

### 7.4 Caching & Optimasi

#### NFR-07: Caching

| Parameter | Deskripsi |
| :--- | :--- |
| **Query Result Cache** | Hasil query disimpan di Redis dengan TTL 1 jam. |
| **LLM Response Cache** | Semantic cache untuk pertanyaan identik/mirip. |
| **Embedding Cache** | Cache embedding metadata di Redis untuk hindari panggilan OpenAI berulang. |
| **Invalidasi Otomatis** | Cache dihapus saat skema berubah atau data signifikan diperbarui. |

**Alasan:**

- Tujuan utama project ini: optimasi performa & biaya.
- TTL mencegah cache basi; invalidasi saat skema berubah menjaga akurasi.
- Redis lokal ringan dan cepat.

---

#### NFR-08: Optimasi Token

| Parameter | Deskripsi |
| :--- | :--- |
| **Prompt Compression** | Mengurangi konteks yang tidak relevan sebelum dikirim ke LLM. |
| **Output JSON Terstruktur** | Output yang terstruktur mengurangi token tidak perlu dan memudahkan parsing. |
| **Chunking Metadata** | Metadata di-chunk secara efisien agar tidak overload. |

**Alasan:**

- Token = biaya & latensi. Semakin sedikit token, semakin cepat dan murah.
- Output JSON terstruktur memudahkan parsing dan menurunkan token tidak perlu.

---

#### NFR-09: Optimasi Embedding

| Parameter | Deskripsi |
| :--- | :--- |
| **Model Embedding** | OpenAI `text-embedding-3-small` (efisien, murah, cepat). |
| **Caching** | Embedding di-cache di Redis agar tidak memanggil API berulang. |
| **Batching** | Batch embedding untuk proses ingest agar hemat biaya. |

**Apa itu embedding dalam project ini?**

Embedding adalah representasi vektor dari teks. Di BIthere, embedding dilakukan pada metadata (nama tabel, nama kolom, deskripsi, business glossary, query historis). Tujuannya agar sistem bisa mencari konteks yang relevan saat user bertanya.

**Kenapa perlu vector DB (Pinecone)?**

Saat user bertanya *"Berapa total transaksi fraud bulan lalu?"*, sistem perlu tahu:
- Tabel mana yang berisi fraud? → `fraud_labels`
- Kolom apa yang menyimpan tanggal? → `date` di `transactions`
- Apa itu fraud? → `fraud_label = Yes`

Metadata ini disimpan sebagai embedding di Pinecone. Dengan vector search, sistem bisa menemukan metadata yang paling mirip secara makna, bukan sekadar keyword. Contoh: user bilang *"penipuan"* → sistem tahu itu `fraud_label = Yes`.

**Kenapa memilih model embedding kecil (`text-embedding-3-small`)?**

| Aspek | Keuntungan |
| :--- | :--- |
| **Biaya** | Model small lebih murah per token. |
| **Kecepatan** | Inference lebih cepat, latensi RAG lebih rendah. |
| **Efisiensi Penyimpanan** | Dimensi vektor 1536 (lebih kecil dari 3072), hemat ruang di Pinecone. |
| **Akurasi** | Untuk metadata pendek dan terstruktur (nama tabel/kolom/istilah), perbedaan akurasi dengan model besar tidak signifikan. |

**Kapan embedding dilakukan?**

| Skenario | Waktu Eksekusi |
| :--- | :--- |
| **Ingest metadata pertama kali** | Seed awal (skema tabel, MCC codes, glossary). |
| **Perubahan skema** | Re-ingest setelah ada perubahan struktur tabel. |
| **Penambahan glossary** | Manual (admin) atau auto-enrichment dari query history. |
| **Query historis** | Embedding query yang sering muncul untuk semantic cache. |

> **Catatan:** Embedding **tidak dilakukan** untuk data transaksi (1 juta baris), **hanya untuk metadata**.

---

### 7.5 Observability & Error Handling

#### NFR-10: Observability (Logging)

| Parameter | Deskripsi |
| :--- | :--- |
| **Format Log** | `[PROCESS]`, `[INFO]`, `[SUCCESS]`, `[WARNING]`, `[ERROR]` |
| **Struktur Log** | JSON untuk memudahkan parsing oleh tools monitoring (ELK, Loki). |
| **Cakupan Log** | Setiap request, error, dan pemanggilan MCP tools dicatat. |
| **Dilarang** | Penggunaan emoji di dalam log. |

**Alasan:**

- Di production, debugging tanpa log terstruktur sangat sulit.
- Log JSON mudah diparsing oleh tools monitoring.
- Mencakup log setiap agent & tool call untuk audit.

---

#### NFR-11: Error Handling

| Parameter | Deskripsi |
| :--- | :--- |
| **User-Friendly Error** | Pesan error ditampilkan dengan bahasa yang jelas, tanpa stack trace mentah. |
| **Security** | Hindari kebocoran detail teknis yang bisa dimanfaatkan attacker. |
| **Retry Mechanism** | Sistem memiliki mekanisme retry untuk API eksternal (Groq, OpenAI, Pinecone). |

**Alasan:**

- User bisnis tidak paham stack trace. Pesan harus informatif.
- Hindari kebocoran detail teknis (security).
- Frontend bisa menampilkan pesan error yang bersih.

---

### 7.6 Maintainability & Portability

#### NFR-12: Portability (Docker Compose)

| Parameter | Deskripsi |
| :--- | :--- |
| **Deployment** | Aplikasi dapat dijalankan di lingkungan lokal via Docker Compose. |
| **Konfigurasi** | Cukup clone repo, isi `.env`, jalankan `docker compose up`. |
| **Komponen** | Backend, frontend, Redis, Metabase diorkestrasi dalam satu command. |

**Alasan:**

- Memudahkan evaluator/rekruter menjalankan project.
- Docker Compose mengorkestrasi backend, frontend, Redis, Metabase.
- Cukup clone repo, isi `.env`, `docker compose up`.

---

#### NFR-13: Maintainability (Clean Code)

| Parameter | Deskripsi |
| :--- | :--- |
| **Standar Kode** | Mengikuti PEP8 (Python), Prettier (JS/JSX), ESLint (frontend), Ruff/Flake8 (backend). |
| **Modularitas** | Setiap Agent (Planner, Generator, Validator, Optimizer) sebagai modul terpisah. |
| **Self-Documenting** | Nama fungsi dan variabel menjelaskan tujuannya (tanpa komentar berlebihan). |
| **Single Responsibility** | Satu fungsi/class hanya untuk satu tugas. |
| **DRY** | Don't Repeat Yourself — hindari duplikasi kode. |
| **Function Length** | Satu fungsi idealnya tidak lebih dari 20-30 baris. |

**Alasan:**

- Project portofolio harus mudah dibaca orang lain.
- Modularitas memudahkan penambahan fitur/agent/tool baru.
- Standar coding menunjukkan profesionalitas.

---

#### NFR-14: Kompatibilitas Database

| Parameter | Deskripsi |
| :--- | :--- |
| **Dynamic Connector** | Mendukung PostgreSQL, MySQL, MongoDB melalui abstraction layer. |
| **Abstraction Layer** | Penambahan konektor baru tidak mengubah logika inti aplikasi. |

**Alasan:**

- Persyaratan lowongan menyebut pengalaman SQL & NoSQL.
- Dynamic connector memberi nilai lebih: user bisa ganti sumber data tanpa ubah kode inti.
- Dataset utama pakai PostgreSQL (Supabase), tapi adapter siap untuk lain.

---
NFR-17: Kepatuhan Rate Limit Layanan Eksternal
Usulan: Sistem harus menghormati rate limit dari Groq, Google AI Studio, dan Pinecone dengan menerapkan strategi retry, exponential backoff, dan antrian. Jika limit tercapai, sistem memberi tahu user dengan pesan jelas dan tidak crash.

Alasan:

Groq free tier memiliki batas Request per Minute (RPM) dan Token per Minute (TPM). Model yang kita gunakan (Llama 3.3 70B) kemungkinan juga dibatasi, meskipun tidak muncul di tabel yang kamu kirim (karena tabel itu hanya contoh model yang diizinkan).

Google AI Studio dan Pinecone juga punya rate limit free tier.

Tanpa penanganan, request bisa gagal tiba-tiba, mengganggu UX dan menimbulkan error tidak jelas.

Dengan antrian & backoff, sistem lebih tangguh dan profesional.

Detail implementasi:

Gunakan library tenacity (Python) untuk retry dengan exponential backoff.

Batasi jumlah request bersamaan dari backend ke Groq/embedding API (misal max 5 concurrent).

Ketika rate limit tercapai, kembalikan respons error yang informatif: "Layanan AI sedang sibuk, coba lagi dalam beberapa detik."

Cache harus tetap berfungsi untuk mengurangi panggilan API berulang, sehingga rate limit jarang tercapai.

### 📊 Ringkasan NFR

| ID | NFR | Target Utama |
| :--- | :--- | :--- |
| NFR-01 | Latensi Chat Streaming | < 2 detik (time to first token) |
| NFR-02 | Latensi Query | < 3 detik (sederhana) / < 10 detik (kompleks) |
| NFR-03 | Throughput | 10 concurrent users |
| NFR-04 | Skalabilitas | Modular, horizontal scaling |
| NFR-05 | Keamanan Query | SQL Injection prevention, SELECT only |
| NFR-06 | Keamanan API Key | Environment variable, .gitignore |
| NFR-07 | Caching | Redis, TTL, invalidasi otomatis |
| NFR-08 | Optimasi Token | Prompt compression, output JSON |
| NFR-09 | Optimasi Embedding | text-embedding-3-small, cache, batch |
| NFR-10 | Observability | Logging terstruktur (JSON) |
| NFR-11 | Error Handling | User-friendly error, retry mechanism |
| NFR-12 | Portability | Docker Compose |
| NFR-13 | Maintainability | Clean Code, modular |
| NFR-14 | Kompatibilitas Database | PostgreSQL, MySQL, MongoDB |

---

## 8. Manajemen State atau Alur Logika (State Management / Logic Flow)

Bagian ini menjelaskan bagaimana state/status dikelola di seluruh sistem, dari percakapan, alur agent, cache, hingga frontend.

---

### 8.1 Session Persistence (Redis + Supabase)

| Aspek | Penyimpanan | Alasan |
| :--- | :--- | :--- |
| **Sesi aktif** (percakapan berjalan, state LangGraph) | Redis | Cepat, mendukung TTL, cocok untuk data sementara |
| **Riwayat permanen** (query_history, hasil analisis) | Supabase | Butuh audit, auto-enrichment glossary, dan analisis historis |

**Alur Session ID:**

- Session ID dibuat di frontend saat user mulai chat pertama kali (UUID).
- Semua pesan dan state agent disimpan di Redis dengan key `session:{session_id}` dan TTL 1 jam (dapat diperpanjang jika aktif).
- Saat percakapan selesai, ringkasan/query final disimpan ke Supabase `query_history`.

---

### 8.2 LangGraph State (Redis Checkpoint)

| Aturan | Deskripsi |
| :--- | :--- |
| **Checkpointer** | LangGraph menyimpan state di Redis menggunakan checkpointer. |
| **State Update** | Setiap langkah agent (Planner, Query Generator, dsb.) menulis state terbaru ke Redis. |
| **Resume** | Jika server restart, alur dapat dilanjutkan dari checkpoint terakhir. |
| **TTL** | Checkpoint = 1 jam (cukup untuk MVP, bisa disesuaikan). |

**State berisi:**
prompt, session_id, metadata_context, generated_query, query_result, insight, dashboard_config, final_response


---

### 8.3 Frontend State (Zustand + Local State)

| Jenis State | Tools | Data yang Disimpan |
| :--- | :--- | :--- |
| **Global State** | Zustand | Daftar pesan chat (`messages`), status streaming (`isStreaming`), Session ID aktif (`sessionId`), Info user (`user`), Dashboard URL aktif (`activeDashboardUrl`) |
| **Local State** | useState | Input form chat, Toggle UI kecil (misal show/hide panel) |

**Alasan pakai Zustand:** ringan, mudah sinkronisasi antar komponen (chat bubble, dashboard panel, navbar) tanpa prop drilling.

---

**Alur update streaming di frontend:**

| Langkah | Aksi |
| :--- | :--- |
| 1 | User kirim prompt → tambah pesan user ke `messages` |
| 2 | Set `isStreaming = true` |
| 3 | Buka koneksi SSE ke `/api/chat` |
| 4 | Setiap event `token` diterima → append token ke pesan AI terakhir |
| 5 | Event `dashboard` diterima → simpan `embedUrl` ke `activeDashboardUrl` |
| 6 | Event `insight` diterima → tampilkan insight di pesan AI |
| 7 | Event `error` → tampilkan pesan error, set `isStreaming = false` |
| 8 | Saat stream selesai → set `isStreaming = false`, simpan sesi ke Supabase |

---

### 8.4 Alur Agent (Linear)

Untuk MVP, alur agent berjalan **berurutan** (tidak paralel). Ini lebih mudah di-debug dan cukup untuk kebutuhan demo.

| Langkah | Agent / Proses | Input | Output |
| :--- | :--- | :--- | :--- |
| 1 | **Planner Agent** | Prompt user + session state | Maksud, kebutuhan visualisasi/aksi |
| 2 | **RAG Retrieval** | Maksud + session | Konteks metadata relevan (dari Pinecone) |
| 3 | **Cache Check** | Prompt + metadata | Cache hit/miss |
| 4 | **Query Generator** (jika miss) | Metadata + prompt | Query SQL |
| 5 | **Validator Agent** | Query | Query aman atau tolak |
| 6 | **Query Optimizer** | Query tervalidasi | Query dioptimalkan |
| 7 | **Query Executor** | Query final | Hasil data |
| 8 | **Insight Analyzer** | Hasil data + prompt | Insight teks |
| 9 | **Dashboard Builder** (jika diminta) | Hasil data + konfigurasi | Dashboard URL |
| 10 | **Report Sender** (jika diminta) | Insight + dashboard URL | Laporan terkirim |
| 11 | **Response Builder** | Semua output | Stream final ke user |

**Catatan:**

- Jika **cache hit** pada langkah 3, langkah 4–7 dilewati, langsung ke Insight Analyzer.
- Atau langsung kirim respons jika respons final juga di-cache.

---

### 8.5 Cache Flow

**Titik pengecekan cache:** setelah RAG Retrieval dan sebelum Query Generator.

| Kondisi | Aksi |
| :--- | :--- |
| **Cache hit penuh** (ada respons final) | Kirim langsung respons dari cache, tanpa query/insight ulang |
| **Cache hit query result** (tanpa insight) | Ambil hasil query dari cache, lanjut ke Insight Analyzer |
| **Cache miss** | Generate query, eksekusi, simpan query result + insight ke Redis |

**Cache Keys:**

| Key Pattern | Isi |
| :--- | :--- |
| `query:{hash}` | Hasil query |
| `llm:{hash}` | Respons LLM |
| `embedding:{hash}` | Embedding metadata |
| `dashboard:{id}` | Konfigurasi dashboard |
| `session:{session_id}` | State percakapan aktif |

**Invalidasi Cache:**

| Mekanisme | Deskripsi |
| :--- | :--- |
| **TTL Otomatis** | 1 jam untuk query/LLM, 24 jam untuk embedding |
| **Manual / Otomatis** | Saat skema database berubah → hapus cache `metadata:*` dan `query:*` |

---

## 9. Instruksi Eksekusi dan Pengujian (Setup & Testing Instructions)

---

### 9.1 Struktur Folder Test

```text
test/
├── test_auth.py              # Autentikasi JWT & role
├── test_query_generator.py   # NLQ → SQL
├── test_validator.py         # Keamanan query
├── test_optimizer.py         # Optimasi query
├── test_rag_retrieval.py     # Retrieval metadata Pinecone
├── test_caching.py           # Redis cache
├── test_dashboard.py         # Pembuatan dashboard Metabase
├── test_report.py            # Kirim laporan PDF/Slack/Email
├── test_chat_e2e.py          # Alur chat end-to-end
└── test_mcp_tools.py         # MCP tools langsung
9.2 Cara Menjalankan Test
Aktifkan environment

Pastikan semua environment variable di .env sudah terisi.

Jalankan semua test

bash
pytest test/
Jalankan test spesifik

bash
pytest test/test_query_generator.py
Jalankan test dengan output detail

bash
pytest test/ -v -s
Catatan:

Test akan memanggil API eksternal nyata. Pastikan kuota & rate limit masih tersedia.

Untuk test_chat_e2e.py, disarankan jalankan saat internet stabil.

Jika ingin menguji ulang satu fitur, cukup jalankan file test fitur tersebut.

9.3 Daftar Test (Fungsional)
File Test	Yang Diuji	Skenario Utama
test_auth.py	Register, login, me	Admin invite user → user login → ambil profil
test_query_generator.py	NLQ ke SQL	Input pertanyaan → output query SQL sesuai skema
test_validator.py	Keamanan query	Tolak DROP, DELETE tanpa WHERE; izinkan SELECT
test_optimizer.py	Optimasi query	Query kompleks dioptimalkan (indeks, agregasi)
test_rag_retrieval.py	RAG metadata	Ambil konteks metadata relevan dari Pinecone
test_caching.py	Redis cache	Simpan & ambil query result, TTL berjalan
test_dashboard.py	Metabase	Buat dashboard/card dari hasil query
test_report.py	Report delivery	Generate PDF & kirim ke Slack/Email
test_chat_e2e.py	Alur penuh	Prompt → streaming → jawaban + dashboard
test_mcp_tools.py	MCP tools	Panggil semua tools (fetch_data, send_slack, dll.)
9.4 Pengujian Manual
Untuk fitur yang belum masuk test otomatis, gunakan langkah manual:

Login → buka frontend, masukkan email/password, pastikan masuk.

Chat NLQ → tanyakan "Berapa total transaksi fraud bulan lalu?", lihat streaming.

Dashboard → minta "Tampilkan dashboard fraud per bulan", lihat embed Metabase.

Kirim laporan → minta kirim ke Slack/Email, cek terkirim.

Cache → ulangi pertanyaan sama, pastikan respons lebih cepat.

text

---

## 📌 Cara Menggunakan

1. Copy seluruh konten di atas.
2. Letakkan di `PRJ_BIthere.md` sebagai **Poin 9** (setelah bagian **Manajemen State atau Alur Logika**).
3. Sesuaikan heading level (`##` → `###` atau `####`) jika diperlukan.

Sekarang bagian **Instruksi Eksekusi dan Pengujian** sudah rapi, terstruktur, dan mudah dibaca tanpa mengubah makna atau menambahkan kata-kata baru. 🚀



=================================================
LAGNKAH 
===================================================

TAHAP 1: PERSIAPAN DAN FONDASI PROYEK
Tujuan: Menyiapkan struktur dasar, environment, dan layanan eksternal agar siap digunakan.

Langkah 1.1 — Inisialisasi Repository dan Struktur Folder
□ Buat repository Git lokal dengan nama bithere
□ Buat struktur folder utama sesuai kesepakatan:
□ backend/
□ frontend/
□ scripts/
□ test/
□ docker-compose.yml
□ .env.example
□ README.md
□ .gitignore
□ Inisialisasi Git: git init, buat branch main dan dev
□ File yang dibuat: seluruh folder kosong, .gitignore (isi: .env, __pycache__/, node_modules/, *.pyc, data/*.csv)
Langkah 1.2 — Menyiapkan Environment Variables (.env.example)
□ Buat template environment dengan variabel yang sudah ditentukan:
Variabel	Deskripsi
SUPABASE_URL	URL project Supabase
SUPABASE_ANON_KEY	Anon key Supabase (untuk frontend auth)
SUPABASE_SERVICE_ROLE_KEY	Service role key (untuk admin API, jangan di-expose)
PINECONE_API_KEY	API key Pinecone
PINECONE_ENVIRONMENT	Environment Pinecone (misal gcp-starter)
PINECONE_INDEX_NAME	Nama index, bithere-metadata
GROQ_API_KEY	API key Groq
GOOGLE_API_KEY	API key Google AI Studio
REDIS_URL	URL Redis lokal, misal redis://localhost:6379/0
METABASE_URL	URL Metabase, misal http://localhost:3000
METABASE_USERNAME	Email admin Metabase
METABASE_PASSWORD	Password admin Metabase
JWT_SECRET	Secret untuk verifikasi JWT (dari Supabase)
SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD	Kredensial email untuk kirim laporan
SLACK_WEBHOOK_URL	Incoming webhook Slack
□ Tambahkan juga variabel TEST_MODE (default live)
□ File yang dibuat: .env.example
Langkah 1.3 — Setup Docker Compose untuk Layanan Lokal
□ Buat docker-compose.yml yang mendefinisikan service:
□ redis: image redis:alpine, port 6379, volume untuk persistensi
□ metabase: image metabase/metabase:latest, port 3000, environment MB_DB_FILE=/metabase-data/metabase.db, volume
□ backend: build dari backend/Dockerfile, port 8000, env_file .env, depends_on redis
□ frontend: build dari frontend/Dockerfile, port 5173 (Vite), depends_on backend
□ File yang dibuat: docker-compose.yml
Langkah 1.4 — Setup Supabase
□ Buka dashboard Supabase, buat project baru (jika belum ada)
□ Catat URL, anon key, dan service role key
□ Jalankan script SQL untuk membuat tabel aplikasi (profiles, query_history, dashboard_configs, business_glossary, ingestion_logs) di schema public
□ Pastikan dataset sumber (users, cards, mcc_codes, transactions, fraud_labels) sudah ter-load (1 juta transaksi)
□ Buat user admin pertama melalui Supabase Auth
□ File yang dibuat: scripts/setup_supabase.sql (berisi DDL tabel aplikasi)
Langkah 1.5 — Setup Pinecone
□ Buat akun Pinecone, dapatkan API key dan environment
□ Buat index baru:
Nama: bithere-metadata

Dimensions: 768 (embedding Google text-embedding-004)

Metric: cosine

□ Catat index name
□ File yang dibuat: tidak ada file, cukup konfigurasi di dashboard
Langkah 1.6 — Setup Groq dan Google AI Studio
□ Dapatkan API key Groq dari console GroqCloud
□ Dapatkan API key Google AI Studio dari Google AI Studio
□ Simpan keduanya di .env
TAHAP 2: BACKEND CORE
Tujuan: Membangun kerangka backend FastAPI, konfigurasi, autentikasi, dan koneksi database.

Langkah 2.1 — Buat Aplikasi FastAPI Dasar
□ Buat backend/app/main.py dengan FastAPI app, tambahkan CORS, dan root endpoint
□ Buat backend/app/core/config.py menggunakan pydantic-settings untuk membaca semua env
□ Buat backend/app/core/logging.py untuk logging standar [PROCESS], [INFO], dll
□ File yang dibuat: main.py, core/config.py, core/logging.py
Langkah 2.2 — Setup Supabase Auth Middleware
□ Buat backend/app/core/security.py berisi:
□ Verifikasi JWT dari Supabase menggunakan SUPABASE_URL dan JWT_SECRET
□ Dependency get_current_user untuk FastAPI
□ Dependency require_role(role) untuk cek admin/analyst
□ Implementasikan endpoint /api/auth/me yang mengembalikan profil user dari tabel profiles
□ File yang dibuat: core/security.py, api/routes/auth.py, api/deps.py
Langkah 2.3 — Implementasi Database Connectors
□ Buat abstract base class BaseConnector di app/connectors/base.py
□ Buat PostgresConnector (menggunakan asyncpg atau psycopg2) untuk koneksi ke Supabase
□ Buat MySQLConnector dan MongoDBConnector sebagai stub / implementasi dasar
□ Tambahkan factory function get_connector(db_type) untuk memilih konektor berdasarkan env
□ File yang dibuat: connectors/base.py, connectors/postgres.py, connectors/mysql.py, connectors/mongodb.py, connectors/__init__.py
Langkah 2.4 — Setup Redis Cache Service
□ Buat app/services/cache.py dengan class RedisCache:
□ get(key), set(key, value, ttl), delete(pattern)
□ Gunakan redis.asyncio untuk operasi async
□ Inisialisasi koneksi Redis dari REDIS_URL
□ File yang dibuat: services/cache.py
TAHAP 3: RAG DAN EMBEDDING
Tujuan: Mengimplementasikan komponen Retrieval-Augmented Generation untuk metadata dan business glossary.

Langkah 3.1 — Embedding Client (Google AI Studio)
□ Buat app/rag/embedding.py berisi fungsi embed_text(text: str) -> list[float] yang memanggil Google AI Studio embedding API (text-embedding-004)
□ Tambahkan caching embedding dengan Redis (key embedding:{hash})
□ File yang dibuat: rag/embedding.py
Langkah 3.2 — Pinecone Client
□ Buat app/rag/pinecone_client.py berisi class untuk:
□ upsert(vectors, namespace)
□ query(vector, namespace, top_k)
□ delete(namespace)
□ Inisialisasi koneksi Pinecone dari env
□ File yang dibuat: rag/pinecone_client.py
Langkah 3.3 — Metadata Ingestion Script
□ Buat scripts/ingest_metadata.py yang:
□ Membaca skema database dari Supabase (tabel, kolom, tipe data)
□ Menggabungkan dengan business glossary manual (scripts/seed_glossary.csv)
□ Membuat embedding untuk setiap metadata menggunakan Google AI Studio
□ Menyimpan ke Pinecone namespace schema dan glossary
□ Buat scripts/seed_glossary.csv berisi istilah: fraud, chargeback, high risk transaction, MCC, merchant, dll. dengan definisi singkat
□ File yang dibuat: scripts/ingest_metadata.py, scripts/seed_glossary.csv
TAHAP 4: AGENT ORCHESTRATION (LANGGRAPH)
Tujuan: Membangun multi-agent system dengan LangGraph dan Groq LLM.

Langkah 4.1 — Setup Groq LLM Client
□ Buat app/agents/llm.py berisi fungsi untuk memanggil Groq API (Llama 3.3 70B) dengan dukungan streaming
□ Implementasikan fungsi generate_chat(messages) dan stream_chat(messages)
□ File yang dibuat: agents/llm.py
Langkah 4.2 — Planner Agent
□ Buat app/agents/planner.py:
□ Menerima prompt user dan session state
□ Menggunakan LLM untuk menentukan intent (query data, buat dashboard, kirim laporan, atau kombinasi)
□ Output: JSON berisi intent, entities, filters, needs_dashboard, needs_report
□ File yang dibuat: agents/planner.py
Langkah 4.3 — Query Generator Agent
□ Buat app/agents/query_generator.py:
□ Menerima prompt, metadata context dari RAG, dan dialek SQL (PostgreSQL)
□ Menggunakan LLM untuk generate SQL query yang aman (SELECT only)
□ Output: string SQL
□ File yang dibuat: agents/query_generator.py
Langkah 4.4 — Validator Agent
□ Buat app/agents/validator.py:
□ Menerima SQL query
□ Cek blacklist kata (DROP, DELETE, TRUNCATE, UPDATE, dll.) dan pastikan query dimulai dengan SELECT
□ Jika tidak aman, raise error
□ File yang dibuat: agents/validator.py
Langkah 4.5 — Query Optimizer Agent
□ Buat app/agents/optimizer.py:
□ Menerima SQL query
□ Gunakan EXPLAIN ANALYZE (jika memungkinkan) atau heuristik untuk menyarankan optimasi
□ Terapkan optimasi sederhana: pastikan filter pada kolom terindeks, tambahkan LIMIT jika belum ada untuk query eksplorasi
□ File yang dibuat: agents/optimizer.py
Langkah 4.6 — Insight Analyzer Agent
□ Buat app/agents/insight_analyzer.py:
□ Menerima hasil query (list of dict) dan prompt user
□ Menggunakan LLM untuk merangkum hasil menjadi insight bisnis dalam bahasa alami
□ File yang dibuat: agents/insight_analyzer.py
Langkah 4.7 — Dashboard Builder Agent
□ Buat app/agents/dashboard_builder.py:
□ Menerima hasil query dan konfigurasi visual yang diinginkan
□ Membuat JSON konfigurasi (chart type, x/y axis)
□ Memanggil Metabase API melalui services/metabase.py untuk membuat dashboard
□ Mengembalikan embed URL
□ File yang dibuat: agents/dashboard_builder.py, services/metabase.py
Langkah 4.8 — Report Sender Agent
□ Buat app/agents/report_sender.py:
□ Menerima insight text, dashboard URL, dan tujuan (Slack/Email)
□ Memanggil tools MCP send_slack, send_email, atau export_pdf
□ Mengembalikan status terkirim
□ File yang dibuat: agents/report_sender.py
Langkah 4.9 — LangGraph Orchestration
□ Buat app/agents/graph.py:
□ Definisikan state schema (AgentState) berisi semua field yang dibutuhkan
□ Buat node untuk setiap agent dan hubungkan sesuai alur linear
□ Tambahkan Redis checkpointer
□ Ekspor compile_graph() untuk dipakai di endpoint
□ File yang dibuat: agents/graph.py
TAHAP 5: MCP SERVER DAN TOOLS
Tujuan: Menyediakan tools eksternal yang dapat dipanggil oleh agent.

Langkah 5.1 — Implementasi MCP Tools
□ Buat folder app/mcp/tools/ dengan file:
□ fetch_data.py → menjalankan query via database connector
□ send_slack.py → mengirim pesan ke Slack webhook
□ send_email.py → mengirim email via SMTP
□ render_dashboard.py → memanggil Metabase API
□ export_pdf.py → generate PDF menggunakan WeasyPrint
□ Setiap tool berupa fungsi Python dengan dekorasi/registrasi
□ File yang dibuat: mcp/tools/*.py
Langkah 5.2 — MCP Server
□ Buat app/mcp/server.py menggunakan library mcp (atau FastAPI terpisah) untuk mengekspos tools
□ Daftarkan semua tools di atas
□ File yang dibuat: mcp/server.py
TAHAP 6: API ROUTES
Tujuan: Menghubungkan frontend dengan backend.

Langkah 6.1 — Auth Routes
□ POST /api/auth/register (admin only) untuk invite user
□ GET /api/auth/me untuk profil user
□ File yang dibuat: api/routes/auth.py
Langkah 6.2 — Chat Route (SSE)
□ POST /api/chat → menerima message dan session_id, menjalankan LangGraph, dan mengirim event streaming via SSE
□ GET /api/chat/history?session_id= → riwayat percakapan dari Redis/Supabase
□ File yang dibuat: api/routes/chat.py
Langkah 6.3 — Dashboard Routes
□ POST /api/dashboard → membuat dashboard dari hasil query
□ GET /api/dashboard → list dashboard user
□ DELETE /api/dashboard/{id} → hapus dashboard
□ File yang dibuat: api/routes/dashboard.py
Langkah 6.4 — Report Routes
□ POST /api/report → generate PDF dan/atau kirim laporan
□ File yang dibuat: api/routes/report.py
Langkah 6.5 — Users Routes (Admin)
□ GET /api/users, POST /api/users, PUT /api/users/{id}, DELETE /api/users/{id}
□ File yang dibuat: api/routes/users.py
TAHAP 7: FRONTEND (REACT + VITE)
Tujuan: Membangun antarmuka pengguna untuk chat, login, dashboard, dan admin.

Langkah 7.1 — Setup React App
□ Inisialisasi project React dengan Vite di folder frontend/
□ Install dependencies: react-router-dom, zustand, axios/fetch, @supabase/supabase-js
□ Buat struktur folder sesuai kesepakatan
□ File yang dibuat: frontend/package.json, vite.config.js
Langkah 7.2 — Implementasi Auth Flow
□ Buat halaman Login.jsx
□ Integrasikan Supabase Auth (signInWithPassword) langsung di frontend
□ Simpan token di localStorage/Zustand
□ Buat AuthContext atau gunakan Zustand store untuk user state
□ Buat route guard untuk redirect jika belum login
□ File yang dibuat: pages/Login.jsx, services/auth.js, store/authStore.js
Langkah 7.3 — Implementasi Chat Interface
□ Buat halaman Chat.jsx dengan komponen ChatBox, MessageList, MessageBubble
□ Gunakan Zustand untuk menyimpan daftar pesan dan status streaming
□ Implementasikan SSE client (services/sse.js) untuk menerima event dari backend
□ Tampilkan token streaming secara real-time
□ File yang dibuat: pages/Chat.jsx, components/ChatBox.jsx, components/MessageList.jsx, services/sse.js
Langkah 7.4 — Dashboard Embed
□ Buat halaman Dashboard.jsx atau panel di halaman chat untuk menampilkan iframe
□ Saat event dashboard diterima, simpan embed URL dan tampilkan di iframe
□ File yang dibuat: pages/Dashboard.jsx, components/DashboardEmbed.jsx
Langkah 7.5 — Admin Page
□ Buat halaman Admin.jsx dengan daftar user dan tombol invite
□ Panggil API /api/users untuk manajemen user
□ File yang dibuat: pages/Admin.jsx
Langkah 7.6 — Routing dan Navigasi
□ Setup React Router dengan route: /login, /chat, /dashboard, /admin
□ Tambahkan navbar/menu yang menyesuaikan role
□ File yang dibuat: App.jsx
TAHAP 8: INTEGRASI END-TO-END
Tujuan: Menghubungkan semua komponen dan memastikan alur berjalan.

Langkah 8.1 — Alur Chat End-to-End
□ Dari frontend, user mengetik prompt
□ Backend memanggil LangGraph, menjalankan agent, dan streaming response
□ Cache dan MCP tools aktif
□ Dashboard dan laporan terkirim
□ Pengujian manual: lakukan percakapan untuk memvalidasi
Langkah 8.2 — Docker Compose Final
□ Pastikan semua service di docker-compose.yml berjalan
□ Tambahkan network dan depends_on yang benar
□ Uji docker compose up dari nol
TAHAP 9: TESTING
Tujuan: Memastikan setiap fitur berfungsi dan tidak ada bug.

Langkah 9.1 — Tulis Unit Test
□ test_auth.py
□ test_query_generator.py
□ test_validator.py
□ test_optimizer.py
□ test_rag_retrieval.py
□ test_caching.py
□ test_dashboard.py
□ test_report.py
□ test_chat_e2e.py
□ test_mcp_tools.py
Langkah 9.2 — Jalankan Test
□ Jalankan pytest test/ dan perbaiki error hingga semua lolos
TAHAP 10: FINALISASI DAN DOKUMENTASI
Tujuan: Menyempurnakan dokumentasi, README, dan persiapan portofolio.

Langkah 10.1 — Update README
□ Lengkapi PRJ README dengan semua bagian 1–9
□ Tambahkan bagian Roadmap Implementasi ini
□ Sertakan cara menjalankan, testing, dan screenshot (jika ada)
Langkah 10.2 — Optimasi dan Review
□ Review NFR: pastikan latensi, caching, rate limit terpenuhi
□ Lakukan profiling query dan optimasi jika perlu
□ Bersihkan kode, hapus komentar tidak perlu, pastikan standar
Langkah 10.3 — Commit Final
□ Push ke GitHub (buat repository remote)
□ Buat branch main dengan versi stabil
📊 PROGRESS SUMMARY
Tahap	Deskripsi	Status
Tahap 1	Persiapan dan Fondasi Proyek	⬜ Belum
Tahap 2	Backend Core	⬜ Belum
Tahap 3	RAG dan Embedding	⬜ Belum
Tahap 4	Agent Orchestration (LangGraph)	⬜ Belum
Tahap 5	MCP Server dan Tools	⬜ Belum
Tahap 6	API Routes	⬜ Belum
Tahap 7	Frontend (React + Vite)	⬜ Belum
Tahap 8	Integrasi End-to-End	⬜ Belum
Tahap 9	Testing	⬜ Belum
Tahap 10	Finalisasi dan Dokumentasi	⬜ Belum
📌 Cara Menggunakan Checklist Ini
Tandai setiap langkah yang sudah selesai dengan mengubah [ ] menjadi [x].

Update progres secara berkala saat kamu menyelesaikan setiap task.

Gunakan sebagai panduan untuk memastikan tidak ada langkah yang terlewat.

🚀 STATUS PROYEK SAAT INI
Berdasarkan pengerjaan yang sudah dilakukan:

Tahap 1:

☑ Langkah 1.1 — Inisialisasi Repository dan Struktur Folder
☑ Langkah 1.2 — Menyiapkan Environment Variables (.env.example)
☑ Langkah 1.3 — Setup Docker Compose untuk Layanan Lokal
☑ Langkah 1.4 — Setup Supabase (termasuk dataset 1 juta transaksi)
☑ Langkah 1.5 — Setup Pinecone
☑ Langkah 1.6 — Setup Groq dan Google AI Studio
Selanjutnya → Tahap 2: Backend Core (Langkah 2.1 - 2.4)