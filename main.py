from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from flask import Flask, render_template

import joblib

app = Flask(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'flipdatabase'
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
        return None

def drop_all_tables():
    conn = get_db_connection()
    if conn is None:
        return

    try:
        cursor = conn.cursor()
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        for table in tables:
            cursor.execute(f"DROP TABLE IF EXISTS {table[0]}")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        conn.commit()
        print("All tables dropped successfully")
    except Error as e:
        print(f"Error dropping tables: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def create_tables():
    conn = get_db_connection()
    if conn is None:
        return

    try:
        cursor = conn.cursor()

        # Create Users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            age INT NOT NULL
        )
        """)

        # Create Quiz Questions table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_questions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            question TEXT NOT NULL,
            options TEXT NOT NULL
        )
        """)

        # Create Quiz Responses table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_responses (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            question_id INT NOT NULL,
            response VARCHAR(50) NOT NULL,
            patience_score INT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (question_id) REFERENCES quiz_questions(id) ON DELETE CASCADE
        )
        """)

        conn.commit()
        print("Tables created successfully")
    except Error as e:
        print(f"Error creating tables: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

        

def insert_initial_questions():
    conn = get_db_connection()
    if conn is None:
        return

    try:
        cursor = conn.cursor()
        questions = [
            ("You see a cool new avatar. Do you buy it now or wait until the next Flip Store sale?", "buy now,wait"),
            ("You can get 20 Flip Dollars for watching an ad or 100 Flip Dollars for completing a 3-day streak. What do you choose?", "ad,streak"),
            ("You have 500 Flip Dollars. Do you buy a fun item now or invest in a savings goal that doubles in 7 days?", "buy,invest")
        ]
        
        cursor.execute("SELECT COUNT(*) FROM quiz_questions")
        count = cursor.fetchone()[0]
        
        if count == 0:
            cursor.executemany("INSERT INTO quiz_questions (question, options) VALUES (%s, %s)", questions)
            conn.commit()
            print("Initial questions inserted successfully")
        else:
            print("Questions already exist, skipping insertion")
    except Error as e:
        print(f"Error inserting initial questions: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def calculate_patience_score(question_id, response):
    patience_scores = {
        1: {"wait": 10, "buy now": 5},
        2: {"streak": 10, "ad": 5},
        3: {"invest": 10, "buy": 5},
        4: {"tomorrow": 10, "now": 5},
        5: {"wait": 10, "now": 5},
        6: {"big": 10, "small": 5},
        7: {"double": 10, "keep": 5}
    }
    return patience_scores.get(question_id, {}).get(response, 0)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/create_user', methods=['GET', 'POST'])
def create_user():
    if request.method == 'POST':
        username = request.form.get('username')
        age = request.form.get('age')
        
        if not username or not age:
            return render_template('create_user.html', error="Username and age are required")

        conn = get_db_connection()
        if conn is None:
            return render_template('create_user.html', error="Database connection failed")

        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, age) VALUES (%s, %s)", (username, age))
            conn.commit()

            # Get user ID
            user_id = cursor.lastrowid

            return render_template('create_user.html', success=f"User {username} created successfully with User ID: {user_id}", user_id=user_id)
        except Error as e:
            return render_template('create_user.html', error=str(e))
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    return render_template('create_user.html')

@app.route('/submit_quiz', methods=['GET', 'POST'])
def submit_quiz():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        responses = {
            '1': request.form.get('question1'),
            '2': request.form.get('question2'),
            '3': request.form.get('question3')
        }
        
        if not user_id or not all(responses.values()):
            return render_template('submit_quiz.html', error="User ID and all responses are required")

        conn = get_db_connection()
        if conn is None:
            return render_template('submit_quiz.html', error="Database connection failed")

        try:
            cursor = conn.cursor()
            for question_id, response in responses.items():
                patience_score = calculate_patience_score(int(question_id), response)
                cursor.execute("""
                INSERT INTO quiz_responses (user_id, question_id, response, patience_score)
                VALUES (%s, %s, %s, %s)
                """, (user_id, question_id, response, patience_score))
            conn.commit()
            return render_template('submit_quiz.html', success="Quiz submitted successfully")
        except Error as e:
            return render_template('submit_quiz.html', error=str(e))
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    return render_template('submit_quiz.html')

@app.route('/train_model')
def train_model():
    conn = get_db_connection()
    if conn is None:
        return render_template('train_model.html', error="Database connection failed")

    try:
        query = "SELECT user_id, question_id, response, patience_score FROM quiz_responses"
        df = pd.read_sql(query, conn)
        
        if df.empty:
            return render_template('train_model.html', error="No data available to train the model")
        
        le = LabelEncoder()
        df['response_encoded'] = le.fit_transform(df['response'])
        
        X = df[['user_id', 'question_id', 'response_encoded']]
        y = df['patience_score']
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        
        joblib.dump(model, 'patience_model.joblib')
        joblib.dump(le, 'label_encoder.joblib')
        
        return render_template('train_model.html', success="Model trained successfully")
    except Error as e:
        return render_template('train_model.html', error=str(e))
    finally:
        if conn.is_connected():
            conn.close()


@app.route('/predict_patience', methods=['GET', 'POST'])
def predict_patience():
    if request.method == 'POST':
        user_id = request.form.get('user_id')

        if not user_id:
            return render_template('predict_patience.html', error="User ID is required")

        conn = get_db_connection()
        if conn is None:
            return render_template('predict_patience.html', error="Database connection failed")

        try:
            cursor = conn.cursor(dictionary=True)

            # GET USERNAME FROM DATABASE
            cursor.execute("SELECT username FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()

            if user is None:
                return render_template('predict_patience.html', error="User not found")

            user_name = user['username'] 


            cursor.execute("""
            SELECT question_id, response
            FROM quiz_responses
            WHERE user_id = %s
            """, (user_id,))
            user_responses = cursor.fetchall()

            if not user_responses:
                return render_template('predict_patience.html', error="No quiz data found for this user")

            model = joblib.load('patience_model.joblib')
            le = joblib.load('label_encoder.joblib')

            X_pred = pd.DataFrame([(user_id, r['question_id'], le.transform([r['response']])[0])
                                   for r in user_responses],
                                  columns=['user_id', 'question_id', 'response_encoded'])

            patience_scores = model.predict(X_pred)
            average_patience_score = patience_scores.mean()

            return render_template('predict_patience.html', user_id=user_id, user_name=user_name, patience_index=average_patience_score)
        except Error as e:
            return render_template('predict_patience.html', error=str(e))
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    return render_template('predict_patience.html')


if __name__ == '__main__':
    app.run(debug=True)
