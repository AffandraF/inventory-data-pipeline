-- Reorder Recommendation Analysis SQL

WITH base_metrics AS (
    SELECT 
        inventory_date,
        product_id,
        stock_awal,
        quantity_received,
        quantity_sold,
        quantity_adjusted,
        stock_akhir,
        stock_aktual_system,
        selisih,
        daily_sales_velocity,
        days_of_inventory,
        inventory_turnover_rate,
        sales_speed_class
    FROM read_parquet($metrics_path)
),
calculations AS (
    SELECT 
        *,
        -- Safety Stock = Daily Sales Velocity * Safety Stock Days
        ROUND(daily_sales_velocity * CAST($safety_stock_days AS INT), 0) AS safety_stock,
        
        -- Reorder Point = (Daily Sales Velocity * Lead Time Days) + Safety Stock
        ROUND((daily_sales_velocity * CAST($lead_time_days AS INT)) + (daily_sales_velocity * CAST($safety_stock_days AS INT)), 0) AS reorder_point
    FROM base_metrics
)
SELECT 
    inventory_date,
    product_id,
    stock_awal,
    quantity_received,
    quantity_sold,
    quantity_adjusted,
    stock_akhir,
    stock_aktual_system,
    selisih,
    daily_sales_velocity,
    days_of_inventory,
    inventory_turnover_rate,
    sales_speed_class,
    
    -- Reorder Alert (True if ending stock is below the reorder point)
    CASE 
        WHEN stock_akhir < reorder_point THEN TRUE
        ELSE FALSE
    END AS reorder_alert,
    
    -- Recommended Reorder Quantity: ROP - stock_akhir + safety_stock (replenish up to safety stock buffer)
    CASE 
        WHEN stock_akhir < reorder_point THEN CAST(reorder_point - stock_akhir + safety_stock AS INT)
        ELSE 0
    END AS recommended_reorder_qty
FROM calculations
ORDER BY inventory_date, product_id
