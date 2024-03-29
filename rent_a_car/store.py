# flask-related
from flask import current_app as app, abort, flash, redirect, render_template, url_for
from flask.views import MethodView
from flask_login import current_user, login_required
from flask_smorest import Blueprint

# project-related
from .factory import EndpointMixinFactory
from .schemas import StoreSchema
from .services import store_service, DuplicateStoreError
from .user import login_as_franchisee_required
from .utils.nav import *

# misc
from marshmallow import Schema, INCLUDE


def NAV_CREATE_STORE():
    return (url_for(str(Store())), "Create Store")


blp = Blueprint("store", __name__, url_prefix="/store")

EndpointMixin = EndpointMixinFactory.create_endpoint(blp)


@blp.route("/")
class Store(MethodView, EndpointMixin):
    @login_required
    @login_as_franchisee_required
    def get(self):
        nav = get_nav_by_user(current_user)
        return render_template(
            "generic/create.html",
            title=f"New {type(self).__name__}",
            submit="Create",
            nav=nav,
            schema=StoreSchema,
            info={},
        )

    @login_required
    @login_as_franchisee_required
    @blp.arguments(StoreSchema, location="form")
    def post(self, store_input):
        app.logger.info(f"Creating {self.blp.name} for user {current_user.email!r}.")
        app.logger.debug(f"{self.blp.name.capitalize()} info: {store_input}.")
        nav = get_nav_by_user(current_user)
        try:
            store = store_service.create(owner_id=current_user.id, **store_input)
        except DuplicateStoreError as e:
            app.logger.error(e)
            flash(f"{e}", "error")
            return (
                render_template(
                    "generic/create.html",
                    title=f"New {type(self).__name__}",
                    submit="Create",
                    nav=nav,
                    schema=StoreSchema,
                    info=store_input,
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
                    schema=StoreSchema,
                    info=store_input,
                ),
                500,
            )
        else:
            app.logger.info(
                f"Successfully created {type(self).__name__} with id #{store.id}."
            )
            flash(f"{type(self).__name__} {store.name!r} created!")
            return redirect(url_for(str(Stores())))


@blp.route("/all")
class Stores(MethodView, EndpointMixin):
    def get(self):
        if current_user.is_authenticated and current_user.is_franchisee():
            stores = store_service.get_owned_by(current_user.id)
        else:
            stores = store_service.get_all()
        nav = get_nav_by_user(current_user)
        if current_user.is_authenticated and current_user.is_franchisee():
            nav = [NAV_CREATE_STORE()] + nav
        nav.remove(NAV_STORES())
        return render_template(
            "generic/all.html",
            title=f"{type(self).__name__}",
            nav=nav,
            table={
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
                    {"name": url_for(str(StoreId()), store_id=store.id)}
                    for store in stores
                ],
            },
        )


@blp.route("/<store_id>")
class StoreId(MethodView, EndpointMixin):
    @blp.arguments(Schema, location="query", as_kwargs=True, unknown=INCLUDE)
    def get(self, store_id, **kwargs):
        app.logger.info(f"Fetching {self.blp.name} #{store_id}.")
        store = store_service.get(store_id)
        if store:
            is_owner = current_user.is_authenticated and store.is_owner(current_user)
            nav = get_nav_by_user(current_user)
            return render_template(
                "generic/view.html",
                title=store.name,
                submit="Update",
                nav=nav,
                schema=StoreSchema,
                info={"name": store.name, "address": store.address or ""},
                is_owner=is_owner,
                update=is_owner and "edit" in kwargs,
                tables=[
                    {
                        "name": "vehicles",
                        "headers": ["picture", "plate", "make", "model", "year"],
                        "rows": [
                            {
                                "plate": vehicle.plate,
                                "make": vehicle.model.make.name,
                                "model": vehicle.model.name,
                                "year": vehicle.year,
                                "picture": vehicle.model.picture or "",
                            }
                            for vehicle in store.vehicles
                        ],
                        "refs": [
                            {
                                "plate": url_for(
                                    str("vehicle.VehicleId"), vehicle_id=vehicle.id
                                ),
                                "make": url_for(
                                    str("make.MakeId"), make_id=vehicle.model.make.id
                                ),
                                "model": url_for(
                                    str("model.ModelId"), model_id=vehicle.model.id
                                ),
                            }
                            for vehicle in store.vehicles
                        ],
                        "pics": ["picture"],
                    },
                ],
            )
        else:
            message = f"Store #{store_id} not found!"
            app.logger.error(message)
            flash(message, "error")
            return render_template("base.html"), 404

    @login_required
    @login_as_franchisee_required
    @blp.arguments(StoreSchema, location="form")
    def post(self, store_info, store_id):
        app.logger.info(f"Updating {self.blp.name} #{store_id}.")
        app.logger.debug(f"{self.blp.name.capitalize()} data: {store_info}.")
        store = store_service.get(store_id)
        if not store:
            abort(404)
        if not store.is_owner(current_user):
            abort(403)
        try:
            store = store_service.update(store_id, **store_info)
        except DuplicateStoreError as e:
            store = store_service.get(store_id)
            flash(f"{e}", "error")
            nav = get_nav_by_user(current_user)
            return render_template(
                "generic/view.html",
                title=store.name,
                submit="Update",
                nav=nav,
                schema=StoreSchema,
                info={
                    "name": store_info["name"],
                    "address": store_info["address"] or "",
                },
                is_owner=True,
                update=True,
            )
        return redirect(url_for(str(StoreId()), store_id=store_id))

    @login_required
    @login_as_franchisee_required
    def delete(self, store_id):
        app.logger.info(f"Deleting {self.blp.name} #{store_id}.")
        store = store_service.delete(store_id)
        if not store:
            abort(404)
        return redirect(url_for(str(Stores()))), 303
