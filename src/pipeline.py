# For manual run, without Airflow

import sys
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.utils.decorators import timeit

from src.extract.extract_pipeline import run_extract
from src.transform.transform_pipeline import run_transform
from src.quality.quality_pipeline import run_quality_check
from src.load.load_pipeline import run_load

@timeit
def run_pipeline():
    # Main orchestrator for the Retail Inventory Analytics Pipeline.
    logger.info("Initializing Retail Inventory Analytics Pipeline...")
    
    try:
        # 1. Extraction Phase
        logger.info("--- STARTING EXTRACTION PHASE ---")
        run_extract()
        
        # 2. Transformation Phase (DuckDB)
        logger.info("--- STARTING TRANSFORMATION PHASE ---")
        run_transform()
        
        # 3. Data Mart Preparation & Quality Checks Phase
        logger.info("--- STARTING DATA QUALITY & MARTS GENERATION PHASE ---")
        run_quality_check()
        
        # 4. Database Loading Phase (DWH)
        logger.info("--- STARTING DWH LOADING PHASE ---")
        total_loaded = run_load()
        
        logger.info("Pipeline completed successfully!")
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    run_pipeline()
