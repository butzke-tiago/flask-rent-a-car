# project-related
from ..db import *

# misc
from sqlalchemy.exc import SQLAlchemyError, IntegrityError


class DuplicateError(Exception):
    pass


class BaseService:
    def __init__(self, name, model):
        self.name = name
        self.model = model

    def create(self, name: str, **kwargs):
        if get_entries_filtered(self.model, name=name):
            raise DuplicateError(f"The {self.name} {name!r} already exists!")
        entry = self.model(name=name, **kwargs)
        try:
            add_entry(entry)
        except SQLAlchemyError:
            raise
        else:
            return entry

    def get(self, id: int):
        return get_entry(self.model, id)

    def delete(self, id: int):
        user = delete_entry(self.model, id)
        return user

    def update(self, entry):
        name = entry.name
        try:
            add_entry(entry)
        except IntegrityError:
            raise DuplicateError(
                f"There is already a {self.name} with the name {name!r}!"
            )
        except SQLAlchemyError:
            raise
        return entry

    def get_all(self):
        return get_all_entries(self.model)
