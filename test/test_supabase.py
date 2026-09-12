import os
import pandas as pd
from pathlib import Path
from supabase import create_client
from dotenv import load_dotenv

# Load .env dari root project (parent dari folder test/)
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
# Prioritas: SERVICE_ROLE_KEY → fallback ke ANON_KEY
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("[ERROR] SUPABASE_URL or SUPABASE_KEY not found in .env file.")
    print(f"[INFO] Looking for .env at: {ROOT_DIR / '.env'}")
    print(f"[INFO] .env exists: {(ROOT_DIR / '.env').exists()}")
    print(f"[INFO] SUPABASE_URL: {'SET' if SUPABASE_URL else 'NOT SET'}")
    print(f"[INFO] SUPABASE_SERVICE_ROLE_KEY: {'SET' if os.getenv('SUPABASE_SERVICE_ROLE_KEY') else 'NOT SET'}")
    print(f"[INFO] SUPABASE_ANON_KEY: {'SET' if os.getenv('SUPABASE_ANON_KEY') else 'NOT SET'}")
    exit(1)

print("[PROCESS] Connecting to Supabase...")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def count_rows(table_name):
    try:
        response = supabase.table(table_name).select("*", count="exact").execute()
        count = response.count
        print(f"[INFO] Table '{table_name}' has {count:,} rows")
        return count
    except Exception as e:
        print(f"[ERROR] Failed to count rows in '{table_name}': {e}")
        return None

def preview_table(table_name, limit=5):
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

tables = ['users', 'cards', 'mcc_codes', 'transactions', 'fraud_labels']

print("[PROCESS] Checking row counts...")
row_counts = {}
for table in tables:
    count = count_rows(table)
    row_counts[table] = count

print("=" * 60)

print("[PROCESS] Previewing data...")
for table in tables:
    preview_table(table, limit=5)

print("=" * 60)
print("[SUCCESS] Testing completed.")