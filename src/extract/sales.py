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
def extract_sales(last_success_date):
    # Extracts sales transactions incrementally based on last success date.
    logger.info(f"Extracting sales transactions from MySQL since {last_success_date}...")
    
    query = """
        SELECT transaction_id, transaction_number, transaction_date, product_id, quantity, unit_price, discount, total_amount, created_at
        FROM sales_transaction
        WHERE transaction_date >= %(last_success)s
    """
    
    engine = get_mysql_engine()
    params = {"last_success": last_success_date}
    
    with engine.connect() as conn:
        df = pd.read_sql_query(query, conn, params=params)
        
    output_path = DATA_RAW_DIR / "sales.parquet"
    df.to_parquet(output_path, index=False)
    logger.info(f"Successfully extracted {len(df)} sales transactions to {output_path}")
    return df
