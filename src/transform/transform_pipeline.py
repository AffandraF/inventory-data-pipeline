import sys
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.transform.inventory_snapshot import run_inventory_snapshot
from src.transform.inventory_turnover import run_inventory_turnover
from src.transform.reorder_analysis import run_reorder_analysis

def run_transform():
    # Runs the full transformation pipeline in DuckDB.
    logger.info("Starting transform pipeline...")
    run_inventory_snapshot()
    run_inventory_turnover()
    run_reorder_analysis()
    logger.info("Transform pipeline completed.")
