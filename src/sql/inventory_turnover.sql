-- Inventory Turnover & Sales Velocity SQL

WITH base_data AS (
    SELECT 
        inventory_date,
        product_id,
        stock_awal,
        quantity_received,
        quantity_sold,
        quantity_adjusted,
        stock_akhir,
        stock_aktual_system,
        selisih
    FROM read_parquet($snapshot_path)
),
moving_metrics AS (
    SELECT 
        *,
        -- 7-Day moving average of sales velocity
        ROUND(AVG(quantity_sold) OVER (
            PARTITION BY product_id 
            ORDER BY inventory_date 
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ), 2) AS daily_sales_velocity,
        
        -- 30-Day moving average of stock levels
        AVG(stock_akhir) OVER (
            PARTITION BY product_id 
            ORDER BY inventory_date 
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) AS avg_stock_30d,

        -- 30-Day total sales quantity
        SUM(quantity_sold) OVER (
            PARTITION BY product_id 
            ORDER BY inventory_date 
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) AS total_sales_30d
    FROM base_data
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
    
    -- Days of Inventory
    CASE 
        WHEN daily_sales_velocity = 0 THEN 999.00
        ELSE ROUND(CAST(stock_akhir AS NUMERIC) / daily_sales_velocity, 2)
    END AS days_of_inventory,
    
    -- Inventory Turnover Rate (ITR = Total Sales / Avg Stock)
    CASE 
        WHEN avg_stock_30d = 0 THEN 0.00
        ELSE ROUND(CAST(total_sales_30d AS NUMERIC) / avg_stock_30d, 2)
    END AS inventory_turnover_rate,
    
    -- Sales Speed Classification
    CASE 
        WHEN daily_sales_velocity = 0 THEN 'STAGNANT'
        WHEN (CAST(stock_akhir AS NUMERIC) / NULLIF(daily_sales_velocity, 0)) < 15 
            THEN 'FAST_MOVING'
        WHEN (CAST(stock_akhir AS NUMERIC) / NULLIF(daily_sales_velocity, 0)) <= 60 
            THEN 'SLOW_MOVING'
        ELSE 'STAGNANT'
    END AS sales_speed_class
FROM moving_metrics
ORDER BY inventory_date, product_id
