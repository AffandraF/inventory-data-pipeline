import sys
from pathlib import Path
import logging
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.extract.products import extract_products, extract_suppliers
from src.extract.sales import extract_sales
from src.extract.purchases import extract_purchases, extract_adjustments
from src.extract.stock_daily import extract_stock_daily
from src.load.postgres_loader import get_last_success_date, log_audit_start

def run_extract():
    # Runs the full incremental extraction pipeline.
    logger.info("Starting extract pipeline...")
    log_audit_start()
    last_success_date = get_last_success_date()
    
    extract_products()
    extract_suppliers()
    extract_sales(last_success_date)
    extract_purchases(last_success_date)
    extract_adjustments(last_success_date)
    extract_stock_daily(last_success_date)
    logger.info("Extract pipeline completed.")
