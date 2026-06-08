import sys
import duckdb
from pathlib import Path
from string import Template
import logging

logger = logging.getLogger(__name__)

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from config.configuration import DATA_STAGING_DIR
from src.utils.decorators import timeit

@timeit
def run_inventory_turnover():
    # Runs DuckDB SQL to calculate sales velocity, days of inventory, and turnover rates.
    logger.info("Starting sales velocity and inventory turnover calculation...")
    
    snapshot_path = DATA_STAGING_DIR / "inventory_snapshot.parquet"
    
    # Read SQL template
    sql_template_path = Path(__file__).resolve().parents[1] / "sql" / "inventory_turnover.sql"
    with open(sql_template_path, "r") as f:
        sql_template = Template(f.read())
        
    # Substitute variables
    sql = sql_template.substitute(
        snapshot_path=f"'{snapshot_path.as_posix()}'"
    )
    
    # Run transformation in DuckDB
    con = duckdb.connect()
    try:
        df = con.execute(sql).fetchdf()
    finally:
        con.close()
        
    # Save to staging
    output_path = DATA_STAGING_DIR / "inventory_metrics.parquet"
    df.to_parquet(output_path, index=False)
    logger.info(f"Inventory turnover metrics completed. Saved {len(df)} records to {output_path}")
    return df
