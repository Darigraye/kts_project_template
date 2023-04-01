import os

from adminapi.web.app import setup_app
from aiohttp.web import run_app


def run_admin_api():
    run_app(
        setup_app(
            config_path=os.path.join(
                os.path.dirname(os.path.realpath(__file__)), "etc", "config.yaml"
            )
        )
    )


if __name__ == "__main__":
    run_admin_api()
