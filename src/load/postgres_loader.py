import sys
import pandas as pd
from pathlib import Path
from datetime import datetime, date
import psycopg2
from psycopg2.extras import execute_values
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from config.database import get_postgres_engine
from config.configuration import DATA_RAW_DIR, DATA_MART_DIR
from src.utils.decorators import timeit

# ============================================================================
# Incremental State and Audit Management
# ============================================================================

def get_last_success_date(pipeline_name="retail_inventory_pipeline") -> date:
    # Reads the last processed success date from the database. Default is 30 days ago.
    engine = get_postgres_engine()
    query = "SELECT last_success_date FROM inventory.etl_state WHERE pipeline_name = :pname"
    
    with engine.connect() as conn:
        result = conn.execute(text(query), {"pname": pipeline_name}).fetchone()
        
    if result:
        logger.info(f"Last success date found in DWH: {result[0]}")
        return result[0]
    else:
        default_date = date.today() - pd.Timedelta(days=30)
        logger.info(f"No previous state found. Defaulting to {default_date}")
        return default_date

def update_last_success_date(max_date: date, pipeline_name="retail_inventory_pipeline"):
    # Updates the last success date in the database state table.
    logger.info(f"Updating last success date to {max_date}...")
    engine = get_postgres_engine()
    query = """
        INSERT INTO inventory.etl_state (pipeline_name, last_success_date, updated_at)
        VALUES (:pname, :max_date, CURRENT_TIMESTAMP)
        ON CONFLICT (pipeline_name) DO UPDATE
        SET last_success_date = EXCLUDED.last_success_date,
            updated_at = CURRENT_TIMESTAMP
    """
    with engine.begin() as conn:
        conn.execute(text(query), {"pname": pipeline_name, "max_date": max_date})
    logger.info("Successfully updated state in DWH.")

def log_audit_start(pipeline_name="retail_inventory_pipeline") -> int:
    # Logs the start of an ETL pipeline run. Returns the generated run_id.
    engine = get_postgres_engine()
    query = """
        INSERT INTO inventory.etl_audit (pipeline_name, run_status, start_time)
        VALUES (:pname, 'RUNNING', CURRENT_TIMESTAMP)
        RETURNING run_id
    """
    with engine.begin() as conn:
        result = conn.execute(text(query), {"pname": pipeline_name}).fetchone()
    run_id = result[0]
    logger.info(f"Logged ETL run start. Assigned Run ID: {run_id}")
    return run_id

def log_audit_end(run_id: int, status: str, records_extracted: int = 0, records_loaded: int = 0, 
                  dq_passed: int = 0, dq_failed: int = 0, error_message: str = None):
    # Updates the audit log table at the end of a pipeline run.
    logger.info(f"Logging ETL run completion for Run ID: {run_id} (Status: {status})...")
    engine = get_postgres_engine()
    query = """
        UPDATE inventory.etl_audit
        SET run_status = :status,
            end_time = CURRENT_TIMESTAMP,
            records_extracted = :records_extracted,
            records_loaded = :records_loaded,
            dq_checks_passed = :dq_passed,
            dq_checks_failed = :dq_failed,
            error_message = :error_message
        WHERE run_id = :run_id
    """
    with engine.begin() as conn:
        conn.execute(text(query), {"status": status, "records_extracted": records_extracted, "records_loaded": records_loaded, "dq_passed": dq_passed, "dq_failed": dq_failed, "error_message": error_message, "run_id": run_id})
    logger.info("Successfully recorded run details to etl_audit.")

# ============================================================================
# Dimensional and Fact Table Loading
# ============================================================================

