-- Schema and tables for PostgreSQL (Source Stock logs & Target Data Mart)

-- Create schemas
CREATE SCHEMA IF NOT EXISTS source;
CREATE SCHEMA IF NOT EXISTS inventory;

-- ============================================================================
-- 1. SOURCE SCHEMA: staging tables or source logs
-- ============================================================================

CREATE TABLE IF NOT EXISTS source.stock_daily (
    product_id INT NOT NULL,
    location_code VARCHAR(50) NOT NULL,
    onhand_quantity INT NOT NULL,
    created_date TIMESTAMP NOT NULL,
    PRIMARY KEY (product_id, location_code, created_date)
);

-- ============================================================================
-- 2. INVENTORY SCHEMA: Dimensional Data Mart
-- ============================================================================

-- A. dim_supplier
CREATE TABLE IF NOT EXISTS inventory.dim_supplier (
    supplier_id INT PRIMARY KEY,
    supplier_code VARCHAR(50) NOT NULL,
    supplier_name VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    country VARCHAR(50),
    created_at TIMESTAMP,
    ingestion_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- B. dim_product (SCD Type 2)
CREATE TABLE IF NOT EXISTS inventory.dim_product (
    product_sk BIGSERIAL PRIMARY KEY,
    product_id INT NOT NULL,
    product_code VARCHAR(50) NOT NULL,
    product_name VARCHAR(200) NOT NULL,
    category VARCHAR(100),
    barcode VARCHAR(50),
    weight NUMERIC(10,2),
    is_active BOOLEAN DEFAULT TRUE,
    effective_start_date TIMESTAMP NOT NULL,
    effective_end_date TIMESTAMP NOT NULL DEFAULT '9999-12-31 23:59:59',
    is_current BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for SCD 2 queries
CREATE INDEX IF NOT EXISTS idx_dim_product_id ON inventory.dim_product (product_id);
CREATE INDEX IF NOT EXISTS idx_dim_product_current ON inventory.dim_product (product_id, is_current);

-- C. fact_inventory_movement
CREATE TABLE IF NOT EXISTS inventory.fact_inventory_movement (
    movement_id BIGSERIAL PRIMARY KEY,
    movement_date DATE NOT NULL,
    product_id INT NOT NULL,
    supplier_id INT, -- NULL for Sales Outbound
    movement_type VARCHAR(50) NOT NULL, -- 'INBOUND', 'OUTBOUND', 'ADJUSTMENT'
    quantity INT NOT NULL,
    unit_price NUMERIC(12,2),
    total_amount NUMERIC(12,2),
    source_reference_id INT NOT NULL,
    ingestion_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_movement_ref UNIQUE (movement_type, source_reference_id)
);

-- D. fact_daily_inventory
CREATE TABLE IF NOT EXISTS inventory.fact_daily_inventory (
    id BIGSERIAL PRIMARY KEY,
    inventory_date DATE NOT NULL,
    product_id INT NOT NULL,
    stock_awal INT NOT NULL DEFAULT 0,
    quantity_received INT NOT NULL DEFAULT 0,
    quantity_sold INT NOT NULL DEFAULT 0,
    quantity_adjusted INT NOT NULL DEFAULT 0,
    stock_akhir INT NOT NULL DEFAULT 0,
    stock_aktual_system INT NOT NULL DEFAULT 0,
    selisih INT NOT NULL DEFAULT 0,
    daily_sales_velocity NUMERIC(10,2) DEFAULT 0.00,
    days_of_inventory NUMERIC(10,2) DEFAULT 999.00,
    inventory_turnover_rate NUMERIC(10,2) DEFAULT 0.00,
    sales_speed_class VARCHAR(30) DEFAULT 'STAGNANT',
    reorder_alert BOOLEAN DEFAULT FALSE,
    recommended_reorder_qty INT DEFAULT 0,
    ingestion_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_daily_inventory UNIQUE (inventory_date, product_id)
);

-- Indexes for Fact tables
CREATE INDEX IF NOT EXISTS idx_fact_movement_date ON inventory.fact_inventory_movement (movement_date);
CREATE INDEX IF NOT EXISTS idx_fact_daily_date ON inventory.fact_daily_inventory (inventory_date);
CREATE INDEX IF NOT EXISTS idx_fact_daily_prod ON inventory.fact_daily_inventory (product_id);

-- ============================================================================
-- 3. STATE AND AUDIT TABLES
-- ============================================================================

-- E. etl_state
CREATE TABLE IF NOT EXISTS inventory.etl_state (
    pipeline_name VARCHAR(100) PRIMARY KEY,
    last_success_date DATE NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- F. etl_audit
CREATE TABLE IF NOT EXISTS inventory.etl_audit (
    run_id BIGSERIAL PRIMARY KEY,
    pipeline_name VARCHAR(100) NOT NULL,
    run_status VARCHAR(50) NOT NULL, -- 'RUNNING', 'SUCCESS', 'FAILED'
    start_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    records_extracted INT DEFAULT 0,
    records_loaded INT DEFAULT 0,
    dq_checks_passed INT DEFAULT 0,
    dq_checks_failed INT DEFAULT 0,
    error_message TEXT
);
