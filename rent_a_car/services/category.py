# project-related
from ..db import *
from ..models import CategoryModel
from .base import BaseService, DuplicateError

# misc
from sqlalchemy.exc import SQLAlchemyError, IntegrityError


class DuplicateCategoryError(Exception):
    pass


class CategoryService(BaseService):
    def create(self, name: str, fare: float = None):
        return super().create(name, fare=fare)

    def update_category(self, id: int, name: str, fare: float):
        category = self.get(id)
        if category:
            category.name = name
            category.fare = fare
            try:
                return super().update(category)
            except DuplicateError:
                raise DuplicateCategoryError
        return category


service = CategoryService("category", CategoryModel)
