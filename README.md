# Flask SocketIO Chat

A minimal chat application using Flask, Flask-Login and Flask-SocketIO. Includes registration and login (SQLite) and a single chat room. Ready for deployment to Render.

Quickstart (local)

1. Create a virtual environment and install dependencies

   python -m venv venv; .\venv\Scripts\Activate; pip install -r requirements.txt

2. Initialize the database

   flask --app app init-db

3. Run locally

   python app.py

Render deploy notes

- Create a new Web Service on Render using Python environment.
- Set build command: pip install -r requirements.txt
- Set start command: gunicorn -k eventlet -w 1 app:app
- Set environment variable SECRET_KEY to a secure value.

Security notes

- This is a minimal example. For production, add CSRF protection, email verification, rate limiting, and stronger session/security settings.
