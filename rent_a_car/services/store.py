# project-related
from ..db import *
from ..models import StoreModel

# misc
from sqlalchemy.exc import SQLAlchemyError, IntegrityError


class DuplicateStoreError(Exception):
    pass


class StoreService:
    def create_store(self, owner_id: int, name: str, address: str = None):
        if get_entries_filtered(StoreModel, name=name):
            raise DuplicateStoreError(f"The store {name!r} already exists!")
        store = StoreModel(name=name, address=address, owner_id=owner_id)
        try:
            add_entry(store)
        except SQLAlchemyError:
            raise
        else:
            return store

    def get_store(self, id: int):
        return get_entry(StoreModel, id)

    def delete_store(self, id: int):
        user = delete_entry(StoreModel, id)
        return user

    def update_store(self, id: int, name: str, address: str = None):
        store = get_entry(StoreModel, id)
        if store:
            store.name = name
            store.address = address
            try:
                add_entry(store)
            except IntegrityError:
                raise DuplicateStoreError(
                    f"There is already a store with the name {name!r}!"
                )
            except SQLAlchemyError:
                raise
        return store

    def get_user_by_name(self, name):
        return get_entry_by(StoreModel, name=name)

    def get_user_stores(self, owner_id):
        return get_entries_filtered(StoreModel, owner_id=owner_id)


service = StoreService()
