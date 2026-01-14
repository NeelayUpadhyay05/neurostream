from flask import Flask
from backend.routes import api  # Imports the Blueprint from your api.py file

# Initialize the Flask Application
app = Flask(__name__)

# Register the routes from api.py
app.register_blueprint(api)

if __name__ == "__main__":
    print("--- STARTING NEUROSTREAM ---")
    # Host '0.0.0.0' makes it accessible within Docker (Required for Hugging Face)
    # Port 7860 is the specific port Hugging Face Spaces open by default
    app.run(host='0.0.0.0', port=7860)