# Dataset guide

Place downloaded CSVs in `data/raw/` and pass them with `--data`.

| Agent | Suggested public dataset | Expected columns |
|---|---|---|
| Risk | IEEE-CIS Fraud Detection (Kaggle) | amount, is_cod, previous_orders, cod_refusals, returns_count, return_frequency, account_age_days, ip_velocity, new_device, payment_risk_flag, location_mismatch, is_fraud |
| Reviews | Amazon/Yelp fake review corpora | text, label (1 = fake) |
| Authenticity | Any labelled listing dump | price_deviation_pct, authorized, suspicious_keyword_count, description_length, cert_claim_unverified, seller_rating, is_counterfeit |

Without `--data`, each script generates realistic synthetic data so the pipeline is runnable offline.
