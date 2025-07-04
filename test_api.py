import requests

url = "http://127.0.0.1:5000/predict"

data = {
    "systolic_bp": 130,
    "diastolic_bp": 85,
    "heart_rate": 88,
    "spo2": 95
}

response = requests.post(url, json=data)

print("Result from AI:", response.json())
