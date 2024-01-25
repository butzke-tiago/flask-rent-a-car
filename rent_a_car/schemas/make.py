from marshmallow import Schema, fields
from marshmallow.validate import Length


class MakeSchema(Schema):
    id = fields.Integer(required=True, dump_only=True)
    name = fields.String(required=True, validate=Length(1, 30))
    logo = fields.Url()
