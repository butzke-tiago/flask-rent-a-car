# project-related
from ..db import *
from ..models import TagModel
from .base import BaseService, DuplicateError

# misc


class DuplicateTagError(DuplicateError):
    pass


class TagService(BaseService):
    def create(self, name: str):
        try:
            return super().create(name)
        except DuplicateError as e:
            raise DuplicateTagError(e)

    def update(self, id: int, name: str):
        tag = self.get(id)
        if tag:
            tag.name = name
            try:
                return super().update(tag)
            except DuplicateError as e:
                raise DuplicateTagError(e)
        return tag

    def get_many(self, tag_ids: list):
        return get_entries(self.model, tag_ids)


service = TagService("tag", TagModel)
