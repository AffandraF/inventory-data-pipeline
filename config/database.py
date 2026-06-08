import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from pathlib import Path

# Load environment variables
BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=BASE_DIR / 'config' / '.env')

# MySQL Configuration (Source WMS)
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "inventory_wms")
MYSQL_USER = os.getenv("MYSQL_USER", "wms_user")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "wmspassword")

# PostgreSQL Configuration (Target DWH)
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = os.getenv("PG_PORT", "5432")
PG_DATABASE = os.getenv("PG_DATABASE", "inventory_dw")
PG_USER = os.getenv("PG_USER", "dw_admin")
PG_PASSWORD = os.getenv("PG_PASSWORD", "dwpassword")

def get_mysql_engine():
    # Returns SQLAlchemy engine for MySQL source database.
    url = f"mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
    return create_engine(url)

def get_postgres_engine():
    # Returns SQLAlchemy engine for PostgreSQL DWH database.
    url = f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DATABASE}"
    return create_engine(url)
