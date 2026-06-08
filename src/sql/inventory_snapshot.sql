-- Daily Inventory Snapshot SQL (Stock Ledger calculation)

WITH date_series AS (
    -- Get all unique combinations of date and product from stock daily logs
    SELECT DISTINCT 
        CAST(created_date AS DATE) AS inventory_date,
        product_id
    FROM read_parquet($stock_daily_path)
),
daily_purchases AS (
    SELECT 
        CAST(received_date AS DATE) AS po_date,
        product_id,
        SUM(received_quantity) AS qty_received
    FROM read_parquet($purchases_path)
    GROUP BY 1, 2
),
daily_sales AS (
    SELECT 
        CAST(transaction_date AS DATE) AS sale_date,
        product_id,
        SUM(quantity) AS qty_sold
    FROM read_parquet($sales_path)
    GROUP BY 1, 2
),
daily_adjustments AS (
    SELECT 
        CAST(adjustment_date AS DATE) AS adj_date,
        product_id,
        SUM(quantity) AS qty_adjusted
    FROM read_parquet($adjustments_path)
    GROUP BY 1, 2
),
daily_system_stock AS (
    SELECT 
        CAST(created_date AS DATE) AS log_date,
        product_id,
        SUM(onhand_quantity) AS stock_aktual_system
    FROM read_parquet($stock_daily_path)
    GROUP BY 1, 2
),
daily_prev_system_stock AS (
    -- Stock awal is the system onhand quantity of the previous day
    SELECT 
        CAST(created_date AS DATE) + INTERVAL '1 DAY' AS next_date,
        product_id,
        SUM(onhand_quantity) AS stock_awal
    FROM read_parquet($stock_daily_path)
    GROUP BY 1, 2
)
SELECT 
    ds.inventory_date,
    ds.product_id,
    COALESCE(prev.stock_awal, 0) AS stock_awal,
    COALESCE(dp.qty_received, 0) AS quantity_received,
    COALESCE(dsales.qty_sold, 0) AS quantity_sold,
    COALESCE(da.qty_adjusted, 0) AS quantity_adjusted,
    (
        COALESCE(prev.stock_awal, 0) 
        + COALESCE(dp.qty_received, 0) 
        - COALESCE(dsales.qty_sold, 0) 
        + COALESCE(da.qty_adjusted, 0)
    ) AS stock_akhir,
    COALESCE(sys.stock_aktual_system, 0) AS stock_aktual_system,
    (
        COALESCE(sys.stock_aktual_system, 0) 
        - (
            COALESCE(prev.stock_awal, 0) 
            + COALESCE(dp.qty_received, 0) 
            - COALESCE(dsales.qty_sold, 0) 
            + COALESCE(da.qty_adjusted, 0)
        )
    ) AS selisih
FROM date_series ds
LEFT JOIN daily_prev_system_stock prev 
    ON ds.inventory_date = CAST(prev.next_date AS DATE) AND ds.product_id = prev.product_id
LEFT JOIN daily_purchases dp 
    ON ds.inventory_date = dp.po_date AND ds.product_id = dp.product_id
LEFT JOIN daily_sales dsales 
    ON ds.inventory_date = dsales.sale_date AND ds.product_id = dsales.product_id
LEFT JOIN daily_adjustments da 
    ON ds.inventory_date = da.adj_date AND ds.product_id = da.product_id
LEFT JOIN daily_system_stock sys 
    ON ds.inventory_date = sys.log_date AND ds.product_id = sys.product_id
ORDER BY ds.inventory_date, ds.product_id
