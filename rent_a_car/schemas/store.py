from marshmallow import Schema, fields
from marshmallow.validate import Length


class StoreSchema(Schema):
    id = fields.Integer(required=True, dump_only=True)
    name = fields.String(required=True, validate=Length(2, 60))
    address = fields.String(validate=Length(2, 128))
    owner_id = fields.Integer(required=True, dump_only=True)
