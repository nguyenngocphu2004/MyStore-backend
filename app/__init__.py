from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask.json.provider import DefaultJSONProvider
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from datetime import timedelta
import cloudinary.api,os
from flask_mail import Mail
from flask_socketio import SocketIO
from dotenv import load_dotenv

class CustomJSONProvider(DefaultJSONProvider):
    def dumps(self, obj, **kwargs):
        kwargs.setdefault("ensure_ascii", False)  # luôn tắt ascii
        return super().dumps(obj, **kwargs)

    def loads(self, s, **kwargs):
        return super().loads(s, **kwargs)

cloudinary.config(
  cloud_name="dbnra16ca",      # Tên cloud trong Cloudinary
  api_key=os.getenv("API_KEY"),
  api_secret=os.getenv("API_SECRET"),
  secure=True
)


db = SQLAlchemy()
mail = Mail()
socketio = SocketIO(cors_allowed_origins="*")

def create_app():
    app = Flask(__name__)
    app.json = CustomJSONProvider(app)
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=2)
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)
    app.secret_key = os.getenv("SECRET_KEY")
    app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:123456@localhost/phustore?charset=utf8mb4"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True

    app.config["MAIL_SERVER"] = "smtp.gmail.com"
    app.config["MAIL_PORT"] = 587
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USERNAME"] = "nguyenphu1999f@gmail.com"
    app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
    app.config["MAIL_DEFAULT_SENDER"] = ("PhuStore", "your_email@gmail.com")
    db.init_app(app)
    mail.init_app(app)
    CORS(app, supports_credentials=True)
    JWTManager(app)
    socketio.init_app(app)

    from .routes import main
    app.register_blueprint(main)
    from . import socket_events
    return app