-- Create the database if it doesn't exist
CREATE DATABASE IF NOT EXISTS studentbite_db;

-- Use the newly created database
USE studentbite_db;

-- Create a dedicated user and grant privileges
CREATE USER IF NOT EXISTS 'studentbite'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON studentbite_db.* TO 'studentbite'@'localhost';
FLUSH PRIVILEGES;

-- Drop tables if they exist to ensure a clean slate on re-runs
DROP TABLE IF EXISTS Reviews;
DROP TABLE IF EXISTS Transactions;
DROP TABLE IF EXISTS Dishes;
DROP TABLE IF EXISTS Users;

-- Users Table: Stores student and admin information
CREATE TABLE Users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL, -- Usernames must be unique for login
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL, -- Store hashed passwords
    `role` ENUM('student', 'admin') NOT NULL DEFAULT 'student',
    points INT DEFAULT 0,
    badges VARCHAR(255) -- Comma-separated list of badge names
);

-- Dishes Table: Stores information about each food item
CREATE TABLE Dishes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    price DECIMAL(10, 2) NOT NULL
);

-- Reviews Table: Stores student reviews for dishes
CREATE TABLE Reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    dish_id INT NOT NULL,
    rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE,
    FOREIGN KEY (dish_id) REFERENCES Dishes(id) ON DELETE CASCADE
);

-- Transactions Table: For demand forecasting and revenue insights
CREATE TABLE Transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    dish_id INT NOT NULL,
    transaction_date DATE NOT NULL,
    FOREIGN KEY (user_id) REFERENCES Users(id),
    FOREIGN KEY (dish_id) REFERENCES Dishes(id)
);

-- Note: Initial data is now inserted via the seed.py script to handle password hashing.

