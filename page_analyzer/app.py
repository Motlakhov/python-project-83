from flask import Flask, render_template
from dotenv import load_dotenv
import os

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

    @app.route("/")
    def index():
        return render_template('index.html')

    return app

app = create_app()
