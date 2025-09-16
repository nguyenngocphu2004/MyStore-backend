from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask.json.provider import DefaultJSONProvider
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from datetime import timedelta
import cloudinary
import cloudinary.uploader
import cloudinary.api
from flask_mail import Mail
from flask_socketio import SocketIO


class CustomJSONProvider(DefaultJSONProvider):
    def dumps(self, obj, **kwargs):
        kwargs.setdefault("ensure_ascii", False)  # luôn tắt ascii
        return super().dumps(obj, **kwargs)

    def loads(self, s, **kwargs):
        return super().loads(s, **kwargs)

cloudinary.config(
  cloud_name="dbnra16ca",      # Tên cloud trong Cloudinary
  api_key="548673345681374",
  api_secret="8EoiDtQ6DZc77GYZzBzI9j2fqKs",
  secure=True
)


db = SQLAlchemy()
mail = Mail()
socketio = SocketIO(cors_allowed_origins="*")

def create_app():
    app = Flask(__name__)
    app.json = CustomJSONProvider(app)
    app.config["JWT_SECRET_KEY"] = "4f9c2a7f6a8b2c9e9d3a8d7f1c2b3e4f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4"
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=2)
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)
    app.secret_key = "KJGHJG^&*%&*^T&*(IGFG%ERFTGHCFHGF^&**&TYIU"
    app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:123456@localhost/phustore?charset=utf8mb4"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True

    app.config["MAIL_SERVER"] = "smtp.gmail.com"
    app.config["MAIL_PORT"] = 587
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USERNAME"] = "nguyenphu1999f@gmail.com"
    app.config["MAIL_PASSWORD"] = "auie bsfh mvee mzvf"
    app.config["MAIL_DEFAULT_SENDER"] = ("FPT Shop", "your_email@gmail.com")
    db.init_app(app)
    mail.init_app(app)
    CORS(app, supports_credentials=True)
    JWTManager(app)
    socketio.init_app(app)

    from .routes import main
    app.register_blueprint(main)
    from . import socket_events
    return app