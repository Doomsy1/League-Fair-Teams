# app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate  # Import Flask-Migrate
from dotenv import load_dotenv
import os

db = SQLAlchemy()
migrate = Migrate()  # Initialize Flask-Migrate

def create_app():
    # Load environment variables from .env file
    load_dotenv()

    app = Flask(__name__)

    # Configure the SQLAlchemy part of the app instance
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///summoners.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize the database and migration
    db.init_app(app)
    migrate.init_app(app, db)  # Initialize Flask-Migrate with app and db

    # Import and register blueprints
    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app
