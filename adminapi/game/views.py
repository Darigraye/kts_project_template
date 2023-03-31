from aiohttp.web import HTTPForbidden, HTTPUnauthorized
from aiohttp.web_exceptions import HTTPNotFound
from aiohttp_apispec import docs, request_schema, response_schema, querystring_schema
from aiohttp_session import new_session, get_session

from adminapi.web.app import View
from adminapi.game.schemes import (GameRequestSchema,
                                   GameResponseSchema,
                                   GameSchema,
                                   ListGamesResponseSchema)
from adminapi.web.utils import json_response


class GetLatestGameView(View):
    @docs(tags=["game"], summary="Get latest game in chat", description="Get game by chat_id")
    @querystring_schema(GameRequestSchema)
    @response_schema(GameResponseSchema, 200)
    async def get(self):
        chat_id = int(self.request.query["chat_id"])
        if game := await self.request.app.store.games.get_latest_game(chat_id):
            return json_response(data=GameSchema().dump(game))
        raise HTTPNotFound


class GetAllGamesView(View):
    @docs(tags=["game"], summary="Get games info", description="Get all games by chat_id")
    @querystring_schema(GameRequestSchema)
    @response_schema(ListGamesResponseSchema)
    async def get(self):
        chat_id = int(self.request.query["chat_id"])
        if games := await self.request.app.store.games.get_all_games(chat_id):
            return json_response(data= [GameSchema().dump(game) for game in games])
        raise HTTPNotFound
