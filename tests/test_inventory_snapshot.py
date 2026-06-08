import pytest

def calculate_stock_akhir(stock_awal, quantity_received, quantity_sold, quantity_adjusted):
    # Business logic for calculated stock_akhir.
    return stock_awal + quantity_received - quantity_sold + quantity_adjusted

def test_inventory_snapshot_math():
    # Scenario 1: Standard transaction day (no adjustments)
    assert calculate_stock_akhir(100, 50, 20, 0) == 130
    
    # Scenario 2: Restock and sales with shrinkage adjustment (quantity_adjusted is negative)
    assert calculate_stock_akhir(100, 30, 15, -2) == 113
    
    # Scenario 3: Stagnant stock day
    assert calculate_stock_akhir(50, 0, 0, 0) == 50
    
    # Scenario 4: Surplus adjustment (positive adjustment)
    assert calculate_stock_akhir(10, 0, 0, 3) == 13
