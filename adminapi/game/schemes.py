from marshmallow import Schema, fields

from adminapi.web.schemes import OkResponseSchema


class GameRequestSchema(Schema):
    chat_id = fields.Int()


class PlayerSchema(Schema):
    profile_id = fields.Int()
    first_name = fields.Str()
    last_name = fields.Str()
    scores = fields.Int()


class GameSchema(Schema):
    id = fields.Int()
    chat_id = fields.Int()
    created_at = fields.DateTime()
    players = fields.Nested(PlayerSchema, many=True)


class GameResponseSchema(OkResponseSchema):
    data = fields.Nested(GameSchema)


class ListGamesResponseSchema(Schema):
    data = fields.Nested(GameSchema, many=True)
