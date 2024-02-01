# flask-related
from flask import redirect, render_template, url_for
from flask.views import MethodView
from flask_login import current_user
from flask_smorest import Blueprint

# project-related
from .utils.nav import get_nav_by_user

blp = Blueprint("home", __name__)


@blp.route("/")
class Home(MethodView):
    def get(self):
        if current_user.is_authenticated:
            return redirect(url_for("user.Profile"))
        nav = get_nav_by_user(current_user)
        return render_template("home.html", title="Rent-E-Ria rent a car", nav=nav)
