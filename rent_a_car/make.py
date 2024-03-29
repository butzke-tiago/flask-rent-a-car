# flask-related
from flask import current_app as app, abort, flash, redirect, render_template, url_for
from flask.views import MethodView
from flask_login import current_user, login_required
from flask_smorest import Blueprint

# project-related
from .factory import EndpointMixinFactory
from .schemas import MakeSchema
from .services import make_service, DuplicateMakeError
from .user import login_as_admin_required
from .utils.nav import *


# misc
from marshmallow import Schema, INCLUDE


def NAV_CREATE_MAKE():
    return (url_for(str(Make())), "Create Make")


blp = Blueprint("make", __name__, url_prefix="/make")


EndpointMixin = EndpointMixinFactory.create_endpoint(blp)


@blp.route("/")
class Make(MethodView, EndpointMixin):
    @login_required
    @login_as_admin_required
    def get(self):
        nav = get_nav_by_user(current_user)
        return render_template(
            "generic/create.html",
            title=f"New {type(self).__name__}",
            submit="Create",
            nav=nav,
            schema=MakeSchema,
            info={},
        )

    @login_required
    @login_as_admin_required
    @blp.arguments(MakeSchema, location="form")
    def post(self, make):
        app.logger.info(f"Creating {self.blp.name}.")
        app.logger.debug(f"{self.blp.name.capitalize()} info: {make}.")
        nav = get_nav_by_user(current_user)
        try:
            make = make_service.create(**make)
        except DuplicateMakeError as e:
            app.logger.error(e)
            flash(f"{e}", "error")
            return (
                render_template(
                    "generic/create.html",
                    title=f"New {type(self).__name__}",
                    submit="Create",
                    nav=nav,
                    schema=MakeSchema,
                    info=make,
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
                    schema=MakeSchema,
                    info=make,
                ),
                500,
            )
        else:
            app.logger.info(f"Successfully created {self.blp.name} with id #{make.id}.")
            flash(f"{self.blp.name.capitalize()} {make.name!r} created!")
            return redirect(url_for(str(Makes())))


@blp.route("/all")
class Makes(MethodView, EndpointMixin):
    def get(self):
        makes = make_service.get_all()
        nav = get_nav_by_user(current_user)
        if current_user.is_authenticated and current_user.is_admin():
            nav = [NAV_CREATE_MAKE()] + nav
        if NAV_MAKES() in nav:
            nav.remove(NAV_MAKES())
        return render_template(
            "generic/all.html",
            title=f"{type(self).__name__}",
            nav=nav,
            table={
                "name": "makes",
                "headers": ["logo", "name", "models"],
                "rows": [
                    {
                        "logo": make.logo or "",
                        "name": make.name,
                        "models": len(list(make.models)),
                    }
                    for make in makes
                ],
                "refs": [
                    {"name": url_for(str(MakeId()), make_id=make.id)} for make in makes
                ],
                "pics": ["logo"],
            },
        )


@blp.route("/<make_id>")
class MakeId(MethodView, EndpointMixin):
    @blp.arguments(Schema, location="query", as_kwargs=True, unknown=INCLUDE)
    def get(self, make_id, **kwargs):
        app.logger.info(f"Fetching {self.blp.name} #{make_id}.")
        make = make_service.get(make_id)
        if make:
            is_owner = current_user.is_authenticated and current_user.is_admin()
            nav = get_nav_by_user(current_user)
            return render_template(
                "generic/view.html",
                title=make.name,
                submit="Update",
                nav=nav,
                schema=MakeSchema,
                info=MakeSchema().dump(make),
                is_owner=is_owner,
                update=is_owner and "edit" in kwargs,
                tables=[
                    {
                        "name": "models",
                        "headers": ["picture", "name", "category"],
                        "rows": [
                            {
                                "name": model.name,
                                "category": model.category.name,
                                "picture": model.picture or "",
                            }
                            for model in make.models
                        ],
                        "refs": [
                            {
                                "name": url_for(
                                    str("model.ModelId"), model_id=model.id
                                ),
                                "category": url_for(
                                    str("category.CategoryId"),
                                    category_id=model.category.id,
                                ),
                            }
                            for model in make.models
                        ],
                        "pics": ["picture"],
                    },
                ],
            )
        else:
            message = f"{self.blp.name.capitalize()} #{make_id} not found!"
            app.logger.error(message)
            flash(message, "error")
            return render_template("base.html"), 404

    @login_required
    @login_as_admin_required
    @blp.arguments(MakeSchema, location="form")
    def post(self, make_info, make_id):
        app.logger.info(f"Updating {self.blp.name} #{make_id}.")
        app.logger.debug(f"{self.blp.name.capitalize()} data: {make_info}.")
        try:
            make = make_service.update(make_id, **make_info)
        except DuplicateMakeError as e:
            make = make_service.get(make_id)
            flash(f"{e}", "error")
            nav = get_nav_by_user(current_user)
            return render_template(
                "generic/view.html",
                title=make.name,
                submit="Update",
                nav=nav,
                schema=MakeSchema,
                info=make_info,
                is_owner=True,
                update=True,
            )
        if not make:
            abort(404)
        return redirect(url_for(str(MakeId()), make_id=make_id))

    @login_required
    @login_as_admin_required
    def delete(self, make_id):
        app.logger.info(f"Deleting {self.blp.name} #{make_id}.")
        make = make_service.delete(make_id)
        if not make:
            app.logger.error(f"{self.blp.name.capitalize()} not found!")
            abort(404)
        return redirect(url_for(str(Makes()))), 303
