import pandas as pd
import logging

logger = logging.getLogger(__name__)


def run_duplicate_check(df: pd.DataFrame, key_columns: list) -> tuple:
    # Verifies that there are no duplicate records based on the given composite key columns.
    #
    # Returns:
    #     tuple: (passed: bool, duplicate_count: int)
    logger.info(f"Running duplicate check on keys: {key_columns}")

    # Check if all keys exist
    missing_cols = [col for col in key_columns if col not in df.columns]
    if missing_cols:
        logger.error(f"Cannot run duplicate check. Missing key columns: {missing_cols}")
        return False, len(df)

    # Find duplicates
    duplicates = df.duplicated(subset=key_columns, keep=False)
    duplicate_count = duplicates.sum()

    passed = duplicate_count == 0
    if passed:
        logger.info("Duplicate check passed.")
    else:
        logger.error(
            f"Duplicate check failed: found {duplicate_count} duplicate rows for keys {key_columns}"
        )

    return passed, duplicate_count
