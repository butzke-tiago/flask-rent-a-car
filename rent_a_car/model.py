# flask-related
from flask import current_app as app, abort, flash, redirect, render_template, url_for
from flask.views import MethodView
from flask_login import current_user, login_required
from flask_smorest import Blueprint

# project-related
from .factory import EndpointMixinFactory
from .schemas import ModelSchema, ModelSchemaNested, TagSchema, TagInputSchema
from .services import (
    category_service,
    make_service,
    model_service,
    tag_service,
    vehicle_service,
    DuplicateModelError,
)
from .user import login_as_admin_required
from .utils.nav import *


# misc
from marshmallow import Schema, INCLUDE
from urllib.parse import unquote


def NAV_CREATE_MODEL():
    return (url_for(str(Model())), "Create Model")


blp = Blueprint("model", __name__, url_prefix="/model")


EndpointMixin = EndpointMixinFactory.create_endpoint(blp)


@blp.route("/")
class Model(MethodView, EndpointMixin):
    @login_required
    @login_as_admin_required
    def get(self):
        nav = get_nav_by_user(current_user)
        return render_template(
            "generic/create.html",
            title=f"New {type(self).__name__}",
            submit="Create",
            nav=nav,
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
        nav = get_nav_by_user(current_user)
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
                    nav=nav,
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
                    nav=nav,
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
        nav = get_nav_by_user(current_user)
        if current_user.is_authenticated and current_user.is_admin():
            nav = [NAV_CREATE_MODEL()] + nav
        nav.remove(NAV_MODELS())
        return render_template(
            "generic/all.html",
            title=f"{type(self).__name__}",
            nav=nav,
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
            is_owner = current_user.is_authenticated and current_user.is_admin()
            update = is_owner and "edit" in kwargs
            nav = get_nav_by_user(current_user)
            info = ModelSchemaNested().dump(model)
            info["category_tags"] = model.category.tags
            if current_user.is_authenticated and current_user.is_admin():
                vehicles = vehicle_service.get_all()
            elif current_user.is_authenticated and current_user.is_franchisee():
                vehicles = vehicle_service.get_owned_by(current_user.id)
            else:
                vehicles = []
            tables = (
                [
                    {
                        "name": "vehicles",
                        "headers": ["picture", "plate", "year", "store"],
                        "rows": [
                            {
                                "plate": vehicle.plate,
                                "year": vehicle.year,
                                "store": vehicle.store.name,
                                "picture": vehicle.model.picture or "",
                            }
                            for vehicle in vehicles
                        ],
                        "refs": [
                            {
                                "plate": url_for(
                                    str("vehicle.VehicleId"), vehicle_id=vehicle.id
                                ),
                                "store": url_for(
                                    str("store.StoreId"),
                                    store_id=vehicle.store.id,
                                ),
                            }
                            for vehicle in vehicles
                        ],
                        "pics": ["picture"],
                    },
                ]
                if vehicles
                else []
            )
            return render_template(
                "generic/view.html",
                title=model.name,
                submit="Update",
                nav=nav,
                schema=ModelSchema if update else ModelSchemaNested,
                info=info,
                info_lists_url={
                    "tags": {"url_prefix": "/tag/", "has_button": is_owner},
                    "category_tags": {"url_prefix": "/tag/"},
                },
                is_owner=is_owner,
                update=update,
                map=get_map(),
                tables=tables,
            )
        else:
            message = f"{self.blp.name.capitalize()} #{model_id} not found!"
            app.logger.error(message)
            flash(message, "error")
            return render_template("base.html"), 404

    @login_required
    @login_as_admin_required
    @blp.arguments(ModelSchema, location="form")
    def post(self, model_info, model_id):
        app.logger.info(f"Updating {self.blp.name} #{model_id}.")
        app.logger.debug(f"{self.blp.name.capitalize()} data: {model_info}.")
        try:
            model = model_service.update(model_id, **model_info)
        except DuplicateModelError as e:
            model = model_service.get(model_id)
            flash(f"{e}", "error")
            nav = get_nav_by_user(current_user)
            return render_template(
                "generic/view.html",
                title=model.name,
                submit="Update",
                nav=nav,
                schema=ModelSchema,
                info=model_info,
                is_owner=True,
                update=True,
            )
        if not model:
            abort(404)
        return redirect(url_for(str(ModelId()), model_id=model_id))

    @login_required
    @login_as_admin_required
    def delete(self, model_id):
        app.logger.info(f"Deleting {self.blp.name} #{model_id}.")
        model = model_service.delete(model_id)
        if not model:
            app.logger.error(f"{self.blp.name.capitalize()} not found!")
            abort(404)
        return redirect(url_for(str(Models()))), 303


@blp.route("/<model_id>/tags/")
class ModelTags(MethodView, EndpointMixin):
    @login_required
    @login_as_admin_required
    def get(self, model_id):
        app.logger.info(f"Editing tags for {blp.name} #{model_id}.")
        model = model_service.get(model_id)
        if not model:
            app.logger.error(f"{blp.name.capitalize()} not found!")
            abort(404)
        tags = tag_service.get_all()
        nav = get_nav_by_user(current_user)
        return render_template(
            "generic/tags.html",
            title=f"{model.name}'s tags",
            submit="Update",
            nav=nav,
            schema=TagSchema,
            info=model.tags,
            tags=tags,
            is_owner=True,
            update=True,
            map=map_tags(model),
            done=url_for(str(ModelId()), model_id=model_id),
        )

    @login_required
    @login_as_admin_required
    @blp.arguments(TagInputSchema, unknown=INCLUDE, location="form", as_kwargs=True)
    def post(self, model_id, **kwargs):
        app.logger.info(f"Updating tags for {blp.name} #{model_id}.")
        model = model_service.get(model_id)
        if not model:
            abort(404)
        app.logger.debug(f"Current tags are {[str(tag) for tag in model.tags]}.")
        if "available" in kwargs:
            tag_ids = kwargs["available"]
            app.logger.info(f"Adding tags #{tag_ids}.")
            tags = tag_service.get_many(tag_ids)
            if len(tags) != len(tag_ids):
                app.logger.error(
                    f"Some tags do not exist: {list(set(tag_ids).difference(set([tag.id for tag in tags])))}."
                )
                abort(400)
            app.logger.debug(f"Added tags are {[tag.name for tag in tags]}.")
            try:
                model_service.add_tags(model_id, tags)
            except ValueError as e:
                abort(400, e)
            except Exception as e:
                abort(500, e)
        if "assigned" in kwargs:
            tag_ids = kwargs["assigned"]
            app.logger.info(f"Removing tags #{tag_ids}.")
            tags = tag_service.get_many(tag_ids)
            if len(tags) != len(tag_ids):
                app.logger.error(
                    f"Some tags do not exist: {list(set(tag_ids).difference(set([tag.id for tag in tags])))}."
                )
                abort(400)
            app.logger.debug(f"Removed tags are {[tag.name for tag in tags]}.")
            try:
                model_service.remove_tags(model_id, tags)
            except ValueError as e:
                abort(400, e)
            except Exception as e:
                abort(500, e)
        nav = get_nav_by_user(current_user)
        return render_template(
            "generic/tags.html",
            title=f"{model.name}'s tags",
            submit="Update",
            nav=nav,
            schema=TagSchema,
            info=model.tags,
            is_owner=True,
            update=True,
            map=map_tags(model),
            done=url_for(str(ModelId()), model_id=model_id),
        )


def map_tags(model):
    all_tags = tag_service.get_all()
    [all_tags.remove(tag) for tag in model.tags + model.category.tags]
    return {
        "tags": {
            "category": {
                "name": "tags",
                "url": unquote(url_for("tag.TagId", tag_id={})),
                "options": (
                    {
                        "value": tag.id,
                        "name": tag.name,
                    }
                    for tag in sorted(model.category.tags, key=lambda x: x.name)
                ),
            },
            "assigned": {
                "name": "tags",
                "url": unquote(url_for("tag.TagId", tag_id={})),
                "options": (
                    {
                        "value": tag.id,
                        "name": tag.name,
                    }
                    for tag in sorted(model.tags, key=lambda x: x.name)
                ),
                "submit": {"text": ">>", "position": "right"},
            },
            "available": {
                "name": "tags",
                "url": unquote(url_for("tag.TagId", tag_id={})),
                "options": (
                    {
                        "value": tag.id,
                        "name": tag.name,
                    }
                    for tag in sorted(all_tags, key=lambda x: x.name)
                ),
                "submit": {"text": "<<", "position": "left"},
            },
        },
        "width": max(
            [len(t.name) for t in all_tags + model.tags + model.category.tags]
        ),
    }


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
