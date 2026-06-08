import sys
import duckdb
from pathlib import Path
from string import Template
import logging

logger = logging.getLogger(__name__)

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from config.configuration import DATA_STAGING_DIR, LEAD_TIME_DAYS, SAFETY_STOCK_DAYS
from src.utils.decorators import timeit

@timeit
def run_reorder_analysis():
    # Runs DuckDB SQL to perform reorder point and safety stock analysis.
    logger.info("Starting safety stock and reorder recommendation analysis...")
    
    metrics_path = DATA_STAGING_DIR / "inventory_metrics.parquet"
    
    # Read SQL template
    sql_template_path = Path(__file__).resolve().parents[1] / "sql" / "reorder_recommendation.sql"
    with open(sql_template_path, "r") as f:
        sql_template = Template(f.read())
        
    # Substitute variables
    sql = sql_template.substitute(
        metrics_path=f"'{metrics_path.as_posix()}'",
        safety_stock_days=str(SAFETY_STOCK_DAYS),
        lead_time_days=str(LEAD_TIME_DAYS)
    )
    
    # Run transformation in DuckDB
    con = duckdb.connect()
    try:
        df = con.execute(sql).fetchdf()
    finally:
        con.close()
        
    # Save to staging
    output_path = DATA_STAGING_DIR / "reorder_recommendation.parquet"
    df.to_parquet(output_path, index=False)
    logger.info(f"Reorder analysis completed. Saved {len(df)} records to {output_path}")
    return df
