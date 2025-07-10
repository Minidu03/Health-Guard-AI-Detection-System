import pandas as pd
from sklearn.linear_model import LogisticRegression
import pickle

data = {
    'bp': [120, 140, 100, 130],
    'hr': [80, 100, 70, 90],
    'oxygen': [98, 92, 99, 91],
    'label': [0, 1, 0, 1]
}

df = pd.DataFrame(data)
X = df[['bp', 'hr', 'oxygen']]
y = df['label']

model = LogisticRegression()
model.fit(X, y)

with open('health_model.pkl', 'wb') as f:
    pickle.dump(model, f)



