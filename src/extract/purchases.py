import sys
import pandas as pd
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from config.database import get_mysql_engine
from config.configuration import DATA_RAW_DIR
from src.utils.decorators import timeit

@timeit
def extract_purchases(last_success_date):
    # Extracts purchase orders incrementally based on last success date.
    logger.info(f"Extracting purchase orders from MySQL since {last_success_date}...")
    
    query = """
        SELECT pod.po_detail_id, pod.po_header_id, poh.po_number, poh.supplier_id, poh.order_date,
               pod.product_id, pod.quantity, pod.unit_price, pod.received_quantity, pod.received_date
        FROM purchase_order_detail pod
        JOIN purchase_order_header poh ON pod.po_header_id = poh.po_header_id
        WHERE pod.received_date >= %(last_success)s
    """
    
    engine = get_mysql_engine()
    params = {"last_success": last_success_date}
    
    with engine.connect() as conn:
        df = pd.read_sql_query(query, conn, params=params)
        
    output_path = DATA_RAW_DIR / "purchases.parquet"
    df.to_parquet(output_path, index=False)
    logger.info(f"Successfully extracted {len(df)} purchase details to {output_path}")
    return df

@timeit
def extract_adjustments(last_success_date):
    # Extracts stock adjustments incrementally based on last success date.
    logger.info(f"Extracting stock adjustments from MySQL since {last_success_date}...")
    
    query = """
        SELECT adjustment_id, adjustment_number, adjustment_date, product_id, quantity, reason, created_at
        FROM stock_adjustment
        WHERE adjustment_date >= %(last_success)s
    """
    
    engine = get_mysql_engine()
    params = {"last_success": last_success_date}
    
    with engine.connect() as conn:
        df = pd.read_sql_query(query, conn, params=params)
        
    output_path = DATA_RAW_DIR / "adjustments.parquet"
    df.to_parquet(output_path, index=False)
    logger.info(f"Successfully extracted {len(df)} stock adjustments to {output_path}")
    return df
