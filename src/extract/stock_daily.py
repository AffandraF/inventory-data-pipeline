import sys
import pandas as pd
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from config.database import get_postgres_engine
from config.configuration import DATA_RAW_DIR
from src.utils.decorators import timeit

@timeit
def extract_stock_daily(last_success_date):
    # Extracts daily system stock logs from PostgreSQL database incrementally.
    logger.info(f"Extracting stock daily logs from PostgreSQL since {last_success_date}...")
    
    query = """
        SELECT product_id, location_code, onhand_quantity, created_date
        FROM source.stock_daily
        WHERE created_date >= %(last_success)s
    """
    
    engine = get_postgres_engine()
    params = {"last_success": last_success_date}
    
    with engine.connect() as conn:
        df = pd.read_sql_query(query, conn, params=params)
        
    output_path = DATA_RAW_DIR / "stock_daily.parquet"
    df.to_parquet(output_path, index=False)
    logger.info(f"Successfully extracted {len(df)} stock daily logs to {output_path}")
    return df
