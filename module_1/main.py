from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
import pickle
import os
import warnings 
warnings.filterwarnings("ignore")

app = Flask(__name__)

# Calculate BMI function
def calculate_bmi(height, weight):
    return weight / ((height / 100) ** 2)

# Load or train model
def get_model():
    model_path = 'fightfit_model.pkl'
    encoders_path = 'fightfit_encoders.pkl'
    
    if os.path.exists(model_path) and os.path.exists(encoders_path):
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        with open(encoders_path, 'rb') as f:
            encoders = pickle.load(f)
        le_gender, le_experience, le_goal, le_injury = encoders
    else:
        df = load_data()
        model, le_gender, le_experience, le_goal, le_injury = train_model(df)
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        with open(encoders_path, 'wb') as f:
            pickle.dump((le_gender, le_experience, le_goal, le_injury), f)
    
    return model, le_gender, le_experience, le_goal, le_injury

# Load model and encoders once at startup
model, le_gender, le_experience, le_goal, le_injury = get_model()

@app.route('/')
def index():
    return render_template('index.html', 
                          experience_levels=list(le_experience.classes_),
                          goals=list(le_goal.classes_),
                          injury_history=list(le_injury.classes_))

@app.route('/predict', methods=['POST'])
def predict():
    # Get form data
    data = request.get_json()
    age = int(data['age'])
    height = int(data['height'])
    weight = int(data['weight'])
    experience = data['experience']
    goal = data['goal']
    injury_history = data['injury_history']
    
    # Calculate BMI
    bmi = calculate_bmi(height, weight)
    
    # Encode inputs
    gender_encoded = le_gender.transform(['Male'])[0]  # Default to Male
    experience_encoded = le_experience.transform([experience])[0]
    goal_encoded = le_goal.transform([goal])[0]
    injury_encoded = le_injury.transform([injury_history])[0]
    
    # Prepare input data
    input_data = np.array([[age, gender_encoded, bmi, experience_encoded, goal_encoded, injury_encoded]])
    
    # Make prediction
    prediction = model.predict(input_data)[0]
    
    # Format results
    results = {
        'bmi': round(bmi, 1),
        'cardio': round(prediction[0]),
        'skill': round(prediction[1]),
        'strength': round(prediction[2]),
        'agility': round(prediction[3]),
        'recovery': round(prediction[4]),
        'duration': round(prediction[5])
    }
    
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)