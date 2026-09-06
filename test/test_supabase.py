import os
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("[ERROR] SUPABASE_URL or SUPABASE_KEY not found in .env file.")
    exit(1)

print("[PROCESS] Connecting to Supabase...")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def count_rows(table_name):
    """Menghitung jumlah baris di tabel."""
    try:
        response = supabase.table(table_name).select("*", count="exact").execute()
        count = response.count
        print(f"[INFO] Table '{table_name}' has {count:,} rows")
        return count
    except Exception as e:
        print(f"[ERROR] Failed to count rows in '{table_name}': {e}")
        return None

def preview_table(table_name, limit=5):
    """Menampilkan beberapa baris pertama dari tabel."""
    try:
        response = supabase.table(table_name).select("*").limit(limit).execute()
        data = response.data
        if data:
            df = pd.DataFrame(data)
            print(f"[INFO] Preview of '{table_name}' (first {limit} rows):")
            print(df.to_string(index=False))
        else:
            print(f"[WARNING] No data found in '{table_name}'")
    except Exception as e:
        print(f"[ERROR] Failed to preview '{table_name}': {e}")

print("[PROCESS] Testing Supabase connection and data...")
print("=" * 60)

# Daftar tabel yang akan diuji
tables = ['users', 'cards', 'mcc_codes', 'transactions', 'fraud_labels']

# 1. Cek jumlah baris per tabel
print("[PROCESS] Checking row counts...")
row_counts = {}
for table in tables:
    count = count_rows(table)
    row_counts[table] = count

print("=" * 60)

# 2. Preview 5 baris pertama dari setiap tabel
print("[PROCESS] Previewing data...")
for table in tables:
    preview_table(table, limit=5)

print("=" * 60)
print("[SUCCESS] Testing completed.")