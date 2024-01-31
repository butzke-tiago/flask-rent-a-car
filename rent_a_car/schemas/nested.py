from marshmallow import fields


from .category import CategorySchema
from .make import MakeSchema
from .model import ModelSchema
from .store import StoreSchema
from .tag import TagSchema
from .user import UserSchema
from .vehicle import VehicleSchema


class CategorySchemaNested(CategorySchema):
    models = fields.List(fields.Nested(ModelSchema), dump_only=True)
    tags = fields.List(fields.Nested(TagSchema))


class MakeSchemaNested(MakeSchema):
    models = fields.List(fields.Nested(ModelSchema), dump_only=True)


class ModelSchemaNested(ModelSchema):
    make = fields.Nested(MakeSchema(), dump_only=True)
    category = fields.Nested(CategorySchema(), dump_only=True)
    vehicles = fields.List(fields.Nested(VehicleSchema()), dump_only=True)
    tags = fields.List(fields.Nested(TagSchema))
    category_tags = fields.List(fields.Nested(TagSchema))


class TagSchemaNested(TagSchema):
    categories = fields.List(fields.Nested(CategorySchema))
    models = fields.List(fields.Nested(ModelSchema))


class StoreSchemaNested(StoreSchema):
    owner = fields.Nested(UserSchema(), dump_only=True)
    vehicles = fields.List(fields.Nested(VehicleSchema()), dump_only=True)


class VehicleSchemaNested(VehicleSchema):
    model = fields.Nested(ModelSchema(), dump_only=True)
    store = fields.Nested(StoreSchema(), dump_only=True)
