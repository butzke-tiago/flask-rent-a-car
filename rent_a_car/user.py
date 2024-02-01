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
from .factory import EndpointMixinFactory
from .schemas import UserSchema, UserLoginSchema
from .services import (
    category_service,
    model_service,
    store_service,
    user_service,
    DuplicateUserError,
    tag_service,
    vehicle_service,
)
from .utils.nav import *

# misc
from functools import wraps
from marshmallow import Schema, INCLUDE

blp = Blueprint("user", __name__, url_prefix="/user")

EndpointMixin = EndpointMixinFactory.create_endpoint(blp)


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


def login_as_operator_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if current_user.is_franchisee() or current_user.is_admin():
            return func(*args, **kwargs)
        else:
            abort(403)

    return decorated_view


@blp.route("/")
class Profile(MethodView):
    @login_required
    def get(self):
        nav = get_nav_by_user(current_user)
        return render_template(
            "user/profile.html",
            title=current_user.name,
            nav=nav,
            tables=get_profile_tables_by_user(current_user),
            ncols=2,
        )


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


@blp.route("/all")
class Users(MethodView):
    @login_required
    @login_as_admin_required
    def get(self):
        users = user_service.get_all()
        nav = get_nav_by_user(current_user)
        nav.remove(NAV_USERS())
        return render_template(
            "generic/all.html",
            title=f"{type(self).__name__}",
            nav=nav,
            table={
                "name": "users",
                "headers": ["name", "e-mail", "role", "stores"],
                "rows": [
                    {
                        "name": user.name,
                        "e-mail": user.email,
                        "role": user.role.name,
                        "stores": len(list(user.stores)),
                    }
                    for user in users
                ],
                "refs": [
                    {"name": url_for(str(UserId()), user_id=user.id)} for user in users
                ],
            },
        )


@blp.route("/<user_id>")
class UserId(MethodView, EndpointMixin):
    @login_required
    @login_as_admin_required
    def get(self, user_id, **kwargs):
        app.logger.info(f"Fetching {self.blp.name} #{user_id}.")
        user = user_service.get(user_id)
        if user:
            is_owner = False
            update = False
            nav = get_nav_by_user(current_user)
            if user.is_franchisee():
                tables = [
                    {
                        "name": "stores",
                        "headers": ["name", "address"],
                        "rows": [
                            {
                                "name": store.name,
                                "address": store.address,
                            }
                            for store in user.stores
                        ],
                        "refs": [
                            {
                                "name": url_for(
                                    str("store.StoreId"), store_id=store.id
                                ),
                            }
                            for store in user.stores
                        ],
                        "pics": ["picture"],
                    },
                ]

            else:
                tables = []
            return render_template(
                "generic/view.html",
                title=user.name,
                submit="Update",
                nav=nav,
                schema=UserSchema,
                info=UserSchema().dump(user),
                is_owner=is_owner,
                update=update,
                tables=tables,
            )
        else:
            message = f"{self.blp.name.capitalize()} #{user_id} not found!"
            app.logger.error(message)
            flash(message, "error")
            return render_template("base.html"), 404


def add_login(app: Flask):
    login_manager = LoginManager(app=app)
    login_manager.login_view = "user.Login"
    login_manager.login_message_category = "warning"
    login_manager.refresh_view = "user.Login"

    @login_manager.user_loader
    def load_user(user_id):
        # since the user_id is just the primary key of our user table, use it in the query for the user
        return user_service.get(user_id)


def get_profile_tables_by_user(user):
    if user.is_admin():
        users = user_service.get_all()
        stores = store_service.get_all()
        categories = category_service.get_all()
        models = model_service.get_all()
        tags = tag_service.get_all()
        vehicles = vehicle_service.get_all()

    if user.is_franchisee():
        stores = store_service.get_owned_by(user.id)
        vehicles = vehicle_service.get_owned_by(user.id)

    if user.is_client():
        stores = store_service.get_all()
        categories = category_service.get_all()

    tables = [
        {
            "name": "users",
            "headers": ["name", "e-mail", "role", "stores"],
            "rows": [
                {
                    "name": user.name,
                    "e-mail": user.email,
                    "role": user.role.name,
                    "stores": len(list(user.stores)),
                }
                for user in users
            ],
            "refs": [
                {"name": url_for(str(UserId()), user_id=user.id)} for user in users
            ],
        }
        if user.is_admin()
        else None,
        {
            "name": "stores",
            "headers": ["name", "address", "vehicles"],
            "rows": [
                {
                    "name": store.name,
                    "address": store.address or "",
                    "vehicles": len(list(store.vehicles)),
                }
                for store in stores
            ],
            "refs": [
                {"name": url_for("store.StoreId", store_id=store.id)}
                for store in stores
            ],
        },
        {
            "name": "categories",
            "headers": ["name", "fare", "models"],
            "rows": [
                {
                    "name": category.name,
                    "fare": category.fare,
                    "models": len(list(category.models)),
                }
                for category in categories
            ],
            "refs": [
                {"name": url_for("category.CategoryId", category_id=category.id)}
                for category in categories
            ],
        }
        if user.is_admin() or user.is_client()
        else None,
        {
            "name": "models",
            "headers": ["picture", "name", "make", "category"],
            "rows": [
                {
                    "picture": model.picture or "",
                    "name": model.name,
                    "make": model.make.name,
                    "category": model.category.name,
                }
                for model in models
            ],
            "refs": [
                {
                    "name": url_for("model.ModelId", model_id=model.id),
                    "make": url_for("make.MakeId", make_id=model.make_id),
                    "category": url_for(
                        "category.CategoryId", category_id=model.category_id
                    ),
                }
                for model in models
            ],
            "pics": ["picture"],
        }
        if user.is_admin()
        else None,
        {
            "name": "models",
            "headers": ["picture", "name", "make", "category"],
            "rows": [
                {
                    "picture": model.picture or "",
                    "name": model.name,
                    "make": model.make.name,
                    "category": model.category.name,
                }
                for model in models
            ],
            "refs": [
                {
                    "name": url_for("model.ModelId", model_id=model.id),
                    "make": url_for("make.MakeId", make_id=model.make_id),
                    "category": url_for(
                        "category.CategoryId", category_id=model.category_id
                    ),
                }
                for model in models
            ],
            "pics": ["picture"],
        }
        if user.is_admin()
        else None,
        {
            "name": "tags",
            "headers": ["name"],
            "rows": [
                {
                    "name": tag.name,
                }
                for tag in tags
            ],
            "refs": [{"name": url_for("tag.TagId", tag_id=tag.id)} for tag in tags],
        }
        if user.is_admin()
        else None,
        {
            "name": "vehicles",
            "headers": ["picture", "name", "model", "year", "store"],
            "rows": [
                {
                    "picture": vehicle.model.picture or "",
                    "name": vehicle.plate,
                    "model": vehicle.model.name,
                    "year": vehicle.year,
                    "store": vehicle.store.name,
                }
                for vehicle in vehicles
            ],
            "refs": [
                {
                    "name": url_for("vehicle.VehicleId", vehicle_id=vehicle.id),
                    "model": url_for("model.ModelId", model_id=vehicle.model_id),
                    "store": url_for("store.StoreId", store_id=vehicle.store_id),
                }
                for vehicle in vehicles
            ],
            "pics": ["picture"],
        }
        if user.is_admin() or user.is_franchisee()
        else None,
    ]
    tables = list(filter(None, tables))
    return tables
