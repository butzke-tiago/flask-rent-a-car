# project-related
from ..db import *
from ..models import MakeModel
from .base import BaseService, DuplicateError


class DuplicateMakeError(DuplicateError):
    pass


class MakeService(BaseService):
    def create(self, name: str, logo: str = None):
        try:
            return super().create(name, logo=logo)
        except DuplicateError as e:
            raise DuplicateMakeError(e)

    def update(self, id: int, name: str, logo: str = None):
        make = self.get(id)
        if make:
            make.name = name
            make.logo = logo
            try:
                return super().update(make)
            except DuplicateError as e:
                raise DuplicateMakeError(e)
        return make


service = MakeService("make", MakeModel)
