from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import Config

db = SQLAlchemy()
jwt = JWTManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    CORS(app)

    # Register blueprints
    from app.api.users import bp as users_bp
    from app.api.accounts import bp as accounts_bp
    from app.api.transactions import bp as transactions_bp

    app.register_blueprint(users_bp, url_prefix='/users')
    app.register_blueprint(accounts_bp, url_prefix='/accounts')
    app.register_blueprint(transactions_bp, url_prefix='/transactions')

    return app
