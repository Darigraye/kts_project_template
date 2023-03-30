from typing import TYPE_CHECKING

from dataclasses import dataclass
from datetime import datetime

if TYPE_CHECKING:
    from kts_backend.users.user_dataclasses import Player


@dataclass
class GameScore:
    scores: int


@dataclass
class Game:
    created_at: datetime
    chat_id: int
    players: list["Player"]
