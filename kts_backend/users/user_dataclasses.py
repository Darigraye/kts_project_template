from dataclasses import dataclass
from datetime import datetime

from kts_backend.games.game_dataclasses import GameScore


@dataclass
class User:
    profile_id: int
    name: str
    last_name: str


@dataclass
class Player(User):
    score: GameScore
