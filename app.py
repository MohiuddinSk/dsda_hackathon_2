from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector
import os
from datetime import datetime, timedelta
import random
from werkzeug.security import generate_password_hash, check_password_hash


# --- App Configuration ---
app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# --- Database Configuration ---
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'studentbite'),
    'password': os.getenv('DB_PASSWORD', 'password'),
    'database': os.getenv('DB_NAME', 'studentbite_db')
}

def get_db_connection():
    """Establishes a connection to the database."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print(f"Error connecting to database: {err}")
        return None

# --- Helper Functions ---
def query_db(query, args=(), one=False):
    """Executes a database query and returns results."""
    conn = get_db_connection()
    if not conn:
        return None 
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, args)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return (results[0] if results else None) if one else results

def execute_db(query, args=()):
    """Executes a database command (INSERT, UPDATE, DELETE)."""
    conn = get_db_connection()
    if not conn:
        return None
    cursor = conn.cursor()
    try:
        cursor.execute(query, args)
        conn.commit()
        last_id = cursor.lastrowid
    except mysql.connector.Error as err:
        print(f"DB Execution Error: {err}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()
    return last_id if 'INSERT' in query.upper() else True


# --- API Endpoints ---

# Authentication Features
@app.route('/api/register', methods=['POST'])
def register_user():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not all([username, email, password]):
        return jsonify({"error": "Missing required fields"}), 400

    # Check if username or email already exists
    if query_db("SELECT * FROM Users WHERE name = %s", (username,), one=True):
        return jsonify({"error": "Username already taken."}), 409
    if query_db("SELECT * FROM Users WHERE email = %s", (email,), one=True):
        return jsonify({"error": "Email already registered."}), 409
        
    password_hash = generate_password_hash(password)
    
    sql = "INSERT INTO Users (name, email, password_hash) VALUES (%s, %s, %s)"
    user_id = execute_db(sql, (username, email, password_hash))

    if user_id:
        return jsonify({"message": "User registered successfully", "user_id": user_id}), 201
    else:
        return jsonify({"error": "Registration failed"}), 500


@app.route('/api/login', methods=['POST'])
def login_user():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not all([username, password]):
        return jsonify({"error": "Username and password are required"}), 400
        
    # Special case for admin login
    if username == 'admin' and password == 'admin@1234':
        admin_user = query_db("SELECT id, name, email, role, points, badges FROM Users WHERE name = 'admin'", one=True)
        if not admin_user: # Failsafe in case admin is not in DB
             return jsonify({"error": "Admin account not found. Please seed the database."}), 404
        return jsonify({"message": "Admin login successful", "user": admin_user}), 200

    user = query_db("SELECT * FROM Users WHERE name = %s", (username,), one=True)

    if user and check_password_hash(user['password_hash'], password):
        # Don't send the password hash to the client
        del user['password_hash']
        return jsonify({"message": "Login successful", "user": user}), 200
    else:
        return jsonify({"error": "Invalid username or password"}), 401


# Student-Facing Features

@app.route('/api/dishes', methods=['GET'])
def get_dishes():
    """Get all dishes with average rating and review count."""
    sql = """
        SELECT d.*, COALESCE(AVG(r.rating), 0) as avg_rating, COUNT(r.id) as review_count
        FROM Dishes d
        LEFT JOIN Reviews r ON d.id = r.dish_id
        GROUP BY d.id
    """
    dishes = query_db(sql)
    return jsonify(dishes)

@app.route('/api/dishes/top-rated', methods=['GET'])
def get_top_rated_dishes():
    """Get the top 3 rated dishes."""
    sql = """
        SELECT d.*, AVG(r.rating) as avg_rating, COUNT(r.id) as review_count
        FROM Dishes d
        JOIN Reviews r ON d.id = r.dish_id
        GROUP BY d.id
        ORDER BY avg_rating DESC
        LIMIT 3
    """
    dishes = query_db(sql)
    return jsonify(dishes)

@app.route('/api/dishes/recommendations/<int:user_id>', methods=['GET'])
def get_recommendations(user_id):
    """Simple recommendation system based on user's top-rated categories."""
    fav_category_query = """
        SELECT d.category
        FROM Reviews r
        JOIN Dishes d ON r.dish_id = d.id
        WHERE r.user_id = %s
        GROUP BY d.category
        ORDER BY AVG(r.rating) DESC
        LIMIT 1
    """
    fav_category_result = query_db(fav_category_query, (user_id,), one=True)
    
    if not fav_category_result:
        return get_top_rated_dishes()

    fav_category = fav_category_result['category']

    recs_query = """
        SELECT d.*, COALESCE(AVG(r.rating), 0) as avg_rating, COUNT(r.id) as review_count
        FROM Dishes d
        LEFT JOIN Reviews r ON d.id = r.dish_id
        WHERE d.category = %s AND d.id NOT IN (
            SELECT dish_id FROM Reviews WHERE user_id = %s
        )
        GROUP BY d.id
        ORDER BY avg_rating DESC
        LIMIT 3
    """
    recommendations = query_db(recs_query, (fav_category, user_id))
    return jsonify(recommendations)

