from marshmallow import Schema, fields

from adminapi.web.schemes import OkResponseSchema


class AdminSchema(Schema):
    login = fields.Str()


class RequestAdminSchema(Schema):
    login = fields.Str(required=True)
    password = fields.Str(required=True)


class ResponseAdminSchema(OkResponseSchema):
    data = fields.Nested(AdminSchema)
