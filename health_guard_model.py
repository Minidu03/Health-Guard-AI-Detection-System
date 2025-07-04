import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report

data = {
    'systolic_bp': [120, 150, 90, 140, 130, 160],
    'diastolic_bp': [80, 95, 60, 90, 85, 100],
    'heart_rate': [72, 90, 65, 100, 75, 110],
    'spo2': [98, 95, 99, 91, 96, 89],
    'label': [0, 1, 0, 1, 0, 1]  
}

df = pd.DataFrame(data)


X = df.drop('label', axis=1)
y = df['label']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = LogisticRegression()
model.fit(X_train, y_train)


y_pred = model.predict(X_test)
print("🔍 Classification Report:")
print(classification_report(y_test, y_pred))


import joblib

joblib.dump(model, 'health_guard_model.pkl')
print("✅ Model saved as health_guard_model.pkl")

