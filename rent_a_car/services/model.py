# project-related
from ..db import *
from ..models import ModelModel
from .base import BaseService, DuplicateError

# misc
from sqlalchemy.exc import SQLAlchemyError


class DuplicateModelError(DuplicateError):
    pass


class ModelService(BaseService):
    def create(self, name: str, make_id: int, category_id: int, picture: str = None):
        try:
            return super().create(
                name, make_id=make_id, category_id=category_id, picture=picture
            )
        except DuplicateError as e:
            raise DuplicateModelError(e)

    def update(
        self, id: int, name: str, make_id: int, category_id: int, picture: str = None
    ):
        model = self.get(id)
        if model:
            model.name = name
            model.make_id = make_id
            model.category_id = category_id
            model.picture = picture
            try:
                return super().update(model)
            except DuplicateError as e:
                raise DuplicateModelError(e)
        return model

    def add_tags(self, id: int, tags: list[ModelModel]):
        model = self.get(id)
        if model:
            for tag in tags:
                model.tags.append(tag)
            try:
                add_entry(model)
            except SQLAlchemyError:
                raise
        return model

    def remove_tags(self, id: int, tags: list[ModelModel]):
        model = self.get(id)
        if model:
            for tag in tags:
                try:
                    model.tags.remove(tag)
                except ValueError:
                    raise ValueError(
                        f"Tag {tag.name} is not associated to the model {model.name!r}!"
                    )
            try:
                add_entry(model)
            except SQLAlchemyError:
                raise
        return model


service = ModelService("model", ModelModel)
