This is the Patience_index model use to calculate the patience index of the kids
Following is the implementation and detail steps to follow to integrate this model
## ⚙ Database Configuration

Make sure your MySQL server is running and you have created a database.

In all database connection functions:

```python
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="your_password_here",  # <-- change this
    database="your_database_name_here"  # <-- change this
)

✅ Recommended:
Set your_password_here to your actual database password.

Set your_database_name_here to your actual project database name (e.g., user_db).


🟣 Features
Manual user creation via a web form (/create_user)

Automated user insertion via an external API (via cron job)

Machine Learning model training using Random Forest

Modular and clean project structure

Ready to integrate with quiz data when the actual quiz API is live

⚙ Manual User Creation
Run your Flask application:
python main.py

Then access:
http://localhost:5000


⚙ Automated User Insertion (via Cron Job)
When live, you can fetch user data from an API and insert it automatically.

Example script: fetch_and_insert_users.py

This script:

Calls the API for user and transaction data.

Inserts or updates users in the database.

-------------------------------------------------------------------------

🟣 Model Training
The main model training file is main.py.

It performs:
Data extraction from the database

Preprocessing (Label Encoding)

Model training (RandomForestRegressor)

Model saving via joblib

Run training manually:
python main.py
Or integrate into fetch_and_insert_users.py to run automatically after data insertion.

⚙ Installing Dependencies
pip install -r requirements.txt

flask
mysql-connector-python
pandas
scikit-learn
joblib


✨ Notes

⚠ The model will later use both user data and quiz data for more accurate predictions.

✅ Recommended: Use .env file to store sensitive credentials (passwords, API keys).

✅ Log all exceptions in production (file or service-based logging).

✅ For scalability, schedule model training frequency carefully based on data volume.

✅ Next Steps When Product Goes Live
Replace the test API URL inside fetch_and_insert_users.py with the real quiz API.
