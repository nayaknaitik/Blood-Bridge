"""
Blood Bridge - Entry point for development server.
Run: python app.py
Production: gunicorn wsgi:app
"""
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
