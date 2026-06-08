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
def extract_products():
    # Extracts all products from MySQL source database and saves as Parquet.
    logger.info("Extracting product master data from MySQL...")
    query = """
        SELECT product_id, code, name, category, barcode, weight, is_active, created_at
        FROM product
    """
    engine = get_mysql_engine()
    with engine.connect() as conn:
        df = pd.read_sql_query(query, conn)
    
    output_path = DATA_RAW_DIR / "products.parquet"
    df.to_parquet(output_path, index=False)
    logger.info(f"Successfully extracted {len(df)} products to {output_path}")
    return df

@timeit
def extract_suppliers():
    # Extracts all suppliers from MySQL source database and saves as Parquet.
    logger.info("Extracting supplier master data from MySQL...")
    query = """
        SELECT supplier_id, code, name, email, country, created_at
        FROM supplier
    """
    engine = get_mysql_engine()
    with engine.connect() as conn:
        df = pd.read_sql_query(query, conn)
    
    output_path = DATA_RAW_DIR / "suppliers.parquet"
    df.to_parquet(output_path, index=False)
    logger.info(f"Successfully extracted {len(df)} suppliers to {output_path}")
    return df
