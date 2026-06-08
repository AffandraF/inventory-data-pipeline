import pytest

def classify_sales_speed(days_of_inventory):
    # Business rule to classify sales speed based on Days of Inventory (DOI).
    if days_of_inventory < 15:
        return "FAST_MOVING"
    elif days_of_inventory <= 60:
        return "SLOW_MOVING"
    else:
        return "STAGNANT"

def test_sales_speed_classification():
    # Fast Moving (DOI < 15)
    assert classify_sales_speed(5) == "FAST_MOVING"
    assert classify_sales_speed(14.9) == "FAST_MOVING"
    
    # Slow Moving (15 <= DOI <= 60)
    assert classify_sales_speed(15) == "SLOW_MOVING"
    assert classify_sales_speed(30) == "SLOW_MOVING"
    assert classify_sales_speed(60) == "SLOW_MOVING"
    
    # Stagnant (DOI > 60)
    assert classify_sales_speed(61) == "STAGNANT"
    assert classify_sales_speed(999) == "STAGNANT"
