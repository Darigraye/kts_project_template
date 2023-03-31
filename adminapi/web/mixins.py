from aiohttp_session import get_session
from aiohttp.web_exceptions import HTTPUnauthorized


class AuthRequiredMixin:
    @classmethod
    async def check_authentication(cls, request):
        session = await get_session(request)
        if session.empty:
            raise HTTPUnauthorized
