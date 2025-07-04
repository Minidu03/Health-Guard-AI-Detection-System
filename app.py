from flask import Flask, request, jsonify, Response, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import csv
import io
import joblib
import os
from flask_migrate import Migrate
from flask_login import UserMixin

#Initialize Flask app
app = Flask(__name__, instance_relative_config=True)
app.config['SECRET_KEY'] = 'your_secret_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///predictions.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


#Initialize extensions
db = SQLAlchemy(app)
CORS(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login_page"

#Load the health prediction model
model = joblib.load("health_guard_model.pkl")

#User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

#Prediction model
class Prediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    systolic = db.Column(db.Integer)
    diastolic = db.Column(db.Integer)
    heart_rate = db.Column(db.Integer)
    spo2 = db.Column(db.Integer)
    result = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

#Load user by ID
login_manager = LoginManager()
login_manager.init_app(app)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#Root
@app.route("/")
def home():
    return "✅ Health Guard AI is running!"

#Registration API
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Missing fields"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 400

    new_user = User(username=username)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User registered successfully!"})

#Login API
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        try:
            print("🔐 Login attempt received")
            data = request.get_json()
            username = data.get("username")
            password = data.get("password")
            print(f"Username: {username}, Password: {password}")

            user = User.query.filter_by(username=username).first()
            if user is None:
                print("❌ User not found")
                return jsonify({"error": "Invalid username"}), 401

            if not user.check_password(password):
                print("❌ Incorrect password")
                return jsonify({"error": "Invalid password"}), 401

            login_user(user)
            print("✅ Login success")
            return jsonify({"message": "Login successful!"})

        except Exception as e:
            print("💥 Server error:", e)
            return jsonify({"error": "Internal server error"}), 500

    return render_template("login.html")



#Logout
@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logged out!"})

#Predict Endpoint
@app.route("/predict", methods=["POST"])
@login_required
def predict():
    data = request.get_json()
    try:
        systolic = int(data.get("systolic_bp"))
        diastolic = int(data.get("diastolic_bp"))
        heart_rate = int(data.get("heart_rate"))
        spo2 = int(data.get("spo2"))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid input"}), 400

    input_data = [[systolic, diastolic, heart_rate, spo2]]
    prediction = model.predict(input_data)
    result = "RISK" if prediction[0] == 1 else "HEALTHY"

    entry = Prediction(
        systolic=systolic,
        diastolic=diastolic,
        heart_rate=heart_rate,
        spo2=spo2,
        result=result,
        user_id=current_user.id
    )
    db.session.add(entry)
    db.session.commit()
    return jsonify({"result": result})

#History
@app.route("/history", methods=["GET"])
@login_required
def history():
    predictions = Prediction.query.filter_by(user_id=current_user.id).order_by(Prediction.timestamp.desc()).all()
    return jsonify([{
        "timestamp": p.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "systolic": p.systolic,
        "diastolic": p.diastolic,
        "heart_rate": p.heart_rate,
        "spo2": p.spo2,
        "result": p.result
    } for p in predictions])

#Filtered History
@app.route("/history/filter", methods=["GET"])
@login_required
def filter_history():
    status = request.args.get("status")
    start = request.args.get("start_date")
    end = request.args.get("end_date")

    query = Prediction.query.filter_by(user_id=current_user.id)
    if status:
        query = query.filter_by(result=status.upper())
    if start and end:
        start_date = datetime.strptime(start, "%Y-%m-%d")
        end_date = datetime.strptime(end, "%Y-%m-%d")
        query = query.filter(Prediction.timestamp.between(start_date, end_date))

    predictions = query.order_by(Prediction.timestamp.desc()).all()
    return jsonify([{
        "timestamp": p.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "systolic": p.systolic,
        "diastolic": p.diastolic,
        "heart_rate": p.heart_rate,
        "spo2": p.spo2,
        "result": p.result
    } for p in predictions])

#CSV Export
@app.route("/download", methods=["GET"])
@login_required
def download_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Timestamp", "Systolic", "Diastolic", "Heart Rate", "SpO2", "Result"])

    predictions = Prediction.query.filter_by(user_id=current_user.id).order_by(Prediction.timestamp.desc()).all()
    for p in predictions:
        writer.writerow([
            p.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            p.systolic,
            p.diastolic,
            p.heart_rate,
            p.spo2,
            p.result
        ])

    output.seek(0)
    return Response(output, mimetype='text/csv',
                    headers={"Content-Disposition": "attachment;filename=predictions.csv"})

#HTML Pages
@app.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")

@app.route("/register", methods=["GET"])
def register_page():
    return render_template("register.html")

@app.route("/dashboard", methods=["GET"])
@login_required
def dashboard():
    return render_template("history.html")

#Start app
if __name__ == "__main__":
    os.makedirs(app.instance_path, exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
