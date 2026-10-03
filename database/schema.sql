CREATE DATABASE IF NOT EXISTS localmart CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE localmart;

DROP TABLE IF EXISTS reviews;
DROP TABLE IF EXISTS wishlists;
DROP TABLE IF EXISTS coupons;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
 id INT AUTO_INCREMENT PRIMARY KEY,
 name VARCHAR(100) NOT NULL,
 email VARCHAR(150) NOT NULL UNIQUE,
 password_hash VARCHAR(255) NOT NULL,
 role ENUM('customer','admin') NOT NULL DEFAULT 'customer',
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE categories (
 id INT AUTO_INCREMENT PRIMARY KEY,
 name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE products (
 id INT AUTO_INCREMENT PRIMARY KEY,
 name VARCHAR(150) NOT NULL,
 description TEXT,
 price DECIMAL(10,2) NOT NULL,
 stock INT NOT NULL DEFAULT 0,
 category_id INT,
 image_url VARCHAR(500),
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
);

CREATE TABLE orders (
 id INT AUTO_INCREMENT PRIMARY KEY,
 user_id INT NOT NULL,
 total_amount DECIMAL(10,2) NOT NULL,
 address TEXT NOT NULL,
 status ENUM('Pending','Confirmed','Packed','Shipped','Delivered','Cancelled') NOT NULL DEFAULT 'Pending',
 payment_method VARCHAR(40) NOT NULL DEFAULT 'Cash on Delivery',
 coupon_code VARCHAR(50),
 discount_amount DECIMAL(10,2) NOT NULL DEFAULT 0,
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE order_items (
 id INT AUTO_INCREMENT PRIMARY KEY,
 order_id INT NOT NULL,
 product_id INT NOT NULL,
 quantity INT NOT NULL,
 unit_price DECIMAL(10,2) NOT NULL,
 FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
 FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT
);

CREATE TABLE wishlists (
 id INT AUTO_INCREMENT PRIMARY KEY, user_id INT NOT NULL, product_id INT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 UNIQUE KEY unique_wishlist(user_id,product_id), FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE, FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE TABLE reviews (
 id INT AUTO_INCREMENT PRIMARY KEY, product_id INT NOT NULL, user_id INT NOT NULL, rating TINYINT NOT NULL, comment VARCHAR(500) NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 UNIQUE KEY one_review(user_id,product_id), FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE, FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE coupons (
 id INT AUTO_INCREMENT PRIMARY KEY, code VARCHAR(50) NOT NULL UNIQUE, discount_type ENUM('flat','percent') NOT NULL, discount_amount DECIMAL(10,2) NOT NULL, active TINYINT(1) NOT NULL DEFAULT 1, expires_at DATETIME NULL
);

INSERT INTO categories(name) VALUES ('Groceries'),('Clothing'),('Electronics'),('Home & Kitchen');

INSERT INTO products(name,description,price,stock,category_id,image_url) VALUES
('Fresh Market Box','A colourful everyday grocery box with fresh local essentials.',499.00,30,1,'https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=900&q=80'),
('Organic Fruit Basket','Seasonal fruits sourced from nearby local sellers.',649.00,18,1,'https://images.unsplash.com/photo-1619566636858-adf3ef46400b?auto=format&fit=crop&w=900&q=80'),
('Premium Grocery Combo','Rice, pulses, spices and pantry essentials for the week.',899.00,22,1,'https://images.unsplash.com/photo-1601598851547-4302969d4f2d?auto=format&fit=crop&w=900&q=80'),
('Cotton Casual Shirt','Soft, breathable everyday shirt from a local clothing seller.',799.00,15,2,'https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?auto=format&fit=crop&w=900&q=80'),
('Everyday Denim Jacket','A versatile denim layer with a comfortable modern fit.',1499.00,9,2,'https://images.unsplash.com/photo-1551537482-f2075a1d41f2?auto=format&fit=crop&w=900&q=80'),
('Classic Sneakers','Lightweight casual sneakers for everyday city walks.',1199.00,14,2,'https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=900&q=80'),
('Wireless Headphones','Comfortable Bluetooth headphones with everyday battery life.',1299.00,12,3,'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=900&q=80'),
('Smart Watch','Modern fitness and notification companion for your daily routine.',2299.00,10,3,'https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=900&q=80'),
('Portable Speaker','Compact wireless speaker for music at home or outdoors.',1599.00,16,3,'https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?auto=format&fit=crop&w=900&q=80'),
('Kitchen Storage Set','Reusable storage containers to keep your kitchen organized.',599.00,20,4,'https://images.unsplash.com/photo-1584990347449-a0d9d7c2d0f6?auto=format&fit=crop&w=900&q=80'),
('Ceramic Dinner Set','Elegant everyday dinnerware for family meals and guests.',1299.00,11,4,'https://images.unsplash.com/photo-1603199506016-b9a594b593c0?auto=format&fit=crop&w=900&q=80'),
('Indoor Plant Pot','A simple decorative planter to bring more green into your home.',449.00,25,4,'https://images.unsplash.com/photo-1485955900006-10f4d324d411?auto=format&fit=crop&w=900&q=80'),
('LED Study Lamp','Adjustable desk lamp for study, work and reading.',699.00,19,4,'https://images.unsplash.com/photo-1507473885765-e6ed057f782c?auto=format&fit=crop&w=900&q=80'),
('Daily Essentials Pack','A convenient bundle of practical household essentials.',749.00,17,1,'https://images.unsplash.com/photo-1604719312566-8912e9227c6a?auto=format&fit=crop&w=900&q=80'),
('Minimal Backpack','Lightweight everyday backpack for college, work and travel.',999.00,13,2,'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=900&q=80'),
('Fast Charging Adapter','Compact charging adapter designed for daily mobile use.',899.00,21,3,'https://images.unsplash.com/photo-1583863788434-e58a36330cf0?auto=format&fit=crop&w=900&q=80');

INSERT INTO coupons(code,discount_type,discount_amount,active) VALUES ('WELCOME10','percent',10,1),('LOCAL100','flat',100,1);
