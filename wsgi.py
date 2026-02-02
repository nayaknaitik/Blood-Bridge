"""
WSGI entry point for production (e.g. gunicorn).
Usage: gunicorn wsgi:app
"""
from app import create_app

app = create_app()
