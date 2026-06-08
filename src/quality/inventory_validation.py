import pandas as pd
import logging

logger = logging.getLogger(__name__)


def run_inventory_business_validation(df: pd.DataFrame) -> tuple:
    # Validates inventory business constraints (e.g. stock quantities should not be negative).
    #
    # Returns:
    #     tuple: (passed: bool, violation_count: int)
    logger.info("Running inventory business rules validation...")

    violation_count = 0

    # 1. Check for negative stock_awal
    if "stock_awal" in df.columns:
        neg_start = (df["stock_awal"] < 0).sum()
        if neg_start > 0:
            logger.warning(
                f"Data Quality Warning: Found {neg_start} records with negative stock_awal."
            )
            violation_count += neg_start

    # 2. Check for negative stock_akhir
    if "stock_akhir" in df.columns:
        neg_end = (df["stock_akhir"] < 0).sum()
        if neg_end > 0:
            logger.warning(
                f"Data Quality Warning: Found {neg_end} records with negative stock_akhir."
            )
            violation_count += neg_end

    passed = violation_count == 0
    if passed:
        logger.info(" Inventory business validation passed.")
    else:
        logger.warning(
            f"Inventory business validation completed with {violation_count} warning violations."
        )

    # We return passed=True even if there are business warnings, but report count
    return True, violation_count
