# flask-related
from flask import current_app as app, render_template, redirect, flash, url_for
from flask.views import MethodView
from flask_smorest import Blueprint

# project-related
from .schemas import UserSchema
from .services import user_service, DuplicateUserError

blp = Blueprint(
    "user",
    __name__,
)


@blp.route("/user/")
class Profile(MethodView):
    def get(self):
        return render_template("user/profile.html", title="User")


class User(MethodView):
    def get(self):
        return render_template("user/auth.html", title=self.title, submit="Register")

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
            return redirect(url_for("user.Profile"))


@blp.route("/user/client")
class Client(User):
    title = "Register to start using"
    register = user_service.register_client


@blp.route("/user/franchisee")
class Franchisee(User):
    title = "Become a franchisee"
    register = user_service.register_franchisee


@blp.route("/user/login")
class Login(MethodView):
    def get(self):
        return render_template("user/auth.html", title="Login", submit="Login")


@blp.route("/user/logout")
class Logout(MethodView):
    def get(self):
        return render_template("home.html", title="Logout")
