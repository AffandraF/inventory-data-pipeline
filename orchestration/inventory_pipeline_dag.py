from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator
import sys
import logging
from pathlib import Path

# Add project root to system path to enable module imports
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.extract.extract_pipeline import run_extract
from src.transform.transform_pipeline import run_transform
from src.quality.quality_pipeline import run_quality_check
from src.load.load_pipeline import run_load

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Default arguments for the DAG
default_args = {
    "owner": "data_engineering_team",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=3),
}

with DAG(
    dag_id="retail_inventory_analytics_pipeline",
    default_args=default_args,
    description="Incremental daily ETL pipeline with separate stages for extraction, DuckDB transformations, and DWH loading.",
    schedule_interval="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["retail", "inventory", "dwh"],
) as dag:

    # 1. Start Task
    start = EmptyOperator(task_id="start")

    # 2. Extract Task
    extract = PythonOperator(
        task_id="extract",
        python_callable=run_extract,
    )

    # 3. Transform Task
    transform = PythonOperator(
        task_id="transform",
        python_callable=run_transform,
    )

    # 4. Quality Check Task
    quality_check = PythonOperator(
        task_id="quality_check",
        python_callable=run_quality_check,
    )

    # 5. Load Task
    load = PythonOperator(
        task_id="load",
        python_callable=run_load,
    )

    # 6. End Task
    end = EmptyOperator(task_id="end")

    # DAG Dependency Flow
    start >> extract >> transform >> quality_check >> load >> end
