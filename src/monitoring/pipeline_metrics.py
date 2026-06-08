import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from config.configuration import DATA_RAW_DIR, DATA_MART_DIR

class PipelineMonitor:
    # Collects runtime statistics and dataset row counts during ETL execution.
    def __init__(self):
        self.metrics = {
            "start_time": datetime.now(),
            "end_time": None,
            "extract_row_counts": {},
            "load_row_counts": {},
            "dq_passed": 0,
            "dq_failed": 0,
            "status": "RUNNING",
            "error": None
        }

    def record_extraction(self):
        # Scans extracted raw files and records row counts.
        logger.info("Collecting extraction statistics...")
        files = {
            "products": "products.parquet",
            "suppliers": "suppliers.parquet",
            "sales": "sales.parquet",
            "purchases": "purchases.parquet",
            "adjustments": "adjustments.parquet",
            "stock_daily": "stock_daily.parquet"
        }
        for key, fname in files.items():
            path = DATA_RAW_DIR / fname
            if path.exists():
                try:
                    df = pd.read_parquet(path)
                    self.metrics["extract_row_counts"][key] = len(df)
                except Exception as e:
                    logger.warning(f"Could not read {path} for metrics: {e}")
                    self.metrics["extract_row_counts"][key] = 0
            else:
                self.metrics["extract_row_counts"][key] = 0

    def record_load(self):
        # Scans final data mart parquets to record load statistics.
        logger.info("Collecting loading statistics...")
        files = {
            "fact_daily_inventory": "fact_daily_inventory.parquet",
            "fact_inventory_movement": "fact_inventory_movement.parquet",
            "reorder_recommendations": "reorder_recommendations.parquet"
        }
        for key, fname in files.items():
            path = DATA_MART_DIR / fname
            if path.exists():
                try:
                    df = pd.read_parquet(path)
                    self.metrics["load_row_counts"][key] = len(df)
                except Exception as e:
                    logger.warning(f"Could not read {path} for metrics: {e}")
                    self.metrics["load_row_counts"][key] = 0
            else:
                self.metrics["load_row_counts"][key] = 0

    def increment_dq(self, passed_count: int, failed_count: int):
        # Accumulates data quality check passing and failing metrics.
        self.metrics["dq_passed"] += passed_count
        self.metrics["dq_failed"] += failed_count

    def end_run(self, status="SUCCESS", error=None):
        # Marks the end of the ETL run and compiles the metrics dictionary.
        self.metrics["end_time"] = datetime.now()
        self.metrics["status"] = status
        self.metrics["error"] = str(error) if error else None
        
        duration = (self.metrics["end_time"] - self.metrics["start_time"]).total_seconds()
        
        logger.info("==================================================")
        logger.info(f"               ETL PIPELINE RUN METRICS          ")
        logger.info("==================================================")
        logger.info(f"Status:      {status}")
        logger.info(f"Duration:    {duration:.2f} seconds")
        logger.info(f"Extracted rows:")
        for k, v in self.metrics["extract_row_counts"].items():
            logger.info(f"  - {k}: {v} rows")
        logger.info(f"Loaded rows:")
        for k, v in self.metrics["load_row_counts"].items():
            logger.info(f"  - {k}: {v} rows")
        logger.info(f"Data Quality Checks:")
        logger.info(f"  - Passed validations: {self.metrics['dq_passed']}")
        logger.info(f"  - Failed validations: {self.metrics['dq_failed']}")
        if error:
            logger.error(f"Execution Error: {error}")
        logger.info("==================================================")
        return self.metrics
