import os


class Config:
    """
    Base configuration class for the Flask Application.
    Handles database paths, security keys, and file storage settings.
    """
    
    # ------------------------------
    # SECURITY
    # ------------------------------
    # Fetch secret key from environment variables, default to 'devkey' for local testing
    SECRET_KEY = os.getenv("SECRET_KEY", "devkey")
    
    # Enable Debug mode (set to False in production)
    DEBUG = os.getenv("DEBUG", True)

    # ------------------------------
    # PATH CONFIGURATION
    # ------------------------------
    # Determine the absolute path to the project root directory
    # __file__ is .../project/app/config.py
    # dirname(__file__) is .../project/app
    # dirname(dirname(__file__)) is .../project (Root)
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

    # Define the instance folder location (stores runtime data like the DB)
    INSTANCE_DIR = os.path.join(BASE_DIR, "instance")

    # Ensure the instance folder exists automatically
    os.makedirs(INSTANCE_DIR, exist_ok=True)

    # ------------------------------
    # DATABASE CONFIGURATION
    # ------------------------------
    # Use SQLite for development. Absolute path ensures DB is created in the instance folder.
    # Change 'app.db' to 'jansaathi.db' if you prefer a specific name.
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(INSTANCE_DIR, "app.db")

    # Disable Flask-SQLAlchemy event system to save resources (not needed for this project)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ------------------------------
    # FILE UPLOAD CONFIGURATION
    # ------------------------------
    # Folder where user documents (Aadhar, PAN, etc.) will be stored
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # Max file size: 16MB (Prevents server crashes from huge uploads)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    # Allowed file extensions for security
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
