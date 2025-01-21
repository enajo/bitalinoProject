import os
import subprocess
import sys

def install_dependencies():
    """
    Install all dependencies listed in requirements.txt.
    """
    try:
        print("Installing dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        sys.exit(1)

def initialize_database():
    """
    Initialize the database if it does not already exist.
    """
    from app import db, create_app
    app = create_app()
    with app.app_context():
        if not os.path.exists("instance/app.db"):
            print("Initializing database...")
            db.create_all()
            print("Database initialized successfully.")
        else:
            print("Database already initialized. Skipping setup.")

def start_application():
    """
    Start the Flask application.
    """
    try:
        print("Starting the application...")
        subprocess.check_call([sys.executable, "app.py"])
    except subprocess.CalledProcessError as e:
        print(f"Error starting the application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("Starting project setup...")
    install_dependencies()
    initialize_database()
    start_application()
