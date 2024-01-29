# project-related
from ..db import *
from ..models import VehicleModel, StoreModel
from .base import BaseService, DuplicateError

# misc
from sqlalchemy.exc import SQLAlchemyError, IntegrityError


class DuplicateVehicleError(DuplicateError):
    pass


class VehicleService(BaseService):
    def create(self, plate: str, model_id: int, year: int, store_id: int = None):
        if get_entries_filtered(self.model, plate=plate):
            raise DuplicateVehicleError(
                f"The plate {plate!r} is already associated with an vehicle!"
            )
        vehicle = self.model(
            plate=plate.upper(),
            model_id=model_id,
            year=year,
            store_id=store_id,
        )
        try:
            add_entry(vehicle)
        except SQLAlchemyError:
            raise
        else:
            return vehicle

    def update(
        self, id: int, plate: str, model_id: int, year: int, store_id: int = None
    ):
        vehicle = self.get(id)
        if vehicle:
            plate = plate.upper()
            vehicle.plate = plate
            vehicle.model_id = model_id
            vehicle.year = year
            vehicle.store_id = store_id
        try:
            add_entry(vehicle)
        except IntegrityError:
            raise DuplicateVehicleError(
                f"There is already a vehicle with the plate {plate!r}!"
            )
        except SQLAlchemyError:
            raise
        return vehicle

    def get_owned_by(self, owner_id):
        return get_entries_joined_filtered(
            VehicleModel, StoreModel, filter=StoreModel.owner_id == owner_id
        )


service = VehicleService("vehicle", VehicleModel)
