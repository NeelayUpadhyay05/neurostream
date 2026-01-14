from flask import Flask
from backend.routes import api

# --- CREATE APP GLOBALLY ---
# Gunicorn needs this 'app' variable to be accessible at the top level
app = Flask(__name__)

# Register the routes from backend/routes.py
app.register_blueprint(api)

if __name__ == '__main__':
    # This block only runs on your laptop
    print("🚀 Starting NeuroStream v2...")
    app.run(debug=True, port=5000)