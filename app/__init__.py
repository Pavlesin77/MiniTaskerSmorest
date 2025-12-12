import os
from datetime import timedelta
from flask import Flask
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager
from .extensions import db, migrate
from app.models.user import User
from app.models.task import Task
from flask_smorest import Api
from app.resources.user import blp as user_blueprint


def create_app():
    """Kreira i konfiguriše Flask aplikaciju"""
    # Učitaj .env fajl iz root direktorijuma
    load_dotenv(".env_postgres")

    app = Flask(__name__)

    # OpenAPI konfiguracija aplikacije.
    app.config["API_TITLE"] = "Mini Tasker API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"


    # Konfiguracija veze sa bazom
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Vreme trajanja access tokena
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=15)  # token važi 15 minuta
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")  # tajni ključ

    # Inicijalizacija JWT
    _jwt = JWTManager(app)

    # Povezivanje baze sa aplikacijom
    db.init_app(app)

    # povezuje Flask-Migrate sa aplikacijom i bazom
    migrate.init_app(app, db)

    api = Api(app)  # kreira API objekat
    api.register_blueprint(user_blueprint)  # registruje blueprint

    return app