@timeit
def load_suppliers() -> int:
    # Loads supplier master data into dim_supplier (Upsert).
    parquet_path = DATA_RAW_DIR / "suppliers.parquet"
    if not parquet_path.exists():
        logger.warning("Suppliers parquet file not found. Skipping load.")
        return 0
        
    df = pd.read_parquet(parquet_path)
    engine = get_postgres_engine()
    
    logger.info(f"Upserting {len(df)} suppliers to dim_supplier...")
    
    query = """
        INSERT INTO inventory.dim_supplier (supplier_id, supplier_code, supplier_name, email, country, created_at)
        VALUES %s
        ON CONFLICT (supplier_id) DO UPDATE
        SET supplier_code = EXCLUDED.supplier_code,
            supplier_name = EXCLUDED.supplier_name,
            email = EXCLUDED.email,
            country = EXCLUDED.country,
            ingestion_date = CURRENT_TIMESTAMP
    """
    
    # Prepare records
    records = []
    for _, r in df.iterrows():
        created_at = None if pd.isna(r["created_at"]) else pd.to_datetime(r["created_at"])
        records.append((
            int(r["supplier_id"]),
            r["code"],
            r["name"],
            None if pd.isna(r["email"]) else r["email"],
            None if pd.isna(r["country"]) else r["country"],
            created_at
        ))
        
    conn = engine.raw_connection()
    try:
        with conn.cursor() as cur:
            execute_values(cur, query, records)
        conn.commit()
    finally:
        conn.close()
        
    logger.info(f"Successfully loaded {len(df)} suppliers.")
    return len(df)

@timeit
def load_products_scd2() -> int:
    # Loads products into dim_product using Slowly Changing Dimension (SCD) Type 2 logic.
    parquet_path = DATA_RAW_DIR / "products.parquet"
    if not parquet_path.exists():
        logger.warning("Products parquet file not found. Skipping load.")
        return 0
        
    df = pd.read_parquet(parquet_path)
    engine = get_postgres_engine()
    
    logger.info(f"Processing SCD Type 2 for {len(df)} products...")
    
    loaded_count = 0
    now_ts = datetime.now()
    
    conn = engine.raw_connection()
    try:
        with conn.cursor() as cur:
            for _, r in df.iterrows():
                prod_id = int(r["product_id"])
                code = r["code"]
                name = r["name"]
                category = None if pd.isna(r["category"]) else r["category"]
                barcode = None if pd.isna(r["barcode"]) else r["barcode"]
                weight = None if pd.isna(r["weight"]) else float(r["weight"])
                is_active = bool(r["is_active"])
                
                # 1. Fetch current active record in DWH
                cur.execute(
                    "SELECT product_sk, product_name, category, barcode, weight, is_active FROM inventory.dim_product WHERE product_id = %s AND is_current = TRUE",
                    (prod_id,)
                )
                existing = cur.fetchone()
                
                if not existing:
                    # New Product -> Insert new active record
                    insert_query = """
                        INSERT INTO inventory.dim_product 
                        (product_id, product_code, product_name, category, barcode, weight, is_active, effective_start_date, effective_end_date, is_current)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, '9999-12-31 23:59:59', TRUE)
                    """
                    cur.execute(insert_query, (prod_id, code, name, category, barcode, weight, is_active, now_ts))
                    loaded_count += 1
                else:
                    # Product exists. Check if any monitored attributes have changed
                    sk, old_name, old_cat, old_barcode, old_weight, old_active = existing
                    
                    has_changed = (
                        old_name != name or
                        old_cat != category or
                        old_barcode != barcode or
                        (old_weight is not None and abs(float(old_weight) - weight) > 0.001 if weight is not None else old_weight != weight) or
                        old_active != is_active
                    )
                    
                    if has_changed:
                        # Value changed! Expire the old record
                        logger.info(f"Product change detected for ID {prod_id} ({name}). Expiring old SK {sk}...")
                        cur.execute(
                            "UPDATE inventory.dim_product SET effective_end_date = %s, is_current = FALSE WHERE product_sk = %s",
                            (now_ts, sk)
                        )
                        # Insert new active record
                        insert_query = """
                            INSERT INTO inventory.dim_product 
                            (product_id, product_code, product_name, category, barcode, weight, is_active, effective_start_date, effective_end_date, is_current)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, '9999-12-31 23:59:59', TRUE)
                        """
                        cur.execute(insert_query, (prod_id, code, name, category, barcode, weight, is_active, now_ts))
                        loaded_count += 1
            
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
        
    logger.info(f"Completed SCD Type 2 products processing. {loaded_count} new/updated product record versions inserted.")
    return loaded_count

