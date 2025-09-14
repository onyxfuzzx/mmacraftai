import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score


df = pd.read_csv('large_dataset.csv')

features_to_diff = [
    'age', 'height', 'weight', 'reach',
    'SLpM_total', 'SApM_total', 'sig_str_acc_total',
    'td_acc_total', 'str_def_total', 'td_def_total',
    'sub_avg', 'td_avg',
    'wins_total', 'losses_total'
]

df_diff = pd.DataFrame()

for feat in features_to_diff:
    df_diff['diff_' + feat] = df['r_' + feat] - df['b_' + feat]

df_diff['target'] = (df['winner'] == 'Red').astype(int)

df_diff.dropna(inplace=True)

X = df_diff.drop('target', axis=1)
y = df_diff['target']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = LogisticRegression(random_state=42)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"Model accuracy: {accuracy:.2f}")

red_fighters = df[['r_fighter'] + ['r_' + feat for feat in features_to_diff]]
blue_fighters = df[['b_fighter'] + ['b_' + feat for feat in features_to_diff]]

red_fighters.columns = ['fighter'] + features_to_diff
blue_fighters.columns = ['fighter'] + features_to_diff

all_fighters = pd.concat([red_fighters, blue_fighters], ignore_index=True)

fighter_db = all_fighters.groupby('fighter').mean().reset_index()


def predict_winner(fighter_a, fighter_b):
    
    stats_a = fighter_db[fighter_db['fighter'] == fighter_a][features_to_diff]
    stats_b = fighter_db[fighter_db['fighter'] == fighter_b][features_to_diff]
    
    if stats_a.empty or stats_b.empty:
        return "One or both fighters not found in database."
    
    diff = stats_a.values - stats_b.values
    diff_df = pd.DataFrame(diff, columns=features_to_diff)
    diff_df.columns = ['diff_' + col for col in diff_df.columns]
    
    prob = model.predict_proba(diff_df)[0][1]
    if prob > 0.5:
        return f"{fighter_a} wins with probability {prob:.2f}"
    else:
        return f"{fighter_b} wins with probability {1-prob:.2f}"

print(predict_winner("Khabib Nurmagomedov", "Conor McGregor"))