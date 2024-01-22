# flask-related
from flask import redirect, render_template, url_for
from flask.views import MethodView
from flask_login import current_user
from flask_smorest import Blueprint

blp = Blueprint("home", __name__)


@blp.route("/")
class Home(MethodView):
    def get(self):
        if current_user.is_authenticated:
            return redirect(url_for("user.Profile"))
        return render_template("home.html", title="Rent a Car")
