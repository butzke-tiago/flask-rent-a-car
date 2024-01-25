# flask-related
from flask import current_app as app, abort, flash, redirect, render_template, url_for
from flask.views import MethodView
from flask_login import login_required
from flask_smorest import Blueprint

# project-related
from .schemas import ModelSchema, ModelSchemaNested

from .factory import EndpointMixinFactory
from .services import category_service, make_service, model_service, DuplicateModelError
from .user import login_as_admin_required


# misc
from marshmallow import Schema, INCLUDE
from urllib.parse import unquote


def NAV_MODELS():
    return (url_for(str(Models())), "Models")


def NAV_CATEGORIES():
    return (url_for("category.Categories"), "Categories")


def NAV_MAKES():
    return (url_for("make.Makes"), "Makes")


def NAV_CREATE_MODEL():
    return (url_for(str(Model())), "Create Model")


blp = Blueprint("model", __name__, url_prefix="/model")


EndpointMixin = EndpointMixinFactory.create_endpoint(blp)


@blp.before_request
def before_request():
    app.jinja_env.globals.update(type=type, zip=zip)


@blp.route("/")
class Model(MethodView, EndpointMixin):
    @login_required
    @login_as_admin_required
    def get(self):
        return render_template(
            "generic/create.html",
            title=f"New {type(self).__name__}",
            submit="Create",
            nav=[NAV_MODELS(), NAV_CATEGORIES(), NAV_MAKES()],
            schema=ModelSchema,
            info={},
            map=get_map(),
        )

    @login_required
    @login_as_admin_required
    @blp.arguments(ModelSchema, location="form")
    def post(self, model):
        app.logger.info(f"Creating {self.blp.name}.")
        app.logger.debug(f"{self.blp.name.capitalize()} info: {model}.")
        try:
            model = model_service.create(**model)
        except DuplicateModelError as e:
            app.logger.error(e)
            flash(f"{e}", "error")
            return (
                render_template(
                    "generic/create.html",
                    title=f"New {type(self).__name__}",
                    submit="Create",
                    nav=[NAV_MODELS(), NAV_CATEGORIES(), NAV_MAKES()],
                    schema=ModelSchema,
                    info=model,
                    map=get_map(),
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
                    nav=[NAV_MODELS(), NAV_CATEGORIES(), NAV_MAKES()],
                    schema=ModelSchema,
                    info=model,
                    map=get_map(),
                ),
                500,
            )
        else:
            app.logger.info(
                f"Successfully created {self.blp.name} with id #{model.id}."
            )
            flash(f"{self.blp.name.capitalize()} {model.name!r} created!")
            return redirect(url_for(str(Models())))


@blp.route("/all")
class Models(MethodView, EndpointMixin):
    def get(self):
        models = model_service.get_all()
        return render_template(
            "generic/all.html",
            title=f"{type(self).__name__}",
            nav=[NAV_CREATE_MODEL(), NAV_CATEGORIES(), NAV_MAKES()],
            table={
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
                        "name": url_for(str(ModelId()), model_id=model.id),
                        "make": url_for("make.MakeId", make_id=model.make_id),
                        "category": url_for(
                            "category.CategoryId", category_id=model.category_id
                        ),
                    }
                    for model in models
                ],
                "pics": ["picture"],
            },
        )


@blp.route("/<model_id>")
class ModelId(MethodView, EndpointMixin):
    @blp.arguments(Schema, location="query", as_kwargs=True, unknown=INCLUDE)
    def get(self, model_id, **kwargs):
        app.logger.info(f"Fetching {self.blp.name} #{model_id}.")
        model = model_service.get(model_id)
        if model:
            return render_template(
                "generic/view.html",
                title=model.name,
                submit="Update",
                nav=[NAV_MODELS(), NAV_CATEGORIES(), NAV_MAKES()],
                schema=ModelSchema,
                info=ModelSchemaNested().dump(model),
                is_owner=True,
                update="edit" in kwargs,
                map=get_map(),
            )
        else:
            message = f"{self.blp.name.capitalize()} #{model_id} not found!"
            app.logger.error(message)
            flash(message, "error")
            return render_template("base.html"), 404

    @blp.arguments(ModelSchema, location="form")
    def post(self, model_info, model_id):
        app.logger.info(f"Updating {self.blp.name} #{model_id}.")
        app.logger.debug(f"{self.blp.name.capitalize()} data: {model_info}.")
        try:
            model = model_service.update(model_id, **model_info)
        except DuplicateModelError as e:
            model = model_service.get(model_id)
            flash(f"{e}", "error")
            return render_template(
                "generic/view.html",
                title=model.name,
                submit="Update",
                nav=[NAV_MODELS(), NAV_CATEGORIES(), NAV_MAKES()],
                schema=ModelSchema,
                info=model_info,
                is_owner=True,
                update=True,
            )
        if not model:
            abort(404)
        return redirect(url_for(str(ModelId()), model_id=model_id))

    @login_as_admin_required
    def delete(self, model_id):
        app.logger.info(f"Deleting {self.blp.name} #{model_id}.")
        model = model_service.delete(model_id)
        if not model:
            app.logger.error(f"{self.blp.name.capitalize()} not found!")
            abort(404)
        return redirect(url_for(str(Models()))), 303


def get_map():
    return {
        "make_id": {
            "name": "make",
            "url": unquote(url_for("make.MakeId", make_id={})),
            "options": (
                {
                    "value": make.id,
                    "name": make.name,
                }
                for make in make_service.get_all()
            ),
        },
        "category_id": {
            "name": "category",
            "url": unquote(url_for("category.CategoryId", category_id={})),
            "options": (
                {"value": category.id, "name": category.name}
                for category in category_service.get_all()
            ),
        },
    }
