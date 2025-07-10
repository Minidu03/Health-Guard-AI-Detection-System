from flask import Flask, render_template, request, redirect, session
import pickle, numpy as np
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to something strong!

# 🧠 Load ML model
model = pickle.load(open('health_model.pkl', 'rb'))

# 🔐 Hardcoded admin credentials
ADMIN_USER = 'admin'
ADMIN_PASS = 'health123'

# 🩺 Symptom database
symptom_db = {
    "cough": {"disease": "Common Cold", "probability": "80%",
              "precautions": ["Rest", "Hydrate", "Lozenges", "Avoid cold air"]},
    "fever": {"disease": "Flu", "probability": "75%",
              "precautions": ["Paracetamol", "Warm fluids", "Rest", "Monitor temp"]},
    "fatigue": {"disease": "Anemia", "probability": "65%",
                "precautions": ["Iron-rich foods", "Avoid exertion", "Consult doctor", "Track diet"]}
}

# ---------------- ROUTES ----------------

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/auth', methods=['POST'])
def auth():
    if request.form['username'] == ADMIN_USER and request.form['password'] == ADMIN_PASS:
        session['logged_in'] = True
        return redirect('/dashboard')
    return "<h3>Invalid credentials</h3>"

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect('/')
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        bp = int(request.form['bp'])
        hr = int(request.form['hr'])
        oxygen = int(request.form['oxygen'])

        prediction = model.predict(np.array([[bp, hr, oxygen]]))
        status = "At Risk 🚨" if prediction[0] == 1 else "Healthy ✅"
        return render_template('result.html', prediction=status)

    except Exception as e:
        return f"<h3>Error during prediction: {str(e)}</h3>"

@app.route('/symptom', methods=['POST'])
def symptom():
    name = request.form['name']
    age = request.form['age']
    address = request.form['address']
    symptoms = request.form['symptoms'].lower().split(',')

    results, labels, probs = [], [], []

    for s in symptoms:
        key = s.strip()
        if key in symptom_db:
            entry = symptom_db[key]
            results.append({
                "disease": entry["disease"],
                "probability": entry["probability"],
                "precautions": entry["precautions"]
            })
            labels.append(entry["disease"])
            probs.append(int(entry["probability"].replace('%', '')))

    # ✅ Only add fallback results — do NOT overwrite patient info
    if not results:
        labels = ['Cold', 'Flu', 'Anemia']
        probs = [80, 75, 65]
        results = [
            {"disease": "Cold", "probability": "80%", "precautions": ["Rest", "Tea", "Sleep", "Steam"]},
            {"disease": "Flu", "probability": "75%", "precautions": ["Medicine", "Hydration", "Rest", "Monitor temp"]},
            {"disease": "Anemia", "probability": "65%", "precautions": ["Iron-rich foods", "Low stress", "Check blood", "Doctor"]}
        ]
        # ❌ DO NOT overwrite name, age, address here

    return render_template('symptom_result.html',
                           name=name, age=age, address=address,
                           results=results, labels=labels, probs=probs)


symptom_db = {
    "fever": {
        "disease": "Flu",
        "probability": "85%",
        "precautions": [
            "Stay hydrated",
            "Take paracetamol",
            "Rest in a cool place",
            "Consult a doctor if persistent"
        ]
    },
    "cough": {
        "disease": "Bronchitis",
        "probability": "75%",
        "precautions": [
            "Use cough syrup",
            "Avoid cold drinks",
            "Drink warm fluids",
            "Use a humidifier"
        ]
    },
    "fatigue": {
        "disease": "Anemia",
        "probability": "70%",
        "precautions": [
            "Eat iron-rich foods",
            "Take iron supplements",
            "Reduce stress",
            "Avoid overexertion"
        ]
    },
    "headache": {
        "disease": "Migraine",
        "probability": "65%",
        "precautions": [
            "Avoid strong lights",
            "Take prescribed meds",
            "Sleep well",
            "Stay hydrated"
        ]
    },
    "nausea": {
        "disease": "Food Poisoning",
        "probability": "80%",
        "precautions": [
            "Avoid solid food",
            "Drink oral rehydration salts",
            "Rest",
            "Seek medical help if severe"
        ]
    }
}


# ---------------- ENTRY POINT ----------------

if __name__ == '__main__':
    app.run(debug=True)
