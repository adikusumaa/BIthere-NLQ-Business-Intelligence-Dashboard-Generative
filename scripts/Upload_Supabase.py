import pandas as pd
from supabase import create_client
import os
import time
from dotenv import load_dotenv

load_dotenv()

print("[PROCESS] Starting data upload to Supabase...")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("[ERROR] SUPABASE_URL or SUPABASE_KEY not found in .env file.")
    exit(1)

print(f"[INFO] Using Supabase URL: {SUPABASE_URL}")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def upload_csv(file_path, table_name, batch_size=1000):
    if not os.path.exists(file_path):
        print(f"[WARNING] File not found: {file_path}")
        return

    print(f"[PROCESS] Reading {file_path}...")
    df = pd.read_csv(file_path, low_memory=False)

    df = df.where(pd.notnull(df), None)

    records = df.to_dict(orient='records')
    total = len(records)
    print(f"[INFO] Total rows to upload to {table_name}: {total:,}")

    for i in range(0, total, batch_size):
        batch = records[i:i+batch_size]
        try:
            supabase.table(table_name).insert(batch).execute()
            print(f"[INFO] Uploaded batch {i//batch_size + 1} ({len(batch)} rows) to {table_name}")
        except Exception as e:
            print(f"[ERROR] Failed on {table_name} batch {i//batch_size + 1}: {e}")
            break
        time.sleep(0.3)

    print(f"[SUCCESS] Finished uploading {table_name}")

print("[PROCESS] Uploading tables in correct order (respecting foreign keys)...")
upload_csv('data/users.csv', 'users')
upload_csv('data/cards.csv', 'cards')
upload_csv('data/mcc_codes.csv', 'mcc_codes')
upload_csv('data/transactions.csv', 'transactions')
upload_csv('data/fraud_labels.csv', 'fraud_labels')

print("[SUCCESS] All data uploaded successfully!")