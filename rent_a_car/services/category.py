# project-related
from ..db import *
from ..models import CategoryModel, TagModel
from .base import BaseService, DuplicateError

# misc
from sqlalchemy.exc import SQLAlchemyError


class DuplicateCategoryError(DuplicateError):
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

    def add_tags(self, id: int, tags: list[TagModel]):
        category = self.get(id)
        if category:
            for tag in tags:
                category.tags.append(tag)
            try:
                add_entry(category)
            except SQLAlchemyError:
                raise
        return category

    def remove_tags(self, id: int, tags: list[TagModel]):
        category = self.get(id)
        if category:
            for tag in tags:
                try:
                    category.tags.remove(tag)
                except ValueError:
                    raise ValueError(
                        f"Tag {tag.name} is not associated to the category {category.name!r}!"
                    )
            try:
                add_entry(category)
            except SQLAlchemyError:
                raise
        return category


service = CategoryService("category", CategoryModel)
