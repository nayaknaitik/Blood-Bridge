"""
Blood Bridge Flask application factory.
Uses DynamoDB for persistence (boto3).
"""
import os
from flask import Flask
from flask_cors import CORS

from config import SECRET_KEY, LOG_DIR, AWS_REGION
from app.services.dynamodb_client import get_dynamodb_tables


def create_app(config_overrides=None):
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
        static_url_path="/static",
    )
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or SECRET_KEY
    app.config["AWS_REGION"] = os.environ.get("AWS_REGION") or AWS_REGION

    if config_overrides:
        app.config.update(config_overrides)

    CORS(
        app,
        supports_credentials=True,
        origins=[
            "http://localhost:5000",
            "http://127.0.0.1:5000",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_headers=["Content-Type", "Accept"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    )

    app.extensions["dynamodb"] = get_dynamodb_tables(app)

    # Ensure log directory exists
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.donors import donors_bp
    from app.routes.requests import requests_bp
    from app.routes.matching import matching_bp
    from app.routes.health import health_bp
    from app.routes.admin_auth import admin_auth_bp
    from app.routes.admin import admin_bp
    from app.routes.pages import pages_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(donors_bp, url_prefix="/api/donors")
    app.register_blueprint(requests_bp, url_prefix="/api/requests")
    app.register_blueprint(matching_bp, url_prefix="/api/matching")
    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(admin_auth_bp, url_prefix="/api/admin")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(pages_bp)

    return app
