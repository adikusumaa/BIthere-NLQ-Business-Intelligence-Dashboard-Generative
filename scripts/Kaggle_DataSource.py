import pandas as pd
import json
import os
import random

print("[PROCESS] 1. Checking available files...")
ROOT_PATH = '/kaggle/input/datasets/computingvictor/transactions-fraud-datasets'

for file in os.listdir(ROOT_PATH):
    print(f"[INFO] Found file: {file}")

print("[PROCESS] 2. Reading fraud labels JSON...")
with open(f'{ROOT_PATH}/train_fraud_labels.json', 'r') as f:
    fraud_labels = json.load(f)

fraud_dict = fraud_labels.get('target', {})
print(f"[INFO] Total labeled transactions available: {len(fraud_dict):,}")

print("[PROCESS] 3. Selecting 1,000,000 random IDs from labels...")
all_labeled_ids = list(fraud_dict.keys())
selected_ids = random.sample(all_labeled_ids, 1000000)
selected_ids_set = set(selected_ids)
print(f"[INFO] Selected {len(selected_ids_set):,} unique IDs.")

print("[PROCESS] 4. Reading cards and users...")
cards = pd.read_csv(f'{ROOT_PATH}/cards_data.csv')
users = pd.read_csv(f'{ROOT_PATH}/users_data.csv')
print(f"[INFO] cards: {len(cards):,} rows, users: {len(users):,} rows")

print("[PROCESS] 5. Streaming transactions and writing to CSV...")
CHUNK_SIZE = 50000
TARGET_ROWS = 1000000
first_chunk = True
chunk_iter = pd.read_csv(f'{ROOT_PATH}/transactions_data.csv', chunksize=CHUNK_SIZE, low_memory=False)
total_rows = 0

for i, chunk in enumerate(chunk_iter):
    chunk['id_str'] = chunk['id'].astype(str)
    filtered_chunk = chunk[chunk['id_str'].isin(selected_ids_set)]
    if not filtered_chunk.empty:
        filtered_chunk = filtered_chunk.drop(columns=['id_str'])
        filtered_chunk.to_csv('/kaggle/working/transactions.csv', mode='a', header=first_chunk, index=False)
        total_rows += len(filtered_chunk)
        print(f"[INFO] Chunk {i+1}: Written {len(filtered_chunk)} rows (total: {total_rows:,})")
        first_chunk = False
    if total_rows >= TARGET_ROWS:
        print(f"[INFO] Target {TARGET_ROWS:,} rows reached. Stopping.")
        break

print(f"[INFO] Total transactions written: {total_rows:,}")

print("[PROCESS] 6. Reading transactions CSV and converting data types...")
trans_sample = pd.read_csv('/kaggle/working/transactions.csv', low_memory=False)
trans_sample['card_id'] = pd.to_numeric(trans_sample['card_id'], errors='coerce').fillna(0).astype('int64')
cards['id'] = cards['id'].astype('int64')
cards['client_id'] = pd.to_numeric(cards['client_id'], errors='coerce').fillna(0).astype('int64')
users['id'] = users['id'].astype('int64')
trans_sample['id_str'] = trans_sample['id'].astype(str)
print(f"[INFO] Transactions loaded: {len(trans_sample):,} rows")

print("[PROCESS] 7. Filtering cards and users with correct types...")
active_card_ids = trans_sample['card_id'].unique()
cards_filtered = cards[cards['id'].isin(active_card_ids)]
print(f"[INFO] Cards after filtering: {len(cards_filtered):,}")

active_user_ids = cards_filtered['client_id'].unique()
users_filtered = users[users['id'].isin(active_user_ids)]
print(f"[INFO] Users after filtering: {len(users_filtered):,}")

print("[PROCESS] 8. Mapping fraud labels...")
trans_sample['fraud_label'] = trans_sample['id_str'].map(fraud_dict)
null_count = trans_sample['fraud_label'].isna().sum()
if null_count > 0:
    print(f"[WARNING] Found {null_count} rows with missing fraud label. Dropping them...")
    trans_sample = trans_sample.dropna(subset=['fraud_label'])
    print(f"[INFO] Remaining transactions: {len(trans_sample):,}")

print("[INFO] Fraud distribution:")
print(trans_sample['fraud_label'].value_counts())

print("[PROCESS] 9. Validating foreign key integrity...")
missing_cards = trans_sample[~trans_sample['card_id'].isin(cards_filtered['id'])]
if len(missing_cards) > 0:
    print(f"[ERROR] Found {len(missing_cards)} transactions with missing card references. Attempting to fix by converting to string...")
    trans_sample['card_id_str'] = trans_sample['card_id'].astype(str)
    cards_filtered['id_str'] = cards_filtered['id'].astype(str)
    active_card_ids_str = trans_sample['card_id_str'].unique()
    cards_filtered = cards[cards['id'].astype(str).isin(active_card_ids_str)]
    print(f"[INFO] Cards after string-based filter: {len(cards_filtered):,}")
    missing_cards_final = trans_sample[~trans_sample['card_id_str'].isin(cards_filtered['id'].astype(str))]
    print(f"[INFO] Transactions with missing card references (final): {len(missing_cards_final)}")
else:
    print("[INFO] Transactions with missing card references: 0")

missing_users = cards_filtered[~cards_filtered['client_id'].isin(users_filtered['id'])]
print(f"[INFO] Cards with missing user references: {len(missing_users)}")

print("[PROCESS] 10. Exporting final CSV files...")
trans_sample = trans_sample.drop(columns=['id_str', 'card_id_str'], errors='ignore')
cards_filtered = cards_filtered.drop(columns=['id_str'], errors='ignore')
trans_sample.to_csv('/kaggle/working/transactions.csv', index=False)
cards_filtered.to_csv('/kaggle/working/cards.csv', index=False)
users_filtered.to_csv('/kaggle/working/users.csv', index=False)

with open(f'{ROOT_PATH}/mcc_codes.json', 'r') as f:
    mcc_data = json.load(f)
mcc_df = pd.DataFrame.from_dict(mcc_data, orient='index').reset_index()
mcc_df.columns = ['mcc_code', 'description']
mcc_df['mcc_code'] = mcc_df['mcc_code'].astype(str)
mcc_df.to_csv('/kaggle/working/mcc_codes.csv', index=False)

fraud_filtered = trans_sample[['id', 'fraud_label']].copy()
fraud_filtered.to_csv('/kaggle/working/fraud_labels.csv', index=False)

print("[SUCCESS] All files exported successfully.")
print("[INFO] Final row counts:")
print(f"  - transactions.csv: {len(trans_sample):,}")
print(f"  - cards.csv: {len(cards_filtered):,}")
print(f"  - users.csv: {len(users_filtered):,}")
print(f"  - mcc_codes.csv: {len(mcc_df):,}")
print(f"  - fraud_labels.csv: {len(fraud_filtered):,}")