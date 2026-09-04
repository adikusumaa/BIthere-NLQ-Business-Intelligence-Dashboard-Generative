BIthere

AI Business Intelligence Analyst (NLQ + Auto-Dashboard + Actionable Insights + Caching + Query Optimization)
Nama Project
AI Business Intelligence Analyst — Platform analisis data berbasis bahasa natural dengan kemampuan auto-dashboard, rekomendasi aksi, optimasi caching, dan optimasi query untuk big data.

Tujuan & Keunggulan
Natural Language Query (NLQ)
Pengguna non-teknis dapat mengajukan pertanyaan bisnis dalam bahasa Indonesia/Inggris biasa, tanpa perlu menulis SQL atau memahami struktur database. Contoh: "Berapa total penjualan per kategori bulan lalu?" atau "Tunjukkan tren stok barang yang hampir habis di gudang Jakarta."

Dynamic Database Connector
Mendukung berbagai sumber data, baik SQL (PostgreSQL, MySQL) maupun NoSQL (MongoDB). Arsitektur menggunakan abstraction layer sehingga penambahan konektor baru tidak mengubah logika inti.

Multi-Agent Orchestration (LangChain/LangGraph)
Sistem terdiri dari beberapa agent yang bekerja sama:

Planner Agent → memahami maksud pertanyaan, memecah menjadi subtask.

Query Generator Agent → menghasilkan query SQL/NoSQL sesuai skema.

Validator Agent → memeriksa keamanan dan sintaks query.

Query Optimizer Agent → menulis ulang query untuk efisiensi (index, partisi, agregasi).

Insight Analyzer Agent → merangkum hasil data menjadi insight bisnis.

Dashboard Builder Agent → membuat konfigurasi dashboard (JSON) dan memanggil Metabase API.

Report Sender Agent → mengirim laporan/insight ke Slack atau Email melalui MCP tools.

RAG (Retrieval-Augmented Generation) untuk Metadata & Business Glossary

Vector database menyimpan embedding dari: skema tabel/koleksi, deskripsi kolom, query historis, dan istilah bisnis.

Retrieval hybrid (semantic + keyword) untuk menemukan konteks relevan sebelum query digenerate.

Meningkatkan akurasi NLQ terhadap struktur database yang kompleks.

Auto-Dashboard dengan Metabase

Dashboard Builder Agent menghasilkan konfigurasi visualisasi (chart, filter, layout) dalam format JSON.

Backend memanggil Metabase API untuk membuat dashboard/card secara otomatis.

Frontend menampilkan dashboard melalui embed URL/iframe.

Adapter visualisasi memungkinkan pergantian ke Apache Superset atau ECharts tanpa mengubah logika inti.

Optimasi Embedding & Token

Pengujian beberapa model embedding (text-embedding-3-small, bge, dsb.) untuk akurasi retrieval metadata.

Token reduction: output JSON terstruktur, prompt compression, caching query & insight, chunking metadata yang efisien.

Optimasi Caching (Komponen Penting untuk Big Data)

Query Result Cache → Simpan hasil query ke Redis untuk pertanyaan yang sama/berulang. Key: hash dari prompt + parameter query + versi skema.

Embedding Cache → Cache embedding metadata/tabel/istilah agar tidak hit API LLM berkali-kali.

LLM Response Cache → Cache jawaban akhir untuk pertanyaan yang identik (semantic cache).

Dashboard Config Cache → Simpan konfigurasi JSON dashboard yang sudah dibuat, hindari regenerate.

Metadata Cache → Cache schema database & business glossary di Redis untuk akses cepat.

Tools: Redis sebagai cache utama, TTL untuk invalidasi berkala, dan mekanisme cache invalidation saat ada perubahan skema/data.

Optimasi Performa Query untuk Big Data

Indexing & Partitioning → Memanfaatkan index pada kolom yang sering difilter, partisi tabel berdasarkan waktu/kategori untuk mengurangi scan data.

