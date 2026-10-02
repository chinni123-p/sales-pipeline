import pandas as pd
import random
import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text

DB_URL = os.environ["DATABASE_URL"]

PRODUCTS = {
    "Electronics": [("Wireless Earbuds", 2499), ("Smart Watch", 8999),
                    ("Bluetooth Speaker", 3499), ("Power Bank", 1299)],
    "Clothing":    [("Cotton T-Shirt", 799), ("Denim Jeans", 1999),
                    ("Winter Jacket", 3999), ("Running Shoes", 2999)],
    "Home":        [("Coffee Maker", 3499), ("Bed Sheets", 1299),
                    ("Table Lamp", 899), ("Dinner Set", 1999)],
    "Books":       [("Fiction Novel", 399), ("Self-Help Book", 499),
                    ("Technical Guide", 899), ("Biography", 599)],
}
CITIES = ["Mumbai", "Delhi", "Bangalore", "Chennai",
          "Kolkata", "Hyderabad", "Pune", "Ahmedabad"]
CUSTOMERS = ["Aarav", "Priya", "Rohan", "Ananya", "Vikram", "Sneha",
             "Arjun", "Kavya", "Aditya", "Riya", "Karan", "Diya"]
PAYMENTS = ["UPI", "Credit Card", "Debit Card", "Net Banking", "COD"]

def generate_sales(days=30):
    print(f"Generating sales for last {days} days...")
    rows = []
    order_num = 10000
    today = datetime.now().date()
    for d in range(days):
        order_date = today - timedelta(days=d)
        is_weekend = order_date.weekday() >= 5
        n_orders = random.randint(30, 50) if is_weekend else random.randint(15, 30)
        for _ in range(n_orders):
            order_num += 1
            category = random.choice(list(PRODUCTS.keys()))
            product, price = random.choice(PRODUCTS[category])
            qty = random.choices([1,2,3,4,5], weights=[60,25,10,3,2])[0]
            discount = random.choices([0,5,10,15], weights=[60,20,15,5])[0]
            revenue = round(price * qty * (1 - discount/100), 2)
            margin = {"Electronics":0.15, "Clothing":0.40, "Home":0.30, "Books":0.50}
            profit = round(revenue * margin[category], 2)
            rows.append({
                "order_id": f"ORD{order_num}",
                "order_date": order_date,
                "customer_name": random.choice(CUSTOMERS),
                "product_name": product,
                "category": category,
                "city": random.choice(CITIES),
                "quantity": qty,
                "unit_price": price,
                "revenue": revenue,
                "profit": profit,
                "payment_method": random.choice(PAYMENTS),
            })
    df = pd.DataFrame(rows)
    print(f"Generated {len(df)} orders")
    return df

def load_sales(df, engine):
    inserted = 0
    with engine.begin() as conn:
        for _, row in df.iterrows():
            result = conn.execute(text("""
                INSERT INTO sales
                (order_id, order_date, customer_name, product_name, category,
                 city, quantity, unit_price, revenue, profit, payment_method)
                VALUES (:order_id, :order_date, :customer_name, :product_name, :category,
                        :city, :quantity, :unit_price, :revenue, :profit, :payment_method)
                ON CONFLICT (order_id) DO NOTHING
            """), row.to_dict())
            inserted += result.rowcount
    print(f"Inserted {inserted} new rows")
    return inserted

def log_run(engine, rows, status, msg=""):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO pipeline_runs (rows_loaded, status, message)
            VALUES (:r, :s, :m)
        """), {"r": rows, "s": status, "m": msg})

def main():
    print("=" * 55)
    print("PIPELINE START")
    print("=" * 55)
    engine = create_engine(DB_URL, connect_args={"connect_timeout": 15})
    try:
        df = generate_sales(days=30)
        inserted = load_sales(df, engine)
        log_run(engine, inserted, "SUCCESS")
        print("PIPELINE COMPLETED SUCCESSFULLY")
    except Exception as e:
        print(f"FAILED: {e}")
        try:
            log_run(engine, 0, "FAILED", str(e)[:200])
        except Exception:
            pass
        raise

if __name__ == "__main__":
    main()
