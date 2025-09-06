Student Bite - Canteen Review Platform
Welcome to Student Bite! This is a full-stack web application that allows students to rate and review canteen food, and provides an analytics dashboard for administrators.

Tech Stack
Frontend: React (served from a single HTML file with CDN links)

Backend: Python (Flask)

Database: MySQL

Styling: Tailwind CSS

Setup Instructions
Follow these steps carefully to get the application running locally.

1. Prerequisites
Python 3.x: Ensure you have Python installed.

MySQL Server: You need a running MySQL server instance. You can install it from the official MySQL website.

Pip: Python's package installer.

2. Database Setup
Connect to MySQL: Open your MySQL client (e.g., MySQL Workbench, or the mysql command line).

Run the Schema Script: Execute the entire schema.sql script. This will:

Create the studentbite_db database.

Create a user studentbite with the password password.

Create the necessary tables (Users, Dishes, Reviews, Transactions).

Insert some initial sample users.

You can run it from the command line like this (you will be prompted for your root password):

mysql -u root -p < schema.sql

3. Backend Setup
Navigate to the Project Directory: Open your terminal and go to the folder containing these files.

Create a Virtual Environment (Recommended):

python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

Install Python Dependencies:

pip install Flask Flask-Cors mysql-connector-python pandas

Seed the Database: Run the seed.py script to populate your database with dishes from the CSV and create mock reviews and transactions.

python seed.py

You should see confirmation messages that dishes, reviews, and transactions have been inserted.

Run the Flask Server:

python app.py

Your backend API is now running at http://127.0.0.1:5000. Keep this terminal window open.

4. Frontend Setup
Open the Frontend File: Open student_bite_frontend.html directly in your web browser (e.g., Google Chrome, Firefox).

Interact with the App: You can now use the application!

Navigate through the pages using the navigation bar.

Click on dishes to view and add reviews.

Explore the leaderboard and the admin analytics dashboard.

Try out the Canteen Buddy chatbot.

File Overview
student_bite_frontend.html: The single-file React application. It contains all UI components, pages, logic, and styling.

app.py: The Flask backend server. It defines all the API endpoints that the frontend communicates with.

schema.sql: The SQL script to set up your MySQL database and tables.

canteen_data.csv: Sample data for canteen dishes.

seed.py: A script to populate the database using the CSV data and generate mock data.

data_cleaning.py: A sample utility script to demonstrate how you could preprocess new CSV data before uploading.

README.md: This file, providing setup and project information.