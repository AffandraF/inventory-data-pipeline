import sys
import pandas as pd
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from config.configuration import DATA_RAW_DIR, DATA_MART_DIR
from src.quality.null_check import run_null_check
from src.quality.duplicate_check import run_duplicate_check
from src.utils.decorators import timeit

@timeit
def generate_inventory_movement_fact() -> tuple:
    # Compiles and validates the fact_inventory_movement dataset from raw transactions.
    logger.info("Compiling inventory movement fact mart...")
    
    purchases_path = DATA_RAW_DIR / "purchases.parquet"
    sales_path = DATA_RAW_DIR / "sales.parquet"
    adjustments_path = DATA_RAW_DIR / "adjustments.parquet"
    
    # 1. Process Purchases (INBOUND)
    if purchases_path.exists() and pd.read_parquet(purchases_path).shape[0] > 0:
        df_pur = pd.read_parquet(purchases_path)
        inbound = pd.DataFrame({
            "movement_date": pd.to_datetime(df_pur["received_date"]).dt.date,
            "product_id": df_pur["product_id"].astype(int),
            "supplier_id": df_pur["supplier_id"].astype(int),
            "movement_type": "INBOUND",
            "quantity": df_pur["received_quantity"].astype(int),
            "unit_price": df_pur["unit_price"].astype(float),
            "total_amount": (df_pur["received_quantity"] * df_pur["unit_price"]).astype(float),
            "source_reference_id": df_pur["po_detail_id"].astype(int)
        })
    else:
        inbound = pd.DataFrame(columns=["movement_date", "product_id", "supplier_id", "movement_type", "quantity", "unit_price", "total_amount", "source_reference_id"])
        
    # 2. Process Sales (OUTBOUND)
    if sales_path.exists() and pd.read_parquet(sales_path).shape[0] > 0:
        df_sale = pd.read_parquet(sales_path)
        outbound = pd.DataFrame({
            "movement_date": pd.to_datetime(df_sale["transaction_date"]).dt.date,
            "product_id": df_sale["product_id"].astype(int),
            "supplier_id": None, # Sales don't have supplier
            "movement_type": "OUTBOUND",
            "quantity": df_sale["quantity"].astype(int),
            "unit_price": df_sale["unit_price"].astype(float),
            "total_amount": df_sale["total_amount"].astype(float),
            "source_reference_id": df_sale["transaction_id"].astype(int)
        })
    else:
        outbound = pd.DataFrame(columns=["movement_date", "product_id", "supplier_id", "movement_type", "quantity", "unit_price", "total_amount", "source_reference_id"])
        
    # 3. Process Adjustments (ADJUSTMENT)
    if adjustments_path.exists() and pd.read_parquet(adjustments_path).shape[0] > 0:
        df_adj = pd.read_parquet(adjustments_path)
        adjust = pd.DataFrame({
            "movement_date": pd.to_datetime(df_adj["adjustment_date"]).dt.date,
            "product_id": df_adj["product_id"].astype(int),
            "supplier_id": None,
            "movement_type": "ADJUSTMENT",
            "quantity": df_adj["quantity"].astype(int),
            "unit_price": None,
            "total_amount": None,
            "source_reference_id": df_adj["adjustment_id"].astype(int)
        })
    else:
        adjust = pd.DataFrame(columns=["movement_date", "product_id", "supplier_id", "movement_type", "quantity", "unit_price", "total_amount", "source_reference_id"])
        
    # Concatenate all movements
    df_movements = pd.concat([inbound, outbound, adjust], ignore_index=True)
    
    if len(df_movements) == 0:
        logger.warning("No movement records compiled.")
        return df_movements, True, {"nulls": 0, "duplicates": 0}
        
    # 4. Data Quality Checks
    null_cols = ["movement_date", "product_id", "movement_type", "quantity", "source_reference_id"]
    null_passed, null_count = run_null_check(df_movements, null_cols)
    
    # Composite key duplicate check
    dup_keys = ["movement_type", "source_reference_id"]
    dup_passed, dup_count = run_duplicate_check(df_movements, dup_keys)
    
    if not (null_passed and dup_passed):
        logger.error("Data Quality check failed for movements. Ingestion aborted.")
        return df_movements, False, {"nulls": null_count, "duplicates": dup_count}
        
    # Save to data mart folder
    output_path = DATA_MART_DIR / "fact_inventory_movement.parquet"
    df_movements.to_parquet(output_path, index=False)
    logger.info(f"Successfully validated and saved inventory movement fact mart to {output_path}")
    
    return df_movements, True, {"nulls": null_count, "duplicates": dup_count}

if __name__ == "__main__":
    generate_inventory_movement_fact()
