import sys
import duckdb
from pathlib import Path
from string import Template
import logging

logger = logging.getLogger(__name__)

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from config.configuration import DATA_RAW_DIR, DATA_STAGING_DIR
from src.utils.decorators import timeit

@timeit
def run_inventory_snapshot():
    # Runs DuckDB SQL to transform raw transaction and log data into daily inventory snapshots.
    logger.info("Starting inventory snapshot calculation...")
    
    # Define paths
    stock_daily_path = DATA_RAW_DIR / "stock_daily.parquet"
    purchases_path = DATA_RAW_DIR / "purchases.parquet"
    sales_path = DATA_RAW_DIR / "sales.parquet"
    adjustments_path = DATA_RAW_DIR / "adjustments.parquet"
    
    # Read SQL template
    sql_template_path = Path(__file__).resolve().parents[1] / "sql" / "inventory_snapshot.sql"
    with open(sql_template_path, "r") as f:
        sql_template = Template(f.read())
        
    # Substitute path variables
    # DuckDB requires paths to be string with forward slashes for cross-platform compatibility
    sql = sql_template.substitute(
        stock_daily_path=f"'{stock_daily_path.as_posix()}'",
        purchases_path=f"'{purchases_path.as_posix()}'",
        sales_path=f"'{sales_path.as_posix()}'",
        adjustments_path=f"'{adjustments_path.as_posix()}'"
    )
    
    # Run transformation in DuckDB
    con = duckdb.connect()
    try:
        df = con.execute(sql).fetchdf()
    finally:
        con.close()
        
    # Save to staging
    output_path = DATA_STAGING_DIR / "inventory_snapshot.parquet"
    df.to_parquet(output_path, index=False)
    logger.info(f"Inventory snapshot completed. Saved {len(df)} records to {output_path}")
    return df
