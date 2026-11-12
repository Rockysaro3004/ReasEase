from pathlib import Path
from flask import Flask
from config import config_by_name
from app.extensions import db, login_manager, csrf

def create_app(config_name='default'):
    """Application factory pattern."""
    flask_app = Flask(__name__)
    flask_app.config.from_object(config_by_name[config_name])

    # Ensure instance and uploads directories exist
    Path(flask_app.instance_path).mkdir(parents=True, exist_ok=True)
    Path(flask_app.config['UPLOAD_FOLDER']).mkdir(parents=True, exist_ok=True)

    # Initialize extensions
    db.init_app(flask_app)
    login_manager.init_app(flask_app)
    csrf.init_app(flask_app)

    # Register blueprints
    from app.auth.routes import auth_bp
    from app.main.routes import main_bp
    from app.documents.routes import documents_bp

    flask_app.register_blueprint(auth_bp)
    flask_app.register_blueprint(main_bp)
    flask_app.register_blueprint(documents_bp)

    # Create database tables automatically
    with flask_app.app_context():
        from . import models
        db.create_all()

    return flask_app