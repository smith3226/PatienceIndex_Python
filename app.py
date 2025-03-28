from flask import Flask, render_template, request
from models.model import predict_patience  # Ensure this function exists

app = Flask(__name__)

# Home route - displays the form
@app.route('/')
def index():
    return render_template('index.html')

# Form submission route - Predict patience index
@app.route('/predict', methods=['POST'])
def predict():
    child_id = request.form.get('child_id') 
    # Get input from form
    if not child_id:
        return "Child ID is required", 400  # Return error if no input

    try:
        patience_index = predict_patience(int(child_id))  # Convert to int and predict
        return render_template('result.html', child_id=child_id, patience_index=patience_index)
    except Exception as e:
        return f"Error: {str(e)}", 500  # Handle prediction errors

if __name__ == '__main__':
    app.run(debug=True)
