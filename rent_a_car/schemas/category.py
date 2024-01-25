from marshmallow import Schema, fields
from marshmallow.validate import Length, Range


class CategorySchema(Schema):
    id = fields.Integer(required=True, dump_only=True)
    name = fields.String(required=True, validate=Length(1, 30))
    fare = fields.Float(validate=Range(min=0.0))
