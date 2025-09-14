from flask import Flask, render_template, request
import pandas as pd
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import io

app = Flask(__name__)

# Load and preprocess data
def load_data():
    # In a real application, you would load from the actual CSV file
    # For this example, we'll create a small sample dataset
    data = pd.read_csv("large_dataset.csv")
    return pd.DataFrame(data)

# Initialize data and model
df = load_data()
model = None
fighter_db = None

def train_model():
    global model, fighter_db
    
    # List of pre-fight stats to use for differences
    features_to_diff = [
        'age', 'height', 'wins_total', 'losses_total',
        'SLpM_total', 'SApM_total'
    ]

    # Create a new DataFrame for training with difference features
    df_diff = pd.DataFrame()

    # Compute differences for each feature
    for feat in features_to_diff:
        df_diff['diff_' + feat] = df['r_' + feat] - df['b_' + feat]

    # Target variable: 1 if red wins, 0 if blue wins
    df_diff['target'] = (df['winner'] == 'Red').astype(int)

    # Drop rows with missing values if any
    df_diff.dropna(inplace=True)

    # Split the data into features and target
    X = df_diff.drop('target', axis=1)
    y = df_diff['target']

    # Train a logistic regression model
    model = LogisticRegression(random_state=42)
    model.fit(X, y)

    # Build a database of fighter average stats
    # First, extract red and blue fighter stats
    red_fighters = df[['r_fighter'] + ['r_' + feat for feat in features_to_diff]]
    blue_fighters = df[['b_fighter'] + ['b_' + feat for feat in features_to_diff]]

    # Rename columns to remove prefix
    red_fighters.columns = ['fighter'] + features_to_diff
    blue_fighters.columns = ['fighter'] + features_to_diff

    # Combine red and blue data
    all_fighters = pd.concat([red_fighters, blue_fighters], ignore_index=True)

    # Group by fighter name and compute mean stats
    fighter_db = all_fighters.groupby('fighter').mean().reset_index()
    
    # Save model and fighter database
    joblib.dump(model, 'model.pkl')
    fighter_db.to_csv('fighter_database.csv', index=False)

# Train model on startup
train_model()

@app.route('/')
def index():
    # Get list of all fighters for the dropdown
    fighters = sorted(pd.concat([df['r_fighter'], df['b_fighter']]).unique())
    return render_template('index.html', fighters=fighters)

@app.route('/predict', methods=['POST'])
def predict():
    fighter_a = request.form['fighter_a']
    fighter_b = request.form['fighter_b']
    
    # Get stats for both fighters
    stats_a = fighter_db[fighter_db['fighter'] == fighter_a].iloc[0][1:]
    stats_b = fighter_db[fighter_db['fighter'] == fighter_b].iloc[0][1:]
    
    # Compute differences: fighter_a as red, fighter_b as blue
    diff = stats_a.values - stats_b.values
    diff_df = pd.DataFrame([diff], columns=['diff_age', 'diff_height', 'diff_wins_total', 
                                          'diff_losses_total', 'diff_SLpM_total', 'diff_SApM_total'])
    
    # Predict probability
    prob = model.predict_proba(diff_df)[0][1]  # Probability that fighter_a wins
    
    # Prepare data for visualization
    comparison_data = []
    features = ['Age', 'Height', 'Total Wins', 'Total Losses', 'Strikes Landed per Min', 'Strikes Absorbed per Min']
    
    for i, feature in enumerate(features):
        comparison_data.append({
            'feature': feature,
            'fighter_a': round(stats_a.iloc[i], 2),
            'fighter_b': round(stats_b.iloc[i], 2)
        })
    
    if prob > 0.5:
        winner = fighter_a
        winner_prob = round(prob * 100, 2)
        loser_prob = round((1 - prob) * 100, 2)
    else:
        winner = fighter_b
        winner_prob = round((1 - prob) * 100, 2)
        loser_prob = round(prob * 100, 2)
    
    return render_template('result.html', 
                         fighter_a=fighter_a, 
                         fighter_b=fighter_b,
                         winner=winner,
                         winner_prob=winner_prob,
                         loser_prob=loser_prob,
                         comparison_data=comparison_data)

if __name__ == '__main__':
    app.run(debug=True)