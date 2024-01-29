# flask-related
from flask import current_app as app, abort, flash, redirect, render_template, url_for
from flask.views import MethodView
from flask_login import current_user, login_required
from flask_smorest import Blueprint

# project-related
from .factory import EndpointMixinFactory
from .schemas import VehicleSchema, VehicleSchemaNested
from .services import (
    model_service,
    store_service,
    user_service,
    vehicle_service,
    DuplicateVehicleError,
)
from .user import login_as_franchisee_required
from .utils.nav import *


# misc
from marshmallow import Schema, INCLUDE
from urllib.parse import unquote


def NAV_CREATE_VEHICLE():
    return (url_for(str(Vehicle())), "Create Vehicle")


blp = Blueprint("vehicle", __name__, url_prefix="/vehicle")


EndpointMixin = EndpointMixinFactory.create_endpoint(blp)


@blp.before_request
def before_request():
    app.jinja_env.globals.update(type=type, zip=zip)


@blp.route("/")
class Vehicle(MethodView, EndpointMixin):
    @login_required
    @login_as_franchisee_required
    def get(self):
        nav = get_nav_by_role(current_user.role)
        return render_template(
            "generic/create.html",
            title=f"New {type(self).__name__}",
            submit="Create",
            nav=nav,
            schema=VehicleSchema,
            info={},
            map=get_map(),
        )

    @login_required
    @login_as_franchisee_required
    @blp.arguments(VehicleSchema, location="form")
    def post(self, vehicle):
        app.logger.info(f"Creating {self.blp.name}.")
        app.logger.debug(f"{self.blp.name.capitalize()} info: {vehicle}.")
        nav = get_nav_by_role(current_user.role)
        try:
            vehicle = vehicle_service.create(**vehicle)
        except DuplicateVehicleError as e:
            app.logger.error(e)
            flash(f"{e}", "error")
            return (
                render_template(
                    "generic/create.html",
                    title=f"New {type(self).__name__}",
                    submit="Create",
                    nav=nav,
                    schema=VehicleSchema,
                    info=vehicle,
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
                    schema=VehicleSchema,
                    info=vehicle,
                    map=get_map(),
                ),
                500,
            )
        else:
            app.logger.info(
                f"Successfully created {self.blp.name} with id #{vehicle.id}."
            )
            flash(f"{self.blp.name.capitalize()} {vehicle.plate!r} created!")
            return redirect(url_for(str(Vehicles())))


@blp.route("/all")
class Vehicles(MethodView, EndpointMixin):
    @login_required
    def get(self):
        if current_user.is_admin():
            vehicles = vehicle_service.get_all()
        else:
            vehicles = vehicle_service.get_owned_by(current_user.id)
        app.logger.debug(vehicles)
        nav = get_nav_by_role(current_user.role)
        if current_user.is_franchisee():
            nav = [NAV_CREATE_VEHICLE()] + nav
        nav.remove(NAV_VEHICLES())
        return render_template(
            "generic/all.html",
            title=f"{type(self).__name__}",
            nav=nav,
            table={
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
                        "name": url_for(str(VehicleId()), vehicle_id=vehicle.id),
                        "model": url_for("model.ModelId", model_id=vehicle.model_id),
                        "store": url_for("store.StoreId", store_id=vehicle.store_id),
                    }
                    for vehicle in vehicles
                ],
                "pics": ["picture"],
            },
        )


@blp.route("/<vehicle_id>")
class VehicleId(MethodView, EndpointMixin):
    @login_required
    @blp.arguments(Schema, location="query", as_kwargs=True, unknown=INCLUDE)
    def get(self, vehicle_id, **kwargs):
        app.logger.info(f"Fetching {self.blp.name} #{vehicle_id}.")
        vehicle = vehicle_service.get(vehicle_id)
        if vehicle:
            nav = get_nav_by_role(current_user.role)
            return render_template(
                "generic/view.html",
                title=vehicle.plate,
                submit="Update",
                nav=nav,
                schema=VehicleSchema,
                info=VehicleSchemaNested().dump(vehicle),
                is_owner=current_user.id == vehicle.store.owner_id,
                update="edit" in kwargs,
                map=get_map(),
            )
        else:
            message = f"{self.blp.name.capitalize()} #{vehicle_id} not found!"
            app.logger.error(message)
            flash(message, "error")
            return render_template("base.html"), 404

    @login_as_franchisee_required
    @blp.arguments(VehicleSchema, location="form")
    def post(self, vehicle_info, vehicle_id):
        app.logger.info(f"Updating {self.blp.name} #{vehicle_id}.")
        app.logger.debug(f"{self.blp.name.capitalize()} data: {vehicle_info}.")
        vehicle = vehicle_service.get(vehicle_id)
        if not vehicle:
            abort(404)
        if current_user.id != vehicle.store.owner_id:
            abort(403)
        try:
            vehicle = vehicle_service.update(vehicle_id, **vehicle_info)
        except DuplicateVehicleError as e:
            vehicle = vehicle_service.get(vehicle_id)
            flash(f"{e}", "error")
            nav = get_nav_by_role(current_user.role)
            return render_template(
                "generic/view.html",
                title=vehicle.plate,
                submit="Update",
                nav=nav,
                schema=VehicleSchema,
                info=vehicle_info,
                is_owner=True,
                update=True,
            )
        return redirect(url_for(str(VehicleId()), vehicle_id=vehicle_id))

    @login_as_franchisee_required
    def delete(self, vehicle_id):
        app.logger.info(f"Deleting {self.blp.name} #{vehicle_id}.")
        vehicle = vehicle_service.delete(vehicle_id)
        if not vehicle:
            app.logger.error(f"{self.blp.name.capitalize()} not found!")
            abort(404)
        return redirect(url_for(str(Vehicles()))), 303


def get_map():
    return {
        "model_id": {
            "name": "model",
            "url": unquote(url_for("model.ModelId", model_id={})),
            "options": (
                {
                    "value": model.id,
                    "name": model.name,
                }
                for model in model_service.get_all()
            ),
        },
        "store_id": {
            "name": "store",
            "url": unquote(url_for("store.StoreId", store_id={})),
            "options": (
                {
                    "value": store.id,
                    "name": store.name,
                }
                for store in store_service.get_owned_by(current_user.id)
            ),
        },
    }
