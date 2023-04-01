import os

from kts_backend.web.app import application
from aiohttp.web import run_app


def main():
    run_app(
        application
        )


if __name__ == "__main__":
    main()
