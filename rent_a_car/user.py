# flask-related
from flask import (
    Flask,
    current_app as app,
    abort,
    flash,
    redirect,
    render_template,
    url_for,
)
from flask.views import MethodView
from flask_login import (
    LoginManager,
    current_user,
    login_user,
    logout_user,
    login_required,
)
from flask_smorest import Blueprint

# project-related
from .schemas import UserSchema, UserLoginSchema
from .services import user_service, DuplicateUserError
from .utils.nav import *

# misc
from functools import wraps
from marshmallow import Schema, INCLUDE

blp = Blueprint("user", __name__, url_prefix="/user")


def anonymous_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if current_user.is_anonymous:
            return func(*args, **kwargs)
        else:
            abort(403)

    return decorated_view


def login_as_franchisee_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if current_user.is_franchisee():
            return func(*args, **kwargs)
        else:
            abort(403)

    return decorated_view


def login_as_admin_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if current_user.is_admin():
            return func(*args, **kwargs)
        else:
            abort(403)

    return decorated_view


@blp.route("/")
class Profile(MethodView):
    @login_required
    def get(self):
        nav = get_nav_by_role(current_user.role)
        return render_template("user/profile.html", title=current_user.name, nav=nav)


class User(MethodView):
    def get(self):
        if current_user.is_authenticated:
            return redirect(url_for("user.Profile"))
        return render_template("user/auth.html", title=self.title, submit="Register")

    @anonymous_required
    @blp.arguments(UserSchema, location="form")
    def post(self, user_input):
        app.logger.info(f"Registering {type(self).__name__}.")
        app.logger.debug(f"{type(self).__name__} info: {user_input}")
        try:
            user = self.register(**user_input)
        except DuplicateUserError as e:
            app.logger.error(e)
            flash(f"{e}", "error")
            return (
                render_template(
                    "user/auth.html",
                    title=self.title,
                    submit="Register",
                    **user_input,
                ),
                409,
            )
        except Exception as e:
            app.logger.error(e)
            flash(
                f"An unexpected error {type(e).__name__!r} happened! Details: {e.__cause__}",
                "error",
            )
            return (
                render_template(
                    "user/auth.html",
                    title=self.title,
                    submit="Register",
                    **user_input,
                ),
                500,
            )
        else:
            app.logger.info(
                f"Successfully registered {type(self).__name__} with id #{user.id}."
            )
            flash(f"Welcome, {user.name}!")
            login_user(user)
            return redirect(url_for("user.Profile"))


@blp.route("/client")
class Client(User):
    title = "Register to start using"
    register = user_service.register_client


@blp.route("/franchisee")
class Franchisee(User):
    title = "Become a franchisee"
    register = user_service.register_franchisee


@blp.route("/login")
class Login(MethodView):
    def get(self):
        return render_template("user/auth.html", title="Login", submit="Login")

    @blp.arguments(UserLoginSchema, location="form")
    @blp.arguments(Schema, location="query", as_kwargs=True, unknown=INCLUDE)
    def post(self, user_input, **kwargs):
        app.logger.debug(
            f"Login attempt with email: {user_input['email']!r} and password: {user_input['password']!r}."
        )
        user, logged_in = user_service.login(
            email=user_input["email"], password=user_input["password"]
        )
        if not logged_in:
            flash("Invalid e-mail or password!", "error")
            return (
                render_template(
                    "user/auth.html",
                    title="Login",
                    submit="Login",
                    **user_input,
                ),
                401,
            )
        flash(f"Welcome, {user.name}!")
        login_user(
            user,
            remember="remember" in user_input,
        )
        app.logger.info(f"User {current_user.email!r} logged in.")
        app.logger.debug(f"Args {kwargs}")
        if "next" in kwargs:
            return redirect(kwargs["next"])
        return redirect(url_for("user.Profile"))


@blp.route("/logout")
class Logout(MethodView):
    @login_required
    def get(self):
        app.logger.info(f"User {current_user.email!r} logged out.")
        logout_user()
        flash("Logged out!")
        return redirect(url_for("home.Home"))


def add_login(app: Flask):
    login_manager = LoginManager(app=app)
    login_manager.login_view = "user.Login"
    login_manager.login_message_category = "warning"
    login_manager.refresh_view = "user.Login"

    @login_manager.user_loader
    def load_user(user_id):
        # since the user_id is just the primary key of our user table, use it in the query for the user
        return user_service.get(user_id)
