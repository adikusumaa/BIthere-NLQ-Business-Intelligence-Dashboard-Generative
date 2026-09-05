import pandas as pd
from supabase import create_client
import os
import time
from dotenv import load_dotenv
import numpy as np

load_dotenv()

print("[PROCESS] Starting data upload to Supabase...")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("[ERROR] SUPABASE_URL or SUPABASE_KEY not found in .env file.")
    exit(1)

print(f"[INFO] Using Supabase URL: {SUPABASE_URL}")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def clean_value(val):
    """Bersihkan nilai, ubah NaN/Inf menjadi None."""
    if pd.isna(val):
        return None
    if isinstance(val, float):
        if np.isnan(val) or np.isinf(val):
            return None
        if abs(val) > 1e15:
            return None
        if val == int(val):
            return int(val)
        return val
    if isinstance(val, str):
        val = val.strip()
        if val == '' or val.lower() in ['nan', 'inf', '-inf', 'null']:
            return None
        cleaned = val.replace('$', '').replace(',', '').strip()
        try:
            num = float(cleaned)
            if np.isnan(num) or np.isinf(num):
                return None
            if abs(num) > 1e15:
                return None
            if num == int(num):
                return int(num)
            return num
        except ValueError:
            return val
    return val

def clean_dataframe(df):
    """Terapkan clean_value ke seluruh kolom."""
    for col in df.columns:
        df[col] = df[col].apply(clean_value)
    return df

def convert_date_to_iso(date_val):
    if pd.isna(date_val):
        return None
    if isinstance(date_val, pd.Timestamp):
        return date_val.isoformat()
    if isinstance(date_val, str):
        try:
            dt = pd.to_datetime(date_val)
            return dt.isoformat()
        except:
            return None
    return None

def upload_csv(file_path, table_name, batch_size=500, drop_columns=None):
    if not os.path.exists(file_path):
        print(f"[WARNING] File not found: {file_path}")
        return

    print(f"[PROCESS] Reading {file_path}...")
    df = pd.read_csv(file_path, low_memory=False)

    if drop_columns:
        for col in drop_columns:
            if col in df.columns:
                df = df.drop(columns=[col])
                print(f"[INFO] Dropped column '{col}' for table {table_name}")

    # CLEANING PER TABEL
    if table_name == 'users':
        for col in ['per_capita_income', 'yearly_income', 'total_debt']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace('$', '').str.replace(',', '')
                df[col] = pd.to_numeric(df[col], errors='coerce')

    elif table_name == 'cards':
        if 'acct_open_date' in df.columns:
            df['acct_open_date'] = df['acct_open_date'].apply(
                lambda x: f"{x.split('/')[1]}-{x.split('/')[0].zfill(2)}-01" if isinstance(x, str) and '/' in x else None
            )
        for col in ['credit_limit']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace('$', '').str.replace(',', '')
                df[col] = pd.to_numeric(df[col], errors='coerce')
        for col in ['has_chip', 'card_on_dark_web']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.lower().map({'yes': True, 'no': False, 'true': True, 'false': False})

    elif table_name == 'transactions':
        if 'amount' in df.columns:
            df['amount'] = df['amount'].astype(str).str.replace('$', '').str.replace(',', '')
            df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df['date'] = df['date'].apply(convert_date_to_iso)
        if 'zip' in df.columns:
            df['zip'] = df['zip'].astype(str).str.replace('.0', '').str.strip()
            df['zip'] = df['zip'].replace(['nan', 'None', ''], None)

    elif table_name == 'fraud_labels':
        pass

    # CLEAN SEMUA NaN/Inf
    df = clean_dataframe(df)

    # KONVERSI KE RECORDS
    records = df.to_dict(orient='records')

    # PASTIKAN TIDAK ADA NaN/Inf DI SETIAP RECORD
    for rec in records:
        for key, value in rec.items():
            if isinstance(value, float) and (np.isnan(value) or np.isinf(value)):
                rec[key] = None
            if isinstance(value, str) and value.lower() in ['nan', 'inf', '-inf']:
                rec[key] = None

    total = len(records)
    print(f"[INFO] Total rows to upload to {table_name}: {total:,}")

    successful = 0
    for i in range(0, total, batch_size):
        batch = records[i:i+batch_size]
        batch_num = i // batch_size + 1

        try:
            supabase.table(table_name).upsert(batch).execute()
            successful += len(batch)
            print(f"[INFO] Uploaded batch {batch_num} ({len(batch)} rows) to {table_name} (total: {successful:,})")
        except Exception as e:
            print(f"[ERROR] Failed on {table_name} batch {batch_num}: {e}")
            for idx, rec in enumerate(batch):
                try:
                    supabase.table(table_name).upsert([rec]).execute()
                except Exception as single_error:
                    print(f"[DEBUG] Problematic record: {rec}")
                    print(f"[DEBUG] Error: {single_error}")
                    break
            break
        time.sleep(0.2)

    print(f"[SUCCESS] Finished uploading {table_name} with {successful:,} rows")

print("[PROCESS] Uploading tables in correct order...")
upload_csv('data/users.csv', 'users')
upload_csv('data/cards.csv', 'cards')
upload_csv('data/mcc_codes.csv', 'mcc_codes')
upload_csv('data/transactions.csv', 'transactions', drop_columns=['fraud_label'])
upload_csv('data/fraud_labels.csv', 'fraud_labels')

print("[SUCCESS] All data uploaded successfully!")