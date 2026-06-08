import sys
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.marts.daily_inventory_snapshot import generate_daily_inventory_fact
from src.marts.inventory_metrics import generate_inventory_movement_fact
from src.marts.reorder_recommendation import generate_reorder_recommendations_mart

def run_quality_check():
    # Runs the data quality and mart compilation checks.
    logger.info("Starting quality check pipeline...")
    _, daily_ok, _ = generate_daily_inventory_fact()
    _, move_ok, _ = generate_inventory_movement_fact()
    _, reorder_ok, _ = generate_reorder_recommendations_mart()
    
    if not (daily_ok and move_ok and reorder_ok):
        raise ValueError("Critical Data Quality check failed in quality pipeline.")
    logger.info("Quality check pipeline completed successfully.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    run_quality_check()
