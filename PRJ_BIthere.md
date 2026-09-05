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
│   │   ├── agents/               # LangGraph agents (Planner, Query Gen, dst.)
│   │   ├── api/
│   │   │   ├── routes/           # chat.py, dashboard.py, auth.py, user.py
│   │   │   └── deps.py           # Dependency JWT, role
│   │   ├── connectors/           # Database connectors (PostgreSQL, MySQL, MongoDB)
│   │   ├── core/
│   │   │   ├── config.py         # Settings env
│   │   │   ├── security.py       # JWT verification, role check
│   │   │   └── logging.py
│   │   ├── mcp/
│   │   │   ├── server.py         # MCP tool server
│   │   │   └── tools/            # fetch_data.py, send_slack.py, send_email.py, render_dashboard.py, export_pdf.py
│   │   ├── rag/                  # Pinecone client, embedding, retrieval
│   │   ├── services/             # redis.py, metabase.py, report.py
│   │   ├── models/               # Pydantic schemas (request/response)
│   │   └── main.py               # FastAPI entry point
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/           # Chat, DashboardEmbed, Navbar
│   │   ├── pages/                # Login.jsx, Chat.jsx, Dashboard.jsx, Admin.jsx
│   │   ├── services/             # api.js, auth.js, sse.js
│   │   └── App.jsx
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml            # Backend, frontend, Redis, Metabase
├── .env.example
├── README.md
└── scripts/                      # seed_data.py, setup_pinecone.py, setup_metabase.py

---

> **📌 Catatan:** Bagian ini adalah **Deskripsi Project** dan **Arsitektur Deployment** berdasarkan komponen terbaru. Untuk bagian selanjutnya (Panduan Instalasi, Konfigurasi Environment, Struktur Folder, dan Cara Menjalankan) akan menyusul di update README berikutnya.

---

## 📋 Functional Requirements (Kebutuhan Fungsional)

Berikut adalah daftar lengkap kebutuhan fungsional (FR) yang menjadi acuan pengembangan sistem **BIthere**. Kebutuhan ini dikelompokkan berdasarkan modul/domain untuk memudahkan pelacakan dan pengujian.

---

### 1. Autentikasi & Manajemen User (Multi-User dengan Role)
| ID | Deskripsi |
|----|-----------|
| **FR-01** | Sistem menyediakan endpoint autentikasi menggunakan **Supabase Auth** (email & password). Backend memverifikasi token JWT dari Supabase pada setiap request yang masuk. |
| **FR-02** | Sistem mendukung banyak pengguna dalam satu tim. Tersedia dua **role** utama: <br> • **Admin** → dapat mengelola user (tambah, nonaktifkan, hapus) <br> • **Analyst** → dapat menggunakan fitur analisis (chat, dashboard, laporan) |
| **FR-02a** | Admin dapat menambahkan, menonaktifkan, dan menghapus user melalui endpoint API yang tersedia (atau secara langsung melalui Supabase Dashboard). |
| **FR-02b** | Setiap pengguna memiliki data profil yang tersimpan di tabel `profiles` dengan skema: `id`, `email`, `role`, `created_at`. |
| **FR-02c** | Seluruh endpoint API dilindungi oleh middleware autentikasi. Hanya request dengan token JWT yang valid yang dapat mengakses fitur-fitur BIthere. |

---

### 2. Chat Interface & Natural Language Query (NLQ)
| ID | Deskripsi |
|----|-----------|
| **FR-03** | Frontend (React) menyediakan antarmuka chat dengan input multi-bahasa (Indonesia dan Inggris). |
| **FR-04** | Sistem merespons pertanyaan pengguna secara *streaming* (SSE - Server-Sent Events) dari backend. |
| **FR-05** | Sistem mampu memahami maksud pengguna: apakah berupa permintaan query data, pembuatan visualisasi, atau pembuatan laporan. |

---

### 3. Dynamic Database Connector
| ID | Deskripsi |
|----|-----------|
| **FR-06** | Mendukung koneksi ke PostgreSQL (Supabase) sebagai sumber data utama, serta menyediakan adapter untuk MySQL dan MongoDB. |
| **FR-07** | Menerapkan *abstraction layer* sehingga penambahan konektor database baru tidak mengubah logika inti aplikasi. |
| **FR-08** | Sistem membaca dan menyimpan metadata skema (nama tabel, kolom, tipe data, dan relasi) dari database yang terhubung. |

---

### 4. Metadata Ingestion & RAG (Retrieval-Augmented Generation)
| ID | Deskripsi |
|----|-----------|
| **FR-09** | Modul *ingest* metadata database ke Pinecone (vector DB cloud) untuk kebutuhan RAG. |
| **FR-10** | Menyimpan *embedding* (menggunakan OpenAI text-embedding-3-small) dari nama tabel, kolom, deskripsi, business glossary, dan query historis. |
| **FR-11** | Menerapkan *retrieval hybrid* (semantic + keyword) untuk mendapatkan konteks paling relevan sebelum proses generasi query. |
| **FR-12** | Business glossary dapat ditambahkan secara manual oleh pengguna atau diimpor dari file eksternal. |

---

