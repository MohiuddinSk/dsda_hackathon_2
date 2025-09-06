import mysql.connector
import csv
import random
from datetime import datetime, timedelta
import os
from werkzeug.security import generate_password_hash

# --- Database Configuration ---
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'studentbite'),
    'password': os.getenv('DB_PASSWORD', 'password'),
    'database': os.getenv('DB_NAME', 'studentbite_db')
}
CSV_FILE_PATH = 'canteen_data.csv'

def seed_data():
    """Reads data from CSV and populates the database tables with hashed passwords."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("Successfully connected to the database.")
    except mysql.connector.Error as err:
        print(f"Error connecting to database: {err}")
        return

    # --- 1. Seed Users (with hashed passwords) ---
    cursor.execute("DELETE FROM Users")
    conn.commit()
    
    # Note: The admin password 'admin@1234' is handled in the Flask login logic as a special case.
    # We still create the admin user here but the password hash is not used for that specific login check.
    # For all other users, the hash IS used.
    users_to_insert = [
        ('admin', 'admin@studentbite.com', generate_password_hash('admin@1234'), 'admin', 0, None),
        ('Alex Doe', 'alex.doe@example.com', generate_password_hash('password123'), 'student', 150, 'First Review,Food Critic'),
        ('Jane Smith', 'jane.smith@example.com', generate_password_hash('password123'), 'student', 280, 'First Review,Food Critic,Gourmet'),
        ('Sam Wilson', 'sam.wilson@example.com', generate_password_hash('password123'), 'student', 80, 'First Review'),
        ('Maria Garcia', 'maria.garcia@example.com', generate_password_hash('password123'), 'student', 210, 'First Review,Food Critic')
    ]
    sql = "INSERT INTO Users (name, email, password_hash, `role`, points, badges) VALUES (%s, %s, %s, %s, %s, %s)"
    cursor.executemany(sql, users_to_insert)
    conn.commit()
    print(f"Inserted {cursor.rowcount} users with hashed passwords.")


    # --- 2. Seed Dishes from CSV ---
    try:
        with open(CSV_FILE_PATH, mode='r') as file:
            reader = csv.DictReader(file)
            dishes_to_insert = []
            for row in reader:
                dishes_to_insert.append((row['name'], row['category'], float(row['price'])))
            
            cursor.execute("DELETE FROM Dishes")
            conn.commit()
            
            sql = "INSERT INTO Dishes (name, category, price) VALUES (%s, %s, %s)"
            cursor.executemany(sql, dishes_to_insert)
            conn.commit()
            print(f"Inserted {cursor.rowcount} dishes.")
    except Exception as e:
        print(f"Error seeding dishes: {e}")
        conn.rollback()


    # --- 3. Seed Reviews (Mock Data) ---
    cursor.execute("DELETE FROM Reviews")
    conn.commit()
    cursor.execute("SELECT id FROM Users WHERE role = 'student'")
    user_ids = [item[0] for item in cursor.fetchall()]
    cursor.execute("SELECT id FROM Dishes")
    dish_ids = [item[0] for item in cursor.fetchall()]

    if not user_ids or not dish_ids:
        print("Cannot seed reviews. No users or dishes found.")
    else:
        reviews_to_insert = []
        comments = [
            "Absolutely delicious, will order again!", "It was okay, not great.", 
            "Loved it! Best on campus.", "A bit cold, but tasted good.", "My favorite!", 
            "Not worth the price.", "Highly recommend this one.", "Could use more seasoning."
        ]
        for _ in range(50): # Create 50 mock reviews
            review = (
                random.choice(user_ids),
                random.choice(dish_ids),
                random.randint(2, 5),
                random.choice(comments)
            )
            reviews_to_insert.append(review)
        
        sql = "INSERT INTO Reviews (user_id, dish_id, rating, comment) VALUES (%s, %s, %s, %s)"
        cursor.executemany(sql, reviews_to_insert)
        conn.commit()
        print(f"Inserted {cursor.rowcount} mock reviews.")


    # --- 4. Seed Transactions (Mock Data for last 90 days) ---
    cursor.execute("DELETE FROM Transactions")
    conn.commit()
    transactions_to_insert = []
    
    if not user_ids or not dish_ids:
        print("Cannot seed transactions. No users or dishes found.")
    else:
        today = datetime.now().date()
        for _ in range(200): # Create 200 mock transactions
            transaction = (
                random.choice(user_ids),
                random.choice(dish_ids),
                today - timedelta(days=random.randint(0, 90))
            )
            transactions_to_insert.append(transaction)
            
        sql = "INSERT INTO Transactions (user_id, dish_id, transaction_date) VALUES (%s, %s, %s)"
        cursor.executemany(sql, transactions_to_insert)
        conn.commit()
        print(f"Inserted {cursor.rowcount} mock transactions.")

    cursor.close()
    conn.close()
    print("Database seeding complete.")


if __name__ == '__main__':
    seed_data()

