import sys
from pathlib import Path
from datetime import date, timedelta
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from config.database import get_postgres_engine
from src.load.postgres_loader import (
    load_suppliers,
    load_products_scd2,
    load_fact_inventory_movement,
    load_fact_daily_inventory,
    update_last_success_date,
    log_audit_end,
)

def run_load():
    # Runs the loading pipeline to PostgreSQL DWH.
    logger.info("Starting DWH load pipeline...")
    
    # Retrieve the latest active running audit run_id from Postgres
    engine = get_postgres_engine()
    query_find = "SELECT run_id FROM inventory.etl_audit WHERE run_status = 'RUNNING' ORDER BY start_time DESC LIMIT 1"
    run_id = None
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query_find)).fetchone()
            if result:
                run_id = result[0]
    except Exception as ae:
        logger.warning(f"Could not fetch active run audit details: {ae}")

    try:
        loaded_suppliers = load_suppliers()
        loaded_products = load_products_scd2()
        loaded_movements = load_fact_inventory_movement()
        loaded_daily = load_fact_daily_inventory()
        
        total_loaded = loaded_suppliers + loaded_products + loaded_movements + loaded_daily
        
        # Update watermark
        yesterday = date.today() - timedelta(days=1)
        update_last_success_date(yesterday)
        
        if run_id:
            log_audit_end(
                run_id=run_id,
                status="SUCCESS",
                records_loaded=total_loaded
            )
            
        logger.info(f"DWH load pipeline completed successfully. Loaded {total_loaded} rows.")
        return total_loaded
    except Exception as e:
        if run_id:
            log_audit_end(
                run_id=run_id,
                status="FAILED",
                error_message=str(e)
            )
        logger.error(f"DWH load pipeline failed: {e}")
        raise e
