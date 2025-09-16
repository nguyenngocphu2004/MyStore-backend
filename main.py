from flask import Flask, jsonify
from flask_cors import CORS
from backend.app import create_app,socketio

app = create_app()
CORS(app,supports_credentials=True)


if __name__ == "__main__":
    socketio.run(app, debug=True)