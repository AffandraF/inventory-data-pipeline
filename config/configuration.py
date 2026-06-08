import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=BASE_DIR / 'config' / '.env')

# Business Logic Settings
LEAD_TIME_DAYS = int(os.getenv("INVENTORY_LEAD_TIME_DAYS", "5"))
SAFETY_STOCK_DAYS = int(os.getenv("INVENTORY_SAFETY_STOCK_DAYS", "3"))

# Data directory paths
DATA_RAW_DIR = BASE_DIR / os.getenv("DATA_RAW_DIR", "data/raw")
DATA_STAGING_DIR = BASE_DIR / os.getenv("DATA_STAGING_DIR", "data/staging")
DATA_MART_DIR = BASE_DIR / os.getenv("DATA_MART_DIR", "data/mart")

# Ensure folders exist
for folder in [DATA_RAW_DIR, DATA_STAGING_DIR, DATA_MART_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

# Target DB Schemas
TARGET_SCHEMA = "inventory"
SOURCE_SCHEMA = "source"
