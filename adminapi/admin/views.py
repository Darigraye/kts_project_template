from aiohttp.web import HTTPForbidden, HTTPUnauthorized
from aiohttp_apispec import docs, request_schema, response_schema
from aiohttp_session import new_session, get_session

from adminapi.web.app import View
from adminapi.admin.schemes import ResponseAdminSchema, RequestAdminSchema, AdminSchema
from adminapi.web.utils import json_response


class AdminRegistrationView(View):
    @docs(tags=["admin"], summary="Register new administrator", description="ok")
    @request_schema(RequestAdminSchema)
    @response_schema(ResponseAdminSchema, 200)
    async def post(self):
        data = await self.request.json()
        if await self.request.app.store.admins.get_by_login(data["login"]) is None:
            admin = await self.request.app.store.admins.create_admin(data["login"],
                                                                     data["password"])
            return json_response(data={"login": admin.login})

        raise Exception("Пользователь уже существует!")


class AdminLoginView(View):
    @docs(tags=["admin"], summary="Login administrator", description="ok")
    @request_schema(RequestAdminSchema)
    @response_schema(ResponseAdminSchema, 200)
    async def post(self):
        data = await self.request.json()
        if admin := await self.request.app.store.admins.get_by_login(data["login"]):
            if admin.is_password_valid(data["password"]):
                session = await new_session(request=self.request)
                session["admin"] = {
                    "login": admin.login
                }

                return json_response(data={"login": admin.login})
            raise HTTPForbidden


class AdminCurrentView(View):
    @docs(tags=["admin"], summary="Get current admin", description="ok")
    @response_schema(AdminSchema, 200)
    async def get(self):
        if session := await get_session(self.request):
            admin = self.store.admins.get_by_login(session["admin"]["login"])
            return json_response(data={"login": admin.login})
        else:
            raise HTTPUnauthorized