@app.route('/api/reviews/<int:dish_id>', methods=['GET'])
def get_reviews_for_dish(dish_id):
    """Get all reviews for a specific dish."""
    sql = """
        SELECT r.id, r.rating, r.comment, r.timestamp, u.name as user_name
        FROM Reviews r
        JOIN Users u ON r.user_id = u.id
        WHERE r.dish_id = %s
        ORDER BY r.timestamp DESC
    """
    reviews = query_db(sql, (dish_id,))
    return jsonify(reviews)


@app.route('/api/reviews', methods=['POST'])
def add_review():
    """Add a new review and handle gamification."""
    data = request.json
    user_id = data.get('user_id')
    dish_id = data.get('dish_id')
    rating = data.get('rating')
    comment = data.get('comment')

    if not all([user_id, dish_id, rating, comment]):
        return jsonify({"error": "Missing data"}), 400

    insert_sql = "INSERT INTO Reviews (user_id, dish_id, rating, comment) VALUES (%s, %s, %s, %s)"
    review_id = execute_db(insert_sql, (user_id, dish_id, rating, comment))
    
    if not review_id:
        return jsonify({"error": "Failed to add review"}), 500

    points_to_add = 10
    update_points_sql = "UPDATE Users SET points = points + %s WHERE id = %s"
    execute_db(update_points_sql, (points_to_add, user_id))

    user_reviews_count = query_db("SELECT COUNT(*) as count FROM Reviews WHERE user_id = %s", (user_id,), one=True)['count']
    user_data = query_db("SELECT badges FROM Users WHERE id = %s", (user_id,), one=True)
    current_badges = user_data['badges'].split(',') if user_data and user_data['badges'] else []
    
    new_badge = None
    if user_reviews_count >= 1 and "First Review" not in current_badges:
        new_badge = "First Review"
    elif user_reviews_count >= 10 and "Food Critic" not in current_badges:
        new_badge = "Food Critic"
    elif user_reviews_count >= 25 and "Gourmet" not in current_badges:
        new_badge = "Gourmet"

    if new_badge:
        current_badges.append(new_badge)
        update_badge_sql = "UPDATE Users SET badges = %s WHERE id = %s"
        execute_db(update_badge_sql, (','.join(current_badges), user_id))

    return jsonify({"message": "Review added successfully", "review_id": review_id}), 201


@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    """Get the top 10 users by points."""
    sql = "SELECT id, name, points, badges FROM Users WHERE role = 'student' ORDER BY points DESC LIMIT 10"
    users = query_db(sql)
    for user in users:
        user['badges'] = user['badges'].split(',') if user['badges'] else []
    return jsonify(users)

@app.route('/api/chatbot', methods=['POST'])
def handle_chatbot():
    """Simple keyword-based chatbot."""
    message = request.json.get('message', '').lower()
    reply = "I'm not sure how to answer that. You can ask about canteen timings, today's specials, or payment methods."
    
    if 'timing' in message or 'open' in message or 'close' in message:
        reply = "The canteen is open from 8:00 AM to 6:00 PM, Monday to Saturday."
    elif 'special' in message or 'today' in message:
        special = query_db("SELECT name FROM Dishes ORDER BY RAND() LIMIT 1", one=True)
        if special:
            reply = f"Today's special is {special['name']}! It's delicious."
        else:
            reply = "I couldn't find today's special, but everything is great!"
    elif 'payment' in message or 'pay' in message or 'card' in message:
        reply = "We accept cash, credit/debit cards, and mobile payment apps."
    elif 'hello' in message or 'hi' in message:
        reply = "Hello! How can I help you with the canteen today?"
        
    return jsonify({'reply': reply})


# Admin-Facing Features

@app.route('/api/admin/popularity', methods=['GET'])
def get_dish_popularity():
    sql = """
        SELECT d.name, COUNT(r.id) as review_count
        FROM Dishes d
        LEFT JOIN Reviews r ON d.id = r.dish_id
        GROUP BY d.id
        ORDER BY review_count DESC
        LIMIT 10
    """
    data = query_db(sql)
    return jsonify(data)

@app.route('/api/admin/quality', methods=['GET'])
def get_dish_quality():
    sql = """
        SELECT d.name, COALESCE(AVG(r.rating), 0) as avg_rating
        FROM Dishes d
        LEFT JOIN Reviews r ON d.id = r.dish_id
        GROUP BY d.id
        HAVING avg_rating > 0
        ORDER BY avg_rating DESC
    """
    data = query_db(sql)
    return jsonify(data)

@app.route('/api/admin/forecasting', methods=['GET'])
def get_demand_forecasting():
    sql = """
        SELECT dish_id, COUNT(*) as daily_sales
        FROM Transactions
        WHERE transaction_date >= CURDATE() - INTERVAL 30 DAY
        GROUP BY dish_id
        ORDER BY daily_sales DESC
        LIMIT 1
    """
    top_dish_sales = query_db(sql, one=True)
    
    avg_daily_sales = (top_dish_sales['daily_sales'] / 30) if top_dish_sales else 5

    labels = [(datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
    predictions = [round(avg_daily_sales * (1 + random.uniform(-0.1, 0.1))) for _ in range(7)]
    
    return jsonify({"labels": labels, "predictions": predictions})

@app.route('/api/admin/trends', methods=['GET'])
def get_trends():
    monthly_trend_sql = """
        SELECT d.name, COUNT(r.id) as review_count
        FROM Reviews r
        JOIN Dishes d ON r.dish_id = d.id
        WHERE r.timestamp >= CURDATE() - INTERVAL 30 DAY
        GROUP BY d.id
        ORDER BY review_count DESC
        LIMIT 1
    """
    monthly_trend = query_db(monthly_trend_sql, one=True) or {"name": "N/A", "review_count": 0}

    current_month = datetime.now().month
    if current_month in [12, 1, 2]:
        season, category = "Winter", "hot beverage"
    elif current_month in [3, 4, 5]:
        season, category = "Spring", "salad"
    elif current_month in [6, 7, 8]:
        season, category = "Summer", "cold beverage"
    else:
        season, category = "Autumn", "soup"

    seasonal_favorite = query_db(
        "SELECT name FROM Dishes WHERE category = %s ORDER BY RAND() LIMIT 1",
        (category,), one=True
    ) or {"name": "N/A"}
    seasonal_favorite['season'] = season

    return jsonify({
        "monthly_trend": monthly_trend,
        "seasonal_favorite": seasonal_favorite
    })

@app.route('/api/admin/revenue', methods=['GET'])
def get_revenue_insights():
    sql = """
        SELECT SUM(d.price) as total_revenue
        FROM Transactions t
        JOIN Dishes d ON t.dish_id = d.id
        WHERE t.transaction_date >= CURDATE() - INTERVAL 30 DAY
    """
    total_revenue = query_db(sql, one=True)['total_revenue'] or 0

    top_earner_sql = """
        SELECT d.name, SUM(d.price) as revenue
        FROM Transactions t
        JOIN Dishes d ON t.dish_id = d.id
        GROUP BY d.id
        ORDER BY revenue DESC
        LIMIT 1
    """
    top_earner = query_db(top_earner_sql, one=True) or {"name": "N/A", "revenue": 0}
    
    return jsonify({
        "total_revenue": total_revenue,
        "top_earner": top_earner
    })

@app.route('/api/admin/heatmap', methods=['GET'])
def get_feedback_heatmap():
    points = []
    for _ in range(100):
        points.append({
            "x": random.randint(10, 790),
            "y": random.randint(10, 390),
            "value": random.randint(1, 5)
        })
    return jsonify({"points": points})


if __name__ == '__main__':
    app.run(debug=True, port=5000)

