import pytest

def calculate_reorder_recommendation(stock_akhir, velocity, lead_time_days, safety_stock_days):
    # Business logic for reorder recommendations.
    safety_stock = round(velocity * safety_stock_days, 0)
    reorder_point = round((velocity * lead_time_days) + safety_stock, 0)
    
    reorder_alert = stock_akhir < reorder_point
    recommended_qty = int(reorder_point - stock_akhir + safety_stock) if reorder_alert else 0
    
    return reorder_alert, recommended_qty

def test_reorder_recommendation_logic():
    # Case 1: Stock is high, no alert
    alert, qty = calculate_reorder_recommendation(
        stock_akhir=100, 
        velocity=5.0, 
        lead_time_days=5, 
        safety_stock_days=3
    )
    # safety_stock = 5 * 3 = 15
    # ROP = 5 * 5 + 15 = 40
    # stock_akhir (100) >= ROP (40) -> no alert, qty = 0
    assert alert is False
    assert qty == 0

    # Case 2: Stock is low, alert and recommended quantity triggered
    alert, qty = calculate_reorder_recommendation(
        stock_akhir=25, 
        velocity=5.0, 
        lead_time_days=5, 
        safety_stock_days=3
    )
    # safety_stock = 15
    # ROP = 40
    # stock_akhir (25) < ROP (40) -> Alert!
    # recommended_qty = ROP (40) - stock_akhir (25) + safety_stock (15) = 30
    assert alert is True
    assert qty == 30
