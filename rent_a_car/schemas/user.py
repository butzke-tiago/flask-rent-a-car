from marshmallow import Schema, fields
from marshmallow.validate import Length


class UserSchema(Schema):
    id = fields.Integer(required=True, dump_only=True)
    email = fields.Email(required=True)
    password = fields.String(required=True, load_only=True)
    name = fields.String(required=True, validate=Length(2, 60))
