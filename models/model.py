import joblib
import mysql.connector
from sklearn.linear_model import LinearRegression
import numpy as np
from flask import Flask, render_template, request

app = Flask(__name__)

# Function to get a connection to the MySQL database
def get_db_connection():
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='flipdatabase'  # Update this if needed
    )
    return conn

# Function to fetch data from MySQL and train the model
def train_model():
    conn = get_db_connection()
    
    query = '''
    SELECT t.child, t.earning, tr.amount
    FROM tasks t
    JOIN transactions tr ON t.child = tr.child
    WHERE t.status = 'Completed' AND tr.type IN ('subscription', 'deposit', 'transfer');
    '''
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()

    if not data:  # If no data, print an error
        print("⚠️ No training data found in the database. Model training skipped!")
        return

    print("✅ Training data:", data)  # Debug: Print fetched data

    for d in data:
        d['earning'] = float(d['earning'])
        d['amount'] = float(d['amount'])

    X = np.array([[d['amount']] for d in data])
    y = np.array([d['earning'] for d in data])

    model = LinearRegression()
    model.fit(X, y)

    joblib.dump(model, 'patience_index_model.pkl')
    print("✅ Model trained and saved!")


# Function to load the trained model
def load_model():
    return joblib.load('patience_index_model.pkl')


# Function to predict the patience index for a given child
def predict_patience(child_id):
    model = load_model()
    
    if not model:
        return "Error: Model not loaded"

    conn = get_db_connection()

    # Fetch task and transaction data for the given child
    query = '''
    SELECT COALESCE(SUM(amount), 0) AS total_amount
    FROM transactions
    WHERE userid = %s;
    '''

    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, (child_id,))
    data = cursor.fetchone()
    conn.close()

    print(f"Child ID: {child_id}, Query Result: {data}")  # Debugging output

    if data:
        total_amount = data['total_amount']
        
        # Predict patience index using the model (for now, just use total amount ranges)
        if total_amount < 100:
            return 'Low'  # Low patience
        elif 100 <= total_amount <= 500:
            return 'Medium'  # Medium patience
        else:
            return 'High'  # High patience
    else:
        print("⚠️ No data found for the given child_id")  # Debug statement
        return None




@app.route('/')
def index():
    return render_template('index.html')


@app.route('/predict', methods=['POST'])
def predict():
    child_id = request.form['child_id']
    patience_index = predict_patience(child_id)

    if patience_index is not None:
        return render_template('result.html', child_id=child_id, patience_index=patience_index)
    else:
        return render_template('result.html', child_id=child_id, patience_index="No data found for this child")


if __name__ == "__main__":
    train_model()  # Train the model when the server starts
    app.run(debug=True)
