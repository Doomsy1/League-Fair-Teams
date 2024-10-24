# app/__init__.py

from flask import Flask
from dotenv import load_dotenv
import os

def create_app():
    app = Flask(__name__)

    # Load environment variables
    load_dotenv()
    RIOT_API_KEY = os.getenv('RIOT_API_KEY')
    app.config['RIOT_API_KEY'] = RIOT_API_KEY

    app.secret_key = 'your_secret_key_here'  # Replace with a secure key in production

    # Register Blueprints
    with app.app_context():
        from . import routes
        app.register_blueprint(routes.routes)

    return app
