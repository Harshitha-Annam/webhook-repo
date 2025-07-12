# initialize a flask app
from .routes import webhook
from flask import Flask
from dotenv import load_dotenv
from flask_cors import CORS
import os

from .extensions import mongo



def create_app():
    load_dotenv()
    app = Flask(__name__)

    CORS(app)
    # get the mongodb URI (not using any fallback)
    app.config['MONGO_URI'] = os.getenv("MONGO_URI")

    mongo.init_app(app)
    app.register_blueprint(webhook)

    return app

