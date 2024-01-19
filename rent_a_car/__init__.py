from flask import Flask, render_template


def create_app():
    app = Flask(__name__)

    @app.get("/")
    def index():
        return render_template("home.html", title="Rent a Car")

    return app
