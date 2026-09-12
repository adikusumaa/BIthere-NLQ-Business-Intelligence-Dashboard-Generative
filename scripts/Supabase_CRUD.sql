CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY,
    current_age INT,
    retirement_age INT,
    birth_year INT,
    birth_month INT,
    gender TEXT,
    address TEXT,
    latitude FLOAT,
    longitude FLOAT,
    per_capita_income FLOAT,
    yearly_income FLOAT,
    total_debt FLOAT,
    credit_score INT,
    num_credit_cards INT
);

CREATE TABLE IF NOT EXISTS cards (
    id BIGINT PRIMARY KEY,
    client_id BIGINT REFERENCES users(id),
    card_brand TEXT,
    card_type TEXT,
    card_number TEXT,
    expires TEXT,
    cvv TEXT,
    has_chip BOOLEAN,
    num_cards_issued INT,
    credit_limit FLOAT,
    acct_open_date DATE,
    year_pin_last_changed INT,
    card_on_dark_web BOOLEAN
);


CREATE TABLE IF NOT EXISTS transactions (
    id BIGINT PRIMARY KEY,
    date TIMESTAMP,
    client_id BIGINT,
    card_id BIGINT REFERENCES cards(id),
    amount NUMERIC(10,2),
    use_chip TEXT,
    merchant_id BIGINT,
    merchant_city TEXT,
    merchant_state TEXT,
    zip TEXT,
    mcc TEXT,
    errors TEXT
);

CREATE TABLE IF NOT EXISTS fraud_labels (
    id BIGINT PRIMARY KEY REFERENCES transactions(id),
    fraud_label TEXT
);


CREATE TABLE IF NOT EXISTS mcc_codes (
    mcc_code TEXT PRIMARY KEY,
    description TEXT
);


CREATE INDEX idx_transactions_card_id ON transactions(card_id);
CREATE INDEX idx_transactions_date ON transactions(date);
CREATE INDEX idx_transactions_mcc ON transactions(mcc);
CREATE INDEX idx_cards_client_id ON cards(client_id);
CREATE INDEX idx_fraud_labels_fraud_label ON fraud_labels(fraud_label);
