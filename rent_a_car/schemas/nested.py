from marshmallow import Schema, fields
from marshmallow.validate import Length, Range


from .category import CategorySchema
from .make import MakeSchema
from .model import ModelSchema


class ModelSchemaNested(ModelSchema):
    make = fields.Nested(MakeSchema(), dump_only=True)
    category = fields.Nested(CategorySchema(), dump_only=True)


class MakeSchemaNested(MakeSchema):
    models = fields.List(fields.Nested(ModelSchema), dump_only=True)


class CategorySchemaNested(CategorySchema):
    models = fields.List(fields.Nested(ModelSchema), dump_only=True)
