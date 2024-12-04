from flask import Flask
from dotenv import load_dotenv
import os

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

    @app.route("/")
    def hello_world():
        return "<p>Hello, World!</p>"

    return app

app = create_app()
