from typing import TYPE_CHECKING, Optional
from dataclasses import dataclass

import yaml

if TYPE_CHECKING:
    from kts_backend.web.app import Application


@dataclass
class BotConfig:
    group_id: int
    token: str


@dataclass
class DatabaseConfig:
    host: str
    port: int
    user: str
    password: str
    database: str


@dataclass
class Config:
    bot: Optional[BotConfig] = None
    database: Optional[DatabaseConfig] = None


def config_from_yaml(config_path) -> Config:
    with open(config_path, 'r') as f:
        raw_config = yaml.safe_load(f)

    return Config(bot=BotConfig(group_id=raw_config['bot']['group_id'],
                                token=raw_config['bot']['token']),
                  database=DatabaseConfig(**raw_config['database']))


def setup_config(app: "Application", config_path: str) -> None:
    with open(config_path, 'r') as f:
        raw_config = yaml.safe_load(f)

    app.config = config_from_yaml(config_path)