Materialized Views & Pre-agregasi → Membuat ringkasan data (agregat) yang sering diakses agar query tidak memproses data mentah setiap saat.

Query Rewriting → Agent Optimizer menulis ulang query dengan EXPLAIN/ANALYZE untuk memilih join order, filter pushdown, dan agregasi awal.

OLAP Engine → Opsional: menggunakan engine analitik kolom (ClickHouse, DuckDB) untuk query cepat pada data besar.

Sampling Data → Untuk eksplorasi awal, gunakan sampling agar hasil cepat, kemudian query penuh jika diminta.

Incremental Caching → Cache hasil query yang sering dipakai dan perbarui secara bertahap saat data berubah.

MCP Server untuk Integrasi Eksternal

Menyediakan tools seperti: send_slack, send_email, render_dashboard, fetch_data.

Memungkinkan agent memanggil layanan eksternal secara aman dan terkontrol.

Frontend Chat + Dashboard

Aplikasi web (React/Vue) dengan antarmuka chat untuk NLQ.

Panel dashboard terpisah untuk menampilkan hasil visual dari Metabase.

Dukungan streaming response untuk pengalaman interaktif.

Cloud-Ready & Scalable

Backend menggunakan FastAPI, containerized dengan Docker.

Siap deploy ke Azure/AWS/GCP.

Arsitektur modular memungkinkan scaling per komponen.

Alur Kerja Singkat
Pengguna mengetik pertanyaan di chat.

Planner Agent menganalisis maksud dan kebutuhan visualisasi.

RAG mencari metadata relevan (tabel, kolom, istilah).

Cek cache: jika query serupa pernah dijalankan, ambil hasil dari Redis.

Jika tidak ada cache, Query Generator membuat query, Validator memastikan keamanan, dan Query Optimizer menulis ulang untuk performa (index, partisi, pre-agregasi).

Data dieksekusi dari sumber database (besar/kecil) dengan strategi optimal (materialized view, sampling, OLAP).

Insight Analyzer merangkum hasil menjadi insight.

Jika perlu visual, Dashboard Builder membuat dashboard di Metabase (atau ambil dari cache jika sudah ada).

Jika diminta, Report Sender mengirim laporan ke Slack/Email.

Jawaban dan/atau dashboard ditampilkan ke pengguna.

Cakupan Persyaratan Lowongan
Project ini mencakup hampir semua kebutuhan dari lowongan EY AI Engineer dan Bukalapak Junior AI Engineer, antara lain:

Natural Language Query (NLQ) agent

Agentic AI workflows

Pengembangan frontend chat & dashboard

Integrasi AI dengan data platform & API

Penggunaan LLM, RAG, embedding, vector search

Cloud deployment, containerization, FastAPI

MCP, LangChain/LangGraph, optimasi token

Visualisasi data & pelaporan

Optimasi caching dan performa query untuk big data (nilai tambah)



Nama: AI Business Intelligence Analyst

Dataset: Fintech / Risk (data transaksi, pinjaman, risiko kredit, dsb.)

Skala Data: 1–2 juta baris (simulasi big data)

Bahasa NLQ: Multi-bahasa (Indonesia & Inggris)

Autentikasi: Single user (MVP)

Output Laporan: PDF + Link/Embed Dashboard

Deployment: Lokal via Docker Compose (semua service termasuk Metabase)

Metabase: Di-setup dari nol di dalam Docker Compose

Mode Jawaban: Streaming chat (profesional, interaktif)

MCP Tools: Wajib send_slack, send_email, render_dashboard, fetch_data + tools tambahan jika diperlukan (misal export_pdf, notify_webhook)

Latensi: Optimal (target secepat mungkin dengan caching & optimasi query)

Komponen Utama: Multi-agent (Planner, Query Generator, Validator, Query Optimizer, Insight Analyzer, Dashboard Builder, Report Sender), RAG metadata, Redis caching, dynamic DB connector (PostgreSQL/MySQL/MongoDB), Metabase adapter, frontend React/Vue + FastAPI backend, Docker Compose.