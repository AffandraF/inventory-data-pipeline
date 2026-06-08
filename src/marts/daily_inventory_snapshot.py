import sys
import pandas as pd
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from config.configuration import DATA_STAGING_DIR, DATA_MART_DIR
from src.quality.null_check import run_null_check
from src.quality.duplicate_check import run_duplicate_check
from src.quality.inventory_validation import run_inventory_business_validation
from src.utils.decorators import timeit

@timeit
def generate_daily_inventory_fact() -> tuple:
    # Prepares and validates the final fact_daily_inventory dataset.
    logger.info("Generating daily inventory data mart snapshot...")
    
    input_path = DATA_STAGING_DIR / "reorder_recommendation.parquet"
    if not input_path.exists():
        raise FileNotFoundError(f"Staging file not found: {input_path}")
        
    df = pd.read_parquet(input_path)
    
    # 1. Run Data Quality Checks
    # Null check
    null_cols = ["inventory_date", "product_id", "stock_awal", "stock_akhir"]
    null_passed, null_count = run_null_check(df, null_cols)
    
    # Duplicate check
    dup_keys = ["inventory_date", "product_id"]
    dup_passed, dup_count = run_duplicate_check(df, dup_keys)
    
    # Business logic check
    biz_passed, biz_count = run_inventory_business_validation(df)
    
    # Check if critical checks passed
    if not (null_passed and dup_passed):
        logger.error("Data Quality check failed on critical conditions (NULLs or Duplicates). Ingestion aborted.")
        return df, False, {"nulls": null_count, "duplicates": dup_count, "biz_warnings": biz_count}
        
    # Save final mart parquet
    output_path = DATA_MART_DIR / "fact_daily_inventory.parquet"
    df.to_parquet(output_path, index=False)
    logger.info(f"Successfully validated and saved daily inventory fact mart to {output_path}")
    
    return df, True, {"nulls": null_count, "duplicates": dup_count, "biz_warnings": biz_count}
if __name__ == "__main__":
    generate_daily_inventory_fact()
