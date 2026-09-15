import os
import random
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from faker import Faker

fake = Faker()

## Configs

NUM_WEB_RECORDS = 1200
NUM_POS_RECORDS = 1000
WEB_ERROR_PERCENTAGE = 0.08   # 8% web data quality anomalies
POS_ERROR_PERCENTAGE = 0.06   # 6% POS register anomalies

COUNTRIES = ["US", "UK", "IN", "DE", "FR", "CA", "AU"]

# Canonical Product Catalog (Shared between both sales channels)
# This enables cross-channel analytics in dbt while maintaining distinct source department labels
PRODUCT_CATALOG = [
    {
        "product_id": f"PROD-{i:03d}",
        "web_category": cat,
        "pos_department": dept,
        "base_price_min": p_min,
        "base_price_max": p_max,
    }
    for i, (cat, dept, p_min, p_max) in enumerate([
        ("Electronics", "Consumer Electronics", 50.0, 800.0),
        ("Clothing", "Apparel & Fashion", 15.0, 120.0),
        ("Home", "Home & Living", 20.0, 250.0),
        ("Books", "Books & Media", 8.0, 45.0),
        ("Sports", "Sporting Goods", 25.0, 300.0),
    ] * 20, start=1)  # 100 shared products total
]

WEB_PAYMENT_METHODS = ["Credit Card", "PayPal", "UPI", "Debit Card"]
WEB_PLATFORMS = ["Desktop Web", "Mobile App", "Mobile Web"]
WEB_STATUSES = ["Completed", "Cancelled", "Returned"]

POS_STORES = [
    {"location": "New York - 5th Ave", "country": "US"},
    {"location": "London - Oxford St", "country": "UK"},
    {"location": "Berlin - Mitte", "country": "DE"},
    {"location": "Paris - Champs-Elysees", "country": "FR"},
    {"location": "Toronto - Downtown", "country": "CA"},
    {"location": "Sydney - George St", "country": "AU"},
    {"location": "Mumbai - Bandra", "country": "IN"},
]
POS_TENDER_TYPES = ["Card", "Cash", "Contactless"]


# SOURCE 1: E-COMMERCE STORE GENERATION

def generate_web_sales():
    """Generates transactional sales from an online web / app platform."""
    records = []

    for i in range(NUM_WEB_RECORDS):
        prod = random.choice(PRODUCT_CATALOG)
        order_date = fake.date_between(start_date="-1y", end_date="today")
        quantity = random.randint(1, 5)
        unit_price = round(random.uniform(prod["base_price_min"], prod["base_price_max"]), 2)

        records.append({
            "order_id": f"WEB-{10000 + i + 1}",
            "order_date": order_date,
            "customer_id": f"CUST-{random.randint(100, 400)}",
            "customer_name": fake.name(),
            "country": random.choice(COUNTRIES),
            "product_id": prod["product_id"],
            "category": prod["web_category"],
            "quantity": quantity,
            "unit_price": unit_price,
            "payment_method": random.choice(WEB_PAYMENT_METHODS),
            "order_status": random.choice(WEB_STATUSES),
            "platform": random.choice(WEB_PLATFORMS),
        })

    df = pd.DataFrame(records)
    inject_web_errors(df)
    return df


def inject_web_errors(df):
    """Injects real-world data quality anomalies into web orders."""
    num_errors = int(len(df) * WEB_ERROR_PERCENTAGE)

    for _ in range(num_errors):
        row = random.randint(0, len(df) - 1)
        error_type = random.choice([
            "null_customer",
            "negative_quantity",
            "invalid_price",
            "future_date",
            "invalid_country",
            "duplicate_order",
        ])

        if error_type == "null_customer":
            df.at[row, "customer_id"] = None
        elif error_type == "negative_quantity":
            df.at[row, "quantity"] = -random.randint(1, 5)
        elif error_type == "invalid_price":
            df.at[row, "unit_price"] = -round(random.uniform(10, 100), 2)
        elif error_type == "future_date":
            df.at[row, "order_date"] = (datetime.now() + timedelta(days=random.randint(10, 60))).date()
        elif error_type == "invalid_country":
            df.at[row, "country"] = "UNKNOWN"
        elif error_type == "duplicate_order":
            df.at[row, "order_id"] = "WEB-10001"


# SOURCE 2: PHYSICAL RETAIL POS STORE GENERATION

def generate_pos_sales():
    """Generates checkout register transactions from physical retail stores."""
    records = []

    for i in range(NUM_POS_RECORDS):
        prod = random.choice(PRODUCT_CATALOG)
        store = random.choice(POS_STORES)
        sale_dt = fake.date_time_between(start_date="-1y", end_date="now")
        qty = random.randint(1, 4)
        item_price = round(random.uniform(prod["base_price_min"], prod["base_price_max"]), 2)

        # In physical stores, only some customers scan a loyalty/membership card (~60%)
        has_loyalty = random.random() < 0.60
        loyalty_card_no = f"MEM-{random.randint(100, 400)}" if has_loyalty else None

        records.append({
            "receipt_no": f"POS-{50000 + i + 1}",
            "sale_datetime": sale_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "loyalty_card_no": loyalty_card_no,
            "store_location": store["location"],
            "country": store["country"],
            "item_code": prod["product_id"],
            "department": prod["pos_department"],
            "qty": qty,
            "item_price": item_price,
            "tender_type": random.choice(POS_TENDER_TYPES),
            "register_no": f"REG-0{random.randint(1, 6)}",
            "cashier_id": f"EMP-{random.randint(101, 130)}",
        })

    df = pd.DataFrame(records)
    inject_pos_errors(df)
    return df


def inject_pos_errors(df):
    """Injects POS-specific anomalies (e.g. unhandled return adjustments, scanner glitches)."""
    num_errors = int(len(df) * POS_ERROR_PERCENTAGE)

    for _ in range(num_errors):
        row = random.randint(0, len(df) - 1)
        error_type = random.choice([
            "negative_qty_return",
            "zero_price",
            "duplicate_receipt",
            "invalid_country",
            "future_timestamp",
        ])

        if error_type == "negative_qty_return":
            df.at[row, "qty"] = -random.randint(1, 3)
        elif error_type == "zero_price":
            df.at[row, "item_price"] = 0.00
        elif error_type == "duplicate_receipt":
            df.at[row, "receipt_no"] = "POS-50001"
        elif error_type == "invalid_country":
            df.at[row, "country"] = "XX"
        elif error_type == "future_timestamp":
            future_dt = datetime.now() + timedelta(days=random.randint(5, 30))
            df.at[row, "sale_datetime"] = future_dt.strftime("%Y-%m-%d %H:%M:%S")




##### Main #####


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))

    print("Generating Multi-Source E-Commerce Datasets...")

    # 1. Web Sales
    df_web = generate_web_sales()
    web_file = os.path.join(script_dir, "raw_web_sales.csv")
    df_web.to_csv(web_file, index=False)
    print(f"[+] Web Channel: Generated {len(df_web)} rows -> {web_file}")

    # 2. POS Sales
    df_pos = generate_pos_sales()
    pos_file = os.path.join(script_dir, "raw_pos_sales.csv")
    df_pos.to_csv(pos_file, index=False)
    print(f"[+] Retail POS Channel: Generated {len(df_pos)} rows -> {pos_file}")

    print("\nMulti-source data generation complete!")