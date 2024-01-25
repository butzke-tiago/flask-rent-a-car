from marshmallow import Schema, fields
from marshmallow.validate import Length, Range


class ModelSchema(Schema):
    id = fields.Integer(required=True, dump_only=True)
    name = fields.String(required=True, validate=Length(1, 30))
    make_id = fields.Integer(required=True, validate=Range(min=1))
    category_id = fields.Integer(required=True, validate=Range(min=1))
    picture = fields.Url(dump_default="")
