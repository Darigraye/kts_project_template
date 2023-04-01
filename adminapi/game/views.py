from aiohttp.web import HTTPForbidden, HTTPUnauthorized
from aiohttp.web_exceptions import HTTPNotFound
from aiohttp_apispec import docs, request_schema, response_schema, querystring_schema
from aiohttp_session import new_session, get_session

from adminapi.web.app import View
from adminapi.game.schemes import (GameRequestChatIdSchema,
                                   GameResponseSchema,
                                   GameSchema,
                                   ListGamesResponseSchema,
                                   GameRequestVkIdSchema)
from adminapi.web.utils import json_response
from adminapi.web.mixins import AuthRequiredMixin


class GetLatestGameView(AuthRequiredMixin, View):
    @docs(tags=["game"], summary="Get latest game in chat", description="Get game by chat_id")
    @querystring_schema(GameRequestChatIdSchema)
    @response_schema(GameResponseSchema, 200)
    async def get(self):
        await self.check_authentication(self.request)
        chat_id = int(self.request.query["chat_id"])
        if game := await self.request.app.store.games.get_latest_game(chat_id):
            return json_response(data=GameSchema().dump(game))
        raise HTTPNotFound


class GetAllGamesView(AuthRequiredMixin, View):
    @docs(tags=["game"], summary="Get games info", description="Get all games by chat_id")
    @querystring_schema(GameRequestChatIdSchema)
    @response_schema(ListGamesResponseSchema)
    async def get(self):
        await self.check_authentication(self.request)
        chat_id = int(self.request.query["chat_id"])
        if games := await self.request.app.store.games.get_all_games(chat_id):
            return json_response(data=[GameSchema().dump(game) for game in games])
        raise HTTPNotFound


class GetAllUserGames(AuthRequiredMixin, View):
    @docs(tags=["game"], summary="Get user games info", description="Get all games of user by vk_id")
    @querystring_schema(GameRequestVkIdSchema)
    @response_schema(ListGamesResponseSchema)
    async def get(self):
        await self.check_authentication(self.request)
        profile_id = int(self.request.query["profile_id"])
        if games := await self.request.app.store.games.get_all_games_of_user(profile_id):
            return json_response(data=[GameSchema().dump(game) for game in games])
        raise HTTPNotFound


class DeleteGamesInChatView(AuthRequiredMixin, View):
    @docs(tags=["game"], summary="Delete all games in chat", description="Delete all games in chat")
    @request_schema(GameRequestChatIdSchema)
    @response_schema(GameResponseSchema)
    async def post(self):
        await self.check_authentication(self.request)
        data = await self.request.json()
        if deleted_game := await self.request.app.store.games.delete_latest_game(data["chat_id"]):
            return json_response(data=GameSchema().dump(deleted_game))
        raise HTTPNotFound


class ClearDatabaseView(AuthRequiredMixin, View):
    @docs(tags=["game"], summary="Clear database", description="Delete all information in database")
    @response_schema(GameResponseSchema)
    async def post(self):
        await self.check_authentication(self.request)
        await self.request.app.store.games.clear_database()

        return json_response(data="Database was cleared")
