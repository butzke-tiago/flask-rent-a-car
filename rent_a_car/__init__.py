# flask-related
from flask import Flask, render_template
from flask_migrate import Migrate

# project-related
from .db import db
from .user import blp as UserBlueprint

# misc
from dotenv import load_dotenv
from os import getenv


def create_app():
    app = Flask(__name__)
    load_dotenv()
    DB_FAMILY = getenv("DB_FAMILY") or "sqlite"
    DB_URL = getenv("DB_URL") or "sqlite:///data.db"
    SESSION_KEY = getenv("SESSION_KEY") or "rentacar"

    app.config["SQLALCHEMY_DATABASE_URI"] = DB_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.secret_key = SESSION_KEY

    db.init_app(app)
    migrate = Migrate(app, db, directory=f"migrations-{DB_FAMILY}")

    @app.get("/")
    def index():
        return render_template("home.html", title="Rent a Car")

    app.register_blueprint(UserBlueprint)

    return app
