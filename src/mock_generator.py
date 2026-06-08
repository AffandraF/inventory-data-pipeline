import sys
import random
from datetime import datetime, timedelta
from pathlib import Path
from faker import Faker
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from config.database import get_mysql_engine, get_postgres_engine

fake = Faker()
Faker.seed(42)
random.seed(42)

# Configuration
NUM_SUPPLIERS = 5
NUM_PRODUCTS = 10
DAYS_OF_DATA = 30

def clear_databases():
    # Wipes existing data from source databases to ensure fresh run.
    logger.info("Clearing existing source databases data...")
    
    # Clear MySQL
    mysql_engine = get_mysql_engine()
    with mysql_engine.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        for table in ["sales_transaction", "purchase_order_detail", "purchase_order_header", "stock_adjustment", "product", "supplier"]:
            conn.execute(text(f"TRUNCATE TABLE {table}"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        
    # Clear Postgres
    pg_engine = get_postgres_engine()
    with pg_engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE source.stock_daily"))
        conn.execute(text("TRUNCATE TABLE inventory.fact_daily_inventory CASCADE"))
        conn.execute(text("TRUNCATE TABLE inventory.fact_inventory_movement CASCADE"))
        conn.execute(text("TRUNCATE TABLE inventory.dim_product CASCADE"))
        conn.execute(text("TRUNCATE TABLE inventory.dim_supplier CASCADE"))
        conn.execute(text("TRUNCATE TABLE inventory.etl_state CASCADE"))
        conn.execute(text("TRUNCATE TABLE inventory.etl_audit CASCADE"))

def generate_static_data():
    # Generates suppliers and products in MySQL.
    logger.info("Generating supplier and product static data...")
    mysql_engine = get_mysql_engine()
    
    suppliers = []
    products = []
    
    # 1. Suppliers
    countries = ["Indonesia", "Singapore", "Japan", "South Korea", "China"]
    for i in range(1, NUM_SUPPLIERS + 1):
        code = f"SPL-{100 + i}"
        name = fake.company()
        email = f"info@{name.lower().replace(' ', '').replace(',', '')}.com"
        country = countries[i-1]
        suppliers.append((i, code, name, email, country))
        
    # 2. Products
    categories = ["Electronics", "Apparel", "Home & Living", "Office Supplies"]
    for i in range(1, NUM_PRODUCTS + 1):
        code = f"PRD-{1000 + i}"
        name = fake.ecommerce_name() if hasattr(fake, 'ecommerce_name') else f"Product {fake.word().capitalize()} {i}"
        category = random.choice(categories)
        barcode = f"899{random.randint(1000000, 9999999)}"
        weight = round(random.uniform(0.1, 15.0), 2)
        products.append((i, code, name, category, barcode, weight, 1))

    with mysql_engine.begin() as conn:
        # Insert Suppliers
        for s in suppliers:
            conn.execute(
                text("INSERT INTO supplier (supplier_id, code, name, email, country) VALUES (:id, :code, :name, :email, :country)"),
                {"id": s[0], "code": s[1], "name": s[2], "email": s[3], "country": s[4]}
            )
        # Insert Products
        for p in products:
            conn.execute(
                text("INSERT INTO product (product_id, code, name, category, barcode, weight, is_active) VALUES (:id, :code, :name, :category, :barcode, :weight, :is_active)"),
                {"id": p[0], "code": p[1], "name": p[2], "category": p[3], "barcode": p[4], "weight": p[5], "is_active": p[6]}
            )
            
    logger.info(f"Generated {NUM_SUPPLIERS} suppliers and {NUM_PRODUCTS} products in MySQL.")
    return suppliers, products

def generate_transactional_data(suppliers, products):
    # Generates sales, purchases, adjustments, and daily stock logs over 30 days.
    logger.info(f"Generating transaction data for the last {DAYS_OF_DATA} days...")
    mysql_engine = get_mysql_engine()
    pg_engine = get_postgres_engine()
    
    start_date = datetime.now().date() - timedelta(days=DAYS_OF_DATA)
    
    # Initialize inventory tracker: product_id -> current_stock_qty
    stock_tracker = {p[0]: 150 for p in products}  # Start with 150 units of initial inventory
    
    # Store initial stock state for the very first day in PostgreSQL
    with pg_engine.begin() as conn:
        for prod_id, qty in stock_tracker.items():
            dt = datetime.combine(start_date - timedelta(days=1), datetime.min.time())
            conn.execute(
                text("INSERT INTO source.stock_daily (product_id, location_code, onhand_quantity, created_date) VALUES (:prod_id, :loc, :qty, :dt)"),
                {"prod_id": prod_id, "loc": "WH-MAIN-01", "qty": qty, "dt": dt}
            )

    po_count = 0
    tx_count = 0
    adj_count = 0

    for day_idx in range(DAYS_OF_DATA):
        current_date = start_date + timedelta(days=day_idx)
        logger.info(f"Simulating retail activity for date: {current_date}")
        
        # Determine day's transaction datetime
        dt_base = datetime.combine(current_date, datetime.min.time())
        
        # 1. Purchase Orders (Goods received in the morning)
        # Occurs 30% chance per product daily to replenish stock
        for prod in products:
            prod_id = prod[0]
            if random.random() < 0.25: # 25% chance of restocking this product today
                po_count += 1
                supplier = random.choice(suppliers)
                po_number = f"PO-{10000 + po_count}"
                qty_ordered = random.randint(50, 100)
                unit_price = round(random.uniform(5.0, 50.0), 2)
                
                # Write to MySQL
                with mysql_engine.begin() as conn:
                    # PO Header
                    conn.execute(
                        text("INSERT INTO purchase_order_header (po_header_id, po_number, supplier_id, order_date, status) VALUES (:id, :po_num, :sup_id, :dt, :status)"),
                        {"id": po_count, "po_num": po_number, "sup_id": supplier[0], "dt": current_date, "status": "COMPLETED"}
                    )
                    # PO Detail
                    # Simulate arrival a bit after order date (we assume instant receipt for simplicity)
                    conn.execute(
                        text("INSERT INTO purchase_order_detail (po_header_id, product_id, quantity, unit_price, received_quantity, received_date) VALUES (:hdr_id, :prod_id, :qty, :price, :recv_qty, :recv_dt)"),
                        {"hdr_id": po_count, "prod_id": prod_id, "qty": qty_ordered, "price": unit_price, "recv_qty": qty_ordered, "recv_dt": dt_base + timedelta(hours=8)}
                    )
                # Update local tracker
                stock_tracker[prod_id] += qty_ordered

        # 2. Sales Transactions (Customer purchases throughout the day)
        for prod in products:
            prod_id = prod[0]
            # Fast moving products have higher sales rates
            sales_probability = 0.8 if prod_id in [1, 2, 3] else 0.4
            if random.random() < sales_probability:
                # Decide sales volume
                qty_sold = random.randint(5, 25)
                # Ensure we don't sell more than we have
                qty_sold = min(qty_sold, stock_tracker[prod_id])
                
                if qty_sold > 0:
                    tx_count += 1
                    tx_number = f"TX-{50000 + tx_count}"
                    unit_price = round(random.uniform(10.0, 100.0), 2)
                    discount = round(random.choice([0.0, 0.0, 5.0, 10.0]), 2)
                    total_amount = round((qty_sold * unit_price) * (1 - discount/100.0), 2)
                    
                    with mysql_engine.begin() as conn:
                        conn.execute(
                            text("INSERT INTO sales_transaction (transaction_number, transaction_date, product_id, quantity, unit_price, discount, total_amount) VALUES (:tx_num, :tx_dt, :prod_id, :qty, :price, :disc, :total)"),
                            {"tx_num": tx_number, "tx_dt": dt_base + timedelta(hours=14), "prod_id": prod_id, "qty": qty_sold, "price": unit_price, "disc": discount, "total": total_amount}
                        )
                    # Update tracker
                    stock_tracker[prod_id] -= qty_sold

        # 3. Stock Adjustments (Loss / audit findings at end of day)
        # Occurs with 5% chance per day per product
        for prod in products:
            prod_id = prod[0]
            if random.random() < 0.05:
                adj_count += 1
                adj_qty = random.choice([-1, -2, -3]) # Shrinkage (loss)
                # Avoid negative stock
                if stock_tracker[prod_id] + adj_qty >= 0:
                    adj_number = f"ADJ-{20000 + adj_count}"
                    with mysql_engine.begin() as conn:
                        conn.execute(
                            text("INSERT INTO stock_adjustment (adjustment_number, adjustment_date, product_id, quantity, reason) VALUES (:adj_num, :adj_dt, :prod_id, :qty, :reason)"),
                            {"adj_num": adj_number, "adj_dt": dt_base + timedelta(hours=20), "prod_id": prod_id, "qty": adj_qty, "reason": "Inventory Shrinkage (Damaged/Lost)"}
                        )
                    stock_tracker[prod_id] += adj_qty

        # 4. Save Daily Onhand Stock Log to PostgreSQL at end of day
        with pg_engine.begin() as conn:
            for prod_id, current_qty in stock_tracker.items():
                # End of day timestamp
                log_time = dt_base + timedelta(hours=23, minutes=59)
                conn.execute(
                    text("INSERT INTO source.stock_daily (product_id, location_code, onhand_quantity, created_date) VALUES (:prod_id, :loc, :qty, :dt)"),
                    {"prod_id": prod_id, "loc": "WH-MAIN-01", "qty": current_qty, "dt": log_time}
                )

    logger.info(f"Generated {po_count} Purchase Orders, {tx_count} Sales Transactions, and {adj_count} Adjustments.")
    logger.info("Successfully populated source databases with consistent mock data.")

def main():
    try:
        clear_databases()
        suppliers, products = generate_static_data()
        generate_transactional_data(suppliers, products)
        logger.info("Mock data generation successfully completed!")
    except Exception as e:
        logger.error(f"Error generating mock data: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    main()
