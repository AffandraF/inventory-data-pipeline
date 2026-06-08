import pandas as pd
import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.quality.null_check import run_null_check
from src.quality.duplicate_check import run_duplicate_check
from src.quality.inventory_validation import run_inventory_business_validation

def test_null_check_passes():
    df = pd.DataFrame({"id": [1, 2, 3], "name": ["A", "B", "C"]})
    passed, count = run_null_check(df, ["id", "name"])
    assert passed == True
    assert count == 0

def test_null_check_fails():
    df = pd.DataFrame({"id": [1, None, 3], "name": ["A", "B", None]})
    passed, count = run_null_check(df, ["id", "name"])
    assert passed == False
    assert count == 2

def test_duplicate_check_passes():
    df = pd.DataFrame({"inventory_date": ["2026-06-01", "2026-06-01"], "product_id": [1, 2]})
    passed, count = run_duplicate_check(df, ["inventory_date", "product_id"])
    assert passed == True
    assert count == 0

def test_duplicate_check_fails():
    df = pd.DataFrame({"inventory_date": ["2026-06-01", "2026-06-01"], "product_id": [1, 1]})
    passed, count = run_duplicate_check(df, ["inventory_date", "product_id"])
    assert passed == False
    assert count == 2  # both rows are duplicates

def test_inventory_business_validation_passes():
    df = pd.DataFrame({"stock_awal": [10, 20], "stock_akhir": [5, 15]})
    passed, count = run_inventory_business_validation(df)
    assert passed == True
    assert count == 0

def test_inventory_business_validation_fails():
    df = pd.DataFrame({"stock_awal": [-5, 20], "stock_akhir": [5, -15]})
    passed, count = run_inventory_business_validation(df)
    assert passed == True  # Warning violations don't cause hard failure in logic
    assert count == 2
