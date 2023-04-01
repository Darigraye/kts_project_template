import yaml
from typing import TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from adminapi.web.app import Application


@dataclass
class SessionConfig:
    key: str


@dataclass
class DatabaseConfig:
    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = "postgres"
    database: str = "project"


@dataclass
class Config:
    database: DatabaseConfig = None
    session: SessionConfig = None


def setup_config(app: "Application", config_path: str):
    with open(config_path, "r") as f:
        raw_config = yaml.safe_load(f)

    app.config = Config(database=DatabaseConfig(**raw_config["database"]),
                        session=SessionConfig(key=raw_config["session"]["key"])
                        )
