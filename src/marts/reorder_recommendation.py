import sys
import pandas as pd
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from config.configuration import DATA_STAGING_DIR, DATA_MART_DIR
from src.quality.null_check import run_null_check
from src.utils.decorators import timeit

@timeit
def generate_reorder_recommendations_mart() -> tuple:
    # Prepares the reorder recommendation report mart for store managers.
    logger.info("Generating active reorder recommendations report...")
    
    input_path = DATA_STAGING_DIR / "reorder_recommendation.parquet"
    if not input_path.exists():
        raise FileNotFoundError(f"Staging file not found: {input_path}")
        
    df_all = pd.read_parquet(input_path)
    
    # Filter only records that require restocking (reorder_alert == True)
    df_reorder = df_all[df_all["reorder_alert"] == True].copy()
    
    # Run null checks on essential columns
    null_cols = ["inventory_date", "product_id", "stock_akhir", "recommended_reorder_qty"]
    null_passed, null_count = run_null_check(df_reorder, null_cols)
    
    output_path = DATA_MART_DIR / "reorder_recommendations.parquet"
    df_reorder.to_parquet(output_path, index=False)
    logger.info(f"Successfully generated active reorder recommendations mart to {output_path} (count: {len(df_reorder)})")
    
    return df_reorder, True, {"nulls": null_count}

if __name__ == "__main__":
    generate_reorder_recommendations_mart()
