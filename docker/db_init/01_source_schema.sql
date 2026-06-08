USE inventory_wms;

-- 1. Supplier Table
CREATE TABLE IF NOT EXISTS supplier (
    supplier_id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    country VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Product Table
CREATE TABLE IF NOT EXISTS product (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    category VARCHAR(100),
    barcode VARCHAR(50),
    weight DECIMAL(10,2),
    is_active TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Purchase Order Header
CREATE TABLE IF NOT EXISTS purchase_order_header (
    po_header_id INT AUTO_INCREMENT PRIMARY KEY,
    po_number VARCHAR(50) NOT NULL UNIQUE,
    supplier_id INT NOT NULL,
    order_date DATE NOT NULL,
    status VARCHAR(30) DEFAULT 'COMPLETED',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (supplier_id) REFERENCES supplier(supplier_id)
);

-- 4. Purchase Order Detail (Debet / Barang Masuk)
CREATE TABLE IF NOT EXISTS purchase_order_detail (
    po_detail_id INT AUTO_INCREMENT PRIMARY KEY,
    po_header_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(12,2) NOT NULL,
    received_quantity INT NOT NULL,
    received_date DATETIME NOT NULL,
    FOREIGN KEY (po_header_id) REFERENCES purchase_order_header(po_header_id),
    FOREIGN KEY (product_id) REFERENCES product(product_id)
);

-- 5. Sales Transaction Table (Kredit / Barang Keluar)
CREATE TABLE IF NOT EXISTS sales_transaction (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    transaction_number VARCHAR(50) NOT NULL,
    transaction_date DATETIME NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(12,2) NOT NULL,
    discount DECIMAL(5,2) DEFAULT 0.00,
    total_amount DECIMAL(12,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES product(product_id)
);

-- 6. Stock Adjustment Table
CREATE TABLE IF NOT EXISTS stock_adjustment (
    adjustment_id INT AUTO_INCREMENT PRIMARY KEY,
    adjustment_number VARCHAR(50) NOT NULL,
    adjustment_date DATETIME NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL, -- negative for shrinkage/loss, positive for surplus
    reason VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES product(product_id)
);
