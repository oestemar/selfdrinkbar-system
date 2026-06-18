-- データベース作成
CREATE DATABASE IF NOT EXISTS selfdrinkbar;
USE selfdrinkbar;

-- 管理者テーブル
CREATE TABLE IF NOT EXISTS admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    role VARCHAR(20) NOT NULL DEFAULT 'admin',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    password_hash VARCHAR(255) NOT NULL
);

-- 商品テーブル
CREATE TABLE IF NOT EXISTS items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    price INT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_category (category)
);

-- 注文テーブル
CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    total INT NOT NULL,
    payment_method VARCHAR(50),
    purchase_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_purchase_datetime (purchase_datetime)
);

-- 注文詳細テーブル
CREATE TABLE IF NOT EXISTS order_details (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ordered_id INT NOT NULL,
    item_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    price INT NOT NULL,
    quantity INT NOT NULL,
    subtotal INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ordered_id) REFERENCES orders(id) ON DELETE CASCADE,
    INDEX idx_order_id (ordered_id)
);

-- サンプルデータ（オプション）
-- INSERT INTO admins (username, password) VALUES ('admin', 'ハッシュ化されたパスワード');

-- INSERT INTO items (name, category, price, description) VALUES
-- ('ブラックコーヒー', 'coffee', 300, 'シンプルなブラックコーヒー'),
-- ('カフェラテ', 'coffee', 400, '濃厚なミルク入りコーヒー'),
-- ('紅茶', 'tea', 350, 'イギリスの紅茶');
