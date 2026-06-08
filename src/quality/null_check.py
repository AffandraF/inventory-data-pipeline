import pandas as pd
import logging

logger = logging.getLogger(__name__)


def run_null_check(df: pd.DataFrame, columns_to_check: list) -> tuple:
    # Verifies that none of the specified columns contain NULL values.
    #
    # Returns:
    #     tuple: (passed: bool, null_count: int)
    logger.info(f"Running NULL check on columns: {columns_to_check}")

    null_count = 0
    for col in columns_to_check:
        if col not in df.columns:
            logger.warning(f"Column '{col}' not found in DataFrame for NULL check.")
            continue
        col_null_count = df[col].isnull().sum()
        if col_null_count > 0:
            logger.warning(
                f"Data Quality Alert: Column '{col}' contains {col_null_count} NULL values."
            )
            null_count += col_null_count

    passed = null_count == 0
    if passed:
        logger.info("NULL check passed.")
    else:
        logger.error(f"NULL check failed with {null_count} total NULL violations.")

    return passed, null_count
