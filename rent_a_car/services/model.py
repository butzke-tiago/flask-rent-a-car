# project-related
from ..db import *
from ..models import ModelModel
from .base import BaseService, DuplicateError


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


service = ModelService("model", ModelModel)
