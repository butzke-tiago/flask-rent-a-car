# flask-related
from flask import current_app as app, abort, flash, redirect, render_template, url_for
from flask.views import MethodView
from flask_login import login_required
from flask_smorest import Blueprint

# project-related
from .schemas import MakeSchema

from .factory import EndpointMixinFactory
from .services import make_service, DuplicateMakeError
from .user import login_as_admin_required


def NAV_CATEGORIES():
    return (url_for("category.Categories"), "Categories")


def NAV_MODELS():
    return (url_for("model.Models"), "Models")


# misc
from marshmallow import Schema, INCLUDE


def NAV_MAKES():
    return (url_for(str(Makes())), "Makes")


def NAV_CREATE_MAKE():
    return (url_for(str(Make())), "Create Make")


blp = Blueprint("make", __name__, url_prefix="/make")


EndpointMixin = EndpointMixinFactory.create_endpoint(blp)


@blp.before_request
def before_request():
    app.jinja_env.globals.update(type=type, zip=zip, float=float)


@blp.route("/")
class Make(MethodView, EndpointMixin):
    @login_required
    @login_as_admin_required
    def get(self):
        return render_template(
            "generic/create.html",
            title=f"New {type(self).__name__}",
            submit="Create",
            nav=[NAV_MAKES(), NAV_CATEGORIES(), NAV_MODELS()],
            schema=MakeSchema,
            info={},
        )

    @login_required
    @login_as_admin_required
    @blp.arguments(MakeSchema, location="form")
    def post(self, make):
        app.logger.info(f"Creating {self.blp.name}.")
        app.logger.debug(f"{self.blp.name.capitalize()} info: {make}.")
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
                    nav=[NAV_MAKES(), NAV_CATEGORIES(), NAV_MODELS()],
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
                    nav=[NAV_MAKES(), NAV_CATEGORIES(), NAV_MODELS()],
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
        return render_template(
            "generic/all.html",
            title=f"{type(self).__name__}",
            nav=[NAV_CREATE_MAKE(), NAV_CATEGORIES(), NAV_MODELS()],
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
            return render_template(
                "generic/view.html",
                title=make.name,
                submit="Update",
                nav=[NAV_MAKES(), NAV_CATEGORIES(), NAV_MODELS()],
                schema=MakeSchema,
                info=MakeSchema().dump(make),
                is_owner=True,
                update="edit" in kwargs,
            )
        else:
            message = f"{self.blp.name.capitalize()} #{make_id} not found!"
            app.logger.error(message)
            flash(message, "error")
            return render_template("base.html"), 404

    @blp.arguments(MakeSchema, location="form")
    def post(self, make_info, make_id):
        app.logger.info(f"Updating {self.blp.name} #{make_id}.")
        app.logger.debug(f"{self.blp.name.capitalize()} data: {make_info}.")
        try:
            make = make_service.update(make_id, **make_info)
        except DuplicateMakeError as e:
            make = make_service.get(make_id)
            flash(f"{e}", "error")
            return render_template(
                "generic/view.html",
                title=make.name,
                submit="Update",
                nav=[NAV_MAKES(), NAV_CATEGORIES(), NAV_MODELS()],
                schema=MakeSchema,
                info=make_info,
                is_owner=True,
                update=True,
            )
        if not make:
            abort(404)
        return redirect(url_for(str(MakeId()), make_id=make_id))

    @login_as_admin_required
    def delete(self, make_id):
        app.logger.info(f"Deleting {self.blp.name} #{make_id}.")
        make = make_service.delete(make_id)
        if not make:
            app.logger.error(f"{self.blp.name.capitalize()} not found!")
            abort(404)
        return redirect(url_for(str(Makes()))), 303