### 5. Multi-Agent Orchestration (LangGraph)
| ID | Deskripsi |
|----|-----------|
| **FR-13** | **Planner Agent** memecah pertanyaan kompleks menjadi subtask dan menentukan kebutuhan visualisasi/aksi. |
| **FR-14** | **Query Generator Agent** menghasilkan query SQL/NoSQL berdasarkan metadata dan pertanyaan pengguna. |
| **FR-15** | **Validator Agent** memeriksa keamanan query (mencegah perintah DROP, DELETE tanpa WHERE) serta memastikan sintaks benar. |
| **FR-16** | **Query Optimizer Agent** menulis ulang query untuk performa tinggi (memanfaatkan index, partisi, agregasi awal, materialized view). |
| **FR-17** | **Insight Analyzer Agent** merangkum hasil query menjadi insight bisnis yang strategis dan mudah dipahami. |
| **FR-18** | **Dashboard Builder Agent** membuat konfigurasi visualisasi (JSON) dan memanggil Metabase API untuk pembuatan dashboard. |
| **FR-19** | **Report Sender Agent** mengirim laporan ke Slack atau Email sesuai permintaan pengguna. |

---

### 6. Query Execution & Big Data Optimization
| ID | Deskripsi |
|----|-----------|
| **FR-20** | Sistem mengeksekusi query ke database sumber (Supabase PostgreSQL) dengan *timeout* yang dapat dikonfigurasi. |
| **FR-21** | Menyediakan strategi *sampling data* untuk eksplorasi awal pada tabel besar, guna mempercepat respons awal. |
| **FR-22** | Mendukung pre-agregasi dan pemanfaatan *materialized view* untuk query yang sering dijalankan. |
| **FR-23** | Menggunakan `EXPLAIN / ANALYZE` untuk memilih query plan paling efisien sebelum eksekusi. |
| **FR-24** | Menangani hasil query berukuran besar dengan mekanisme paginasi atau agregasi ringkas. |

---

### 7. Caching Layer (Redis)
| ID | Deskripsi |
|----|-----------|
| **FR-25** | Redis (berjalan di Docker lokal) digunakan sebagai penyimpanan cache hasil query dengan mekanisme TTL. |
| **FR-26** | *Cache key* dihitung dari hash kombinasi prompt, parameter query, dan versi skema database. |
| **FR-27** | Menerapkan cache untuk embedding metadata guna menghindari pemanggilan OpenAI API secara berulang. |
| **FR-28** | Menerapkan *semantic cache* untuk respons LLM, sehingga pertanyaan dengan maksud mirip tidak memicu komputasi ulang. |
| **FR-29** | Cache konfigurasi dashboard untuk mencegah regenerasi chart/visualisasi yang sama. |
| **FR-30** | Menyediakan mekanisme invalidasi cache otomatis ketika terjadi perubahan skema database. |

---

### 8. Dashboard Generation & Visualization (Metabase)
| ID | Deskripsi |
|----|-----------|
| **FR-31** | Membuat dashboard baru di Metabase melalui API, dengan layout dan kartu sesuai hasil analisis query. |
| **FR-32** | Membuat kartu visualisasi individual (bar, line, pie, table) dan menambahkannya ke dalam dashboard. |
| **FR-33** | Menghasilkan embed URL untuk dashboard yang ditampilkan di frontend melalui iframe. |
| **FR-34** | Frontend menampilkan dashboard Metabase secara interaktif tanpa pengguna harus meninggalkan halaman chat. |
| **FR-35** | Adapter visualisasi memungkinkan penggantian Metabase ke Apache Superset atau ECharts di masa depan tanpa mengubah logika bisnis. |

---

### 9. Report Generation & Delivery
| ID | Deskripsi |
|----|-----------|
| **FR-36** | Menghasilkan laporan PDF menggunakan WeasyPrint (konversi HTML → PDF) yang berisi insight, tabel ringkas, dan grafik. |
| **FR-37** | Mengirim laporan PDF ke alamat email yang ditentukan (melalui SMTP atau API email). |
| **FR-38** | Mengirim ringkasan insight beserta link dashboard ke Slack (via incoming webhook). |
| **FR-39** | Pengguna dapat meminta laporan dikirim secara otomatis setelah proses analisis selesai dijalankan. |

---

### 10. MCP Server Tools
| ID | Deskripsi |
|----|-----------|
| **FR-40** | MCP server menyediakan tools standar: `fetch_data`, `send_slack`, `send_email`, `render_dashboard`, dan `export_pdf`. |
| **FR-41** | Tools tersebut dapat dipanggil oleh agen secara aman dengan parameter yang telah dibatasi (whitelist parameters). |
| **FR-42** | Menyediakan tool tambahan `notify_webhook` untuk kebutuhan integrasi eksternal (opsional). |

---

### 11. Konfigurasi & Setup Sistem
| ID | Deskripsi |
|----|-----------|
| **FR-43** | Seluruh konfigurasi (Supabase, Pinecone, Groq, OpenAI, Redis, Metabase) diatur melalui file `.env` atau environment variables di Docker. |
| **FR-44** | Docker Compose digunakan untuk mengatur dan menjalankan seluruh layanan lokal: backend, frontend, Redis, dan Metabase. |
| **FR-45** | Direktori `scripts/` menyediakan seed script untuk membuat skema database contoh serta mengisi data dummy (100.000 baris) untuk keperluan pengujian (MVP). |

---