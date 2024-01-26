# flask-related
from flask import current_app as app, abort, flash, redirect, render_template, url_for
from flask.views import MethodView
from flask_login import current_user, login_required
from flask_smorest import Blueprint

# project-related
from .schemas import CategorySchema

from .factory import EndpointMixinFactory
from .services import category_service, user_service, DuplicateCategoryError
from .user import login_as_admin_required
from .nav import *


# misc
from marshmallow import Schema, INCLUDE


def NAV_CREATE_CATEGORY():
    return (url_for(str(Category())), "Create Category")


blp = Blueprint("category", __name__, url_prefix="/category")


EndpointMixin = EndpointMixinFactory.create_endpoint(blp)


@blp.before_request
def before_request():
    app.jinja_env.globals.update(type=type, zip=zip, float=float)


@blp.route("/")
class Category(MethodView, EndpointMixin):
    @login_required
    @login_as_admin_required
    def get(self):
        nav = get_nav_by_role(current_user.role)
        return render_template(
            "generic/create.html",
            title=f"New {type(self).__name__}",
            submit="Create",
            nav=nav,
            schema=CategorySchema,
            info={},
        )

    @login_required
    @login_as_admin_required
    @blp.arguments(CategorySchema, location="form")
    def post(self, category):
        app.logger.info(f"Creating {self.blp.name}.")
        app.logger.debug(f"{self.blp.name.capitalize()} info: {category}.")
        nav = get_nav_by_role(current_user.role)
        try:
            category = category_service.create(**category)
        except DuplicateCategoryError as e:
            app.logger.error(e)
            flash(f"{e}", "error")
            return (
                render_template(
                    "generic/create.html",
                    title=f"New {type(self).__name__}",
                    submit="Create",
                    nav=nav,
                    schema=CategorySchema,
                    info=category,
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
                    "generic/create.html",
                    title=f"New {type(self).__name__}",
                    submit="Create",
                    nav=nav,
                    schema=CategorySchema,
                    info=category,
                ),
                500,
            )
        else:
            app.logger.info(
                f"Successfully created {self.blp.name} with id #{category.id}."
            )
            flash(f"{self.blp.name.capitalize()} {category.name!r} created!")
            return redirect(url_for(str(Categories())))


@blp.route("/all")
class Categories(MethodView, EndpointMixin):
    def get(self):
        categories = category_service.get_all()
        nav = get_nav_by_role(current_user.role)
        if user_service.is_admin(current_user):
            nav = [NAV_CREATE_CATEGORY()] + nav
        nav.remove(NAV_CATEGORIES())
        return render_template(
            "generic/all.html",
            title=f"{type(self).__name__}",
            nav=nav,
            table={
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
                    {"name": url_for(str(CategoryId()), category_id=category.id)}
                    for category in categories
                ],
            },
        )


@blp.route("/<category_id>")
class CategoryId(MethodView, EndpointMixin):
    @blp.arguments(Schema, location="query", as_kwargs=True, unknown=INCLUDE)
    def get(self, category_id, **kwargs):
        app.logger.info(f"Fetching {self.blp.name} #{category_id}.")
        category = category_service.get(category_id)
        if category:
            nav = get_nav_by_role(current_user.role)
            return render_template(
                "generic/view.html",
                title=category.name,
                submit="Update",
                nav=nav,
                schema=CategorySchema,
                info=CategorySchema().dump(category),
                is_owner=True,
                update="edit" in kwargs,
                tables=[
                    {
                        "name": "models",
                        "headers": ["picture", "name", "make"],
                        "rows": [
                            {
                                "name": model.name,
                                "make": model.make.name,
                                "picture": model.picture or "",
                            }
                            for model in category.models
                        ],
                        "refs": [
                            {"name": url_for(str("model.ModelId"), model_id=model.id)}
                            for model in category.models
                        ],
                        "pics": ["picture"],
                    },
                ],
            )
        else:
            message = f"{self.blp.name.capitalize()} #{category_id} not found!"
            app.logger.error(message)
            flash(message, "error")
            return render_template("base.html"), 404

    @blp.arguments(CategorySchema, location="form")
    def post(self, category_info, category_id):
        app.logger.info(f"Updating {self.blp.name} #{category_id}.")
        app.logger.debug(f"{self.blp.name.capitalize()} data: {category_info}.")
        try:
            category = category_service.update_category(category_id, **category_info)
        except DuplicateCategoryError as e:
            category = category_service.get(category_id)
            flash(f"{e}", "error")
            nav = [NAV_CREATE_CATEGORY()] + get_nav_by_role(current_user.role)
            return render_template(
                "generic/view.html",
                title=category.name,
                submit="Update",
                nav=nav,
                schema=CategorySchema,
                info=category_info,
                is_owner=True,
                update=True,
            )
        if not category:
            abort(404)
        return redirect(url_for(str(CategoryId()), category_id=category_id))

    @login_as_admin_required
    def delete(self, category_id):
        app.logger.info(f"Deleting {self.blp.name} #{category_id}.")
        category = category_service.delete(category_id)
        if not category:
            app.logger.error(f"{self.blp.name.capitalize()} not found!")
            abort(404)
        return redirect(url_for(str(Categories()))), 303
