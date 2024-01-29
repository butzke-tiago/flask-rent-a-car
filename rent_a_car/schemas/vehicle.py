from marshmallow import Schema, fields
from marshmallow.validate import And, Length, Range, Regexp


class VehicleSchema(Schema):
    id = fields.Integer(required=True, dump_only=True)
    plate = fields.String(
        required=True,
        validate=And(Regexp("[A-Za-z]{3}-[0-9][A-Za-z][0-9]{2}"), Length(equal=8)),
    )
    model_id = fields.Integer(required=True, validate=Range(min=1))
    year = fields.Integer(required=True, validate=Range(min=2020))
    store_id = fields.Integer(required=True, validate=Range(min=1))
