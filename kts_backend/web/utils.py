import asyncio


class Timer:
    def __init__(self, timeout, callback):
        self._timeout = timeout
        self._callback = callback
        self._task = asyncio.create_task(self._job())

    async def _job(self):
        await asyncio.sleep(self._timeout)
        await self._callback()

    def cancel(self):
        self._task.cancel()


def build_query(host: str, method: str, params: dict) -> str:
    url = "https://" + host + method + "?"
    if "v" not in params:
        params["v"] = "5.131"
    url += "&".join([f"{key}={value}" for key, value in params.items()])
    return url
