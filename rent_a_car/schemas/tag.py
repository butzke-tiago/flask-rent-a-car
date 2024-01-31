from marshmallow import Schema, fields
from marshmallow.validate import Length


class TagSchema(Schema):
    id = fields.Integer(required=True, dump_only=True)
    name = fields.String(required=True, validate=Length(1, 30))


class TagInputSchema(Schema):
    available = fields.List(fields.Integer)
    assigned = fields.List(fields.Integer)
