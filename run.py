from app import app, db
import webbrowser
import threading

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/login")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  

    
    threading.Timer(1.0, open_browser).start()

    app.run(debug=True)
