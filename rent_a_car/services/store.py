# project-related
from ..db import *
from ..models import StoreModel
from .base import BaseService, DuplicateError

# misc
from sqlalchemy.exc import SQLAlchemyError, IntegrityError


class DuplicateStoreError(DuplicateError):
    pass


class StoreService(BaseService):
    def create(self, owner_id: int, name: str, address: str = None):
        try:
            return super().create(name, owner_id=owner_id, address=address)
        except DuplicateError as e:
            raise DuplicateStoreError(e)

    def update(self, id: int, name: str, address: str = None):
        store = self.get(id)
        if store:
            store.name = name
            store.address = address
            try:
                return super().update(store)
            except DuplicateError as e:
                raise DuplicateStoreError(e)
        return store

    def get_owned_by(self, owner_id):
        return get_entries_filtered(StoreModel, owner_id=owner_id)


service = StoreService("store", StoreModel)