@timeit
def load_fact_inventory_movement() -> int:
    # Loads inventory movement facts into fact_inventory_movement (Upsert).
    parquet_path = DATA_MART_DIR / "fact_inventory_movement.parquet"
    if not parquet_path.exists():
        logger.warning("Inventory movements parquet file not found. Skipping load.")
        return 0
        
    df = pd.read_parquet(parquet_path)
    engine = get_postgres_engine()
    
    logger.info(f"Upserting {len(df)} records into fact_inventory_movement...")
    
    query = """
        INSERT INTO inventory.fact_inventory_movement (movement_date, product_id, supplier_id, movement_type, quantity, unit_price, total_amount, source_reference_id)
        VALUES %s
        ON CONFLICT (movement_type, source_reference_id) DO UPDATE
        SET movement_date = EXCLUDED.movement_date,
            product_id = EXCLUDED.product_id,
            supplier_id = EXCLUDED.supplier_id,
            quantity = EXCLUDED.quantity,
            unit_price = EXCLUDED.unit_price,
            total_amount = EXCLUDED.total_amount,
            ingestion_date = CURRENT_TIMESTAMP
    """
    
    records = []
    for _, r in df.iterrows():
        movement_date = pd.to_datetime(r["movement_date"]).date()
        supplier_id = None if pd.isna(r["supplier_id"]) else int(r["supplier_id"])
        unit_price = None if pd.isna(r["unit_price"]) else float(r["unit_price"])
        total_amount = None if pd.isna(r["total_amount"]) else float(r["total_amount"])
        
        records.append((
            movement_date,
            int(r["product_id"]),
            supplier_id,
            r["movement_type"],
            int(r["quantity"]),
            unit_price,
            total_amount,
            int(r["source_reference_id"])
        ))
        
    conn = engine.raw_connection()
    try:
        with conn.cursor() as cur:
            execute_values(cur, query, records)
        conn.commit()
    finally:
        conn.close()
        
    logger.info(f"Successfully loaded {len(df)} movements.")
    return len(df)

@timeit
def load_fact_daily_inventory() -> int:
    # Loads daily inventory balance aggregates into fact_daily_inventory (Upsert).
    parquet_path = DATA_MART_DIR / "fact_daily_inventory.parquet"
    if not parquet_path.exists():
        logger.warning("Daily inventory parquet file not found. Skipping load.")
        return 0
        
    df = pd.read_parquet(parquet_path)
    engine = get_postgres_engine()
    
    logger.info(f"Upserting {len(df)} records into fact_daily_inventory...")
    
    query = """
        INSERT INTO inventory.fact_daily_inventory (
            inventory_date, product_id, stock_awal, quantity_received, quantity_sold, quantity_adjusted,
            stock_akhir, stock_aktual_system, selisih, daily_sales_velocity, days_of_inventory,
            inventory_turnover_rate, sales_speed_class, reorder_alert, recommended_reorder_qty
        )
        VALUES %s
        ON CONFLICT (inventory_date, product_id) DO UPDATE
        SET stock_awal = EXCLUDED.stock_awal,
            quantity_received = EXCLUDED.quantity_received,
            quantity_sold = EXCLUDED.quantity_sold,
            quantity_adjusted = EXCLUDED.quantity_adjusted,
            stock_akhir = EXCLUDED.stock_akhir,
            stock_aktual_system = EXCLUDED.stock_aktual_system,
            selisih = EXCLUDED.selisih,
            daily_sales_velocity = EXCLUDED.daily_sales_velocity,
            days_of_inventory = EXCLUDED.days_of_inventory,
            inventory_turnover_rate = EXCLUDED.inventory_turnover_rate,
            sales_speed_class = EXCLUDED.sales_speed_class,
            reorder_alert = EXCLUDED.reorder_alert,
            recommended_reorder_qty = EXCLUDED.recommended_reorder_qty,
            ingestion_date = CURRENT_TIMESTAMP
    """
    
    records = []
    for _, r in df.iterrows():
        inv_date = pd.to_datetime(r["inventory_date"]).date()
        records.append((
            inv_date,
            int(r["product_id"]),
            int(r["stock_awal"]),
            int(r["quantity_received"]),
            int(r["quantity_sold"]),
            int(r["quantity_adjusted"]),
            int(r["stock_akhir"]),
            int(r["stock_aktual_system"]),
            int(r["selisih"]),
            float(r["daily_sales_velocity"]),
            float(r["days_of_inventory"]),
            float(r["inventory_turnover_rate"]),
            r["sales_speed_class"],
            bool(r["reorder_alert"]),
            int(r["recommended_reorder_qty"])
        ))
        
    conn = engine.raw_connection()
    try:
        with conn.cursor() as cur:
            execute_values(cur, query, records)
        conn.commit()
    finally:
        conn.close()
        
    logger.info(f"Successfully loaded {len(df)} daily snapshots.")
    return len(df)
