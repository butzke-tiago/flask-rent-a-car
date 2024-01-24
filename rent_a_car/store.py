# flask-related
from flask import current_app as app, abort, flash, redirect, render_template, url_for
from flask.views import MethodView
from flask_login import current_user, login_required
from flask_smorest import Blueprint

# project-related
from .schemas import StoreSchema
from .services import store_service, DuplicateStoreError
from .user import login_as_franchisee_required

# misc
from marshmallow import Schema, INCLUDE

blp = Blueprint("store", __name__, url_prefix="/store")


@blp.before_request
def before_request():
    app.jinja_env.globals.update(type=type, zip=zip)


@blp.route("/")
class Store(MethodView):
    @login_required
    @login_as_franchisee_required
    def get(self):
        return render_template(
            "generic/create.html",
            title="New Store",
            submit="Create",
            nav=[(url_for("store.Stores"), "Stores"), ("", "Fleet")],
            schema=StoreSchema,
            info={},
        )

    @login_required
    @login_as_franchisee_required
    @blp.arguments(StoreSchema, location="form")
    def post(self, store_input):
        app.logger.info(
            f"Creating {type(self).__name__} for user {current_user.email!r}."
        )
        app.logger.debug(f"{type(self).__name__} info: {store_input}.")
        try:
            store = store_service.create_store(owner_id=current_user.id, **store_input)
        except DuplicateStoreError as e:
            app.logger.error(e)
            flash(f"{e}", "error")
            return (
                render_template(
                    "generic/create.html",
                    title=f"New {type(self).__name__}",
                    submit="Create",
                    nav=[(url_for("store.Stores"), "Stores"), ("", "Fleet")],
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
                    nav=[(url_for("store.Stores"), "Stores"), ("", "Fleet")],
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
            return redirect(url_for("store.Stores"))


@blp.route("/all")
class Stores(MethodView):
    def get(self):
        stores = store_service.get_user_stores(current_user.id)
        return render_template(
            "generic/all.html",
            title=f"{type(self).__name__}",
            nav=[(url_for("store.Store"), "Create Store"), ("", "Fleet")],
            table={
                "name": "stores",
                "headers": ["name", "address"],
                "rows": [
                    {"name": store.name, "address": store.address or ""}
                    for store in stores
                ],
                "refs": [
                    {"name": url_for("store.StoreId", store_id=store.id)}
                    for store in stores
                ],
            },
        )


@blp.route("/<store_id>")
class StoreId(MethodView):
    @blp.arguments(Schema, location="query", as_kwargs=True, unknown=INCLUDE)
    def get(self, store_id, **kwargs):
        app.logger.info(f"Fetching Store #{store_id}.")
        store = store_service.get_store(store_id)
        if store:
            is_owner = (
                current_user.is_authenticated and current_user.id == store.owner_id
            )
            return render_template(
                "generic/view.html",
                title=store.name,
                submit="Update",
                nav=[(url_for("store.Stores"), "Stores"), ("", "Fleet")],
                schema=StoreSchema,
                info={"name": store.name, "address": store.address or ""},
                is_owner=is_owner,
                update=is_owner and "edit" in kwargs,
            )
        else:
            message = f"Store #{store_id} not found!"
            app.logger.error(message)
            flash(message, "error")
            return render_template("base.html"), 404

    @blp.arguments(StoreSchema, location="form")
    def post(self, store_info, store_id):
        app.logger.info(f"Updating Store #{store_id}.")
        app.logger.debug(f"Store data: {store_info}.")
        try:
            store = store_service.update_store(store_id, **store_info)
        except DuplicateStoreError as e:
            store = store_service.get_store(store_id)
            flash(f"{e}", "error")
            return render_template(
                "generic/view.html",
                title=store.name,
                submit="Update",
                nav=[(url_for("store.Stores"), "Stores"), ("", "Fleet")],
                schema=StoreSchema,
                info={
                    "name": store_info["name"],
                    "address": store_info["address"] or "",
                },
                is_owner=True,
                update=True,
            )
        if not store:
            abort(404)
        return redirect(url_for("store.StoreId", store_id=store_id))

    @login_as_franchisee_required
    def delete(self, store_id):
        app.logger.info(f"Deleting Store #{store_id}.")
        store = store_service.delete_store(store_id)
        if not store:
            abort(404)
        return redirect(url_for("store.Stores")), 303
