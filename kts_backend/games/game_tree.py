import os
import sys
from typing import TYPE_CHECKING, Optional
from math import log
from random import randint

from aiohttp import ClientSession, TCPConnector

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from kts_backend.web.utils import build_query
from kts_backend.web.config import config_from_yaml


class PhotoNode:
    def __init__(self, photo_id):
        self.number_votes = 0
        self.photo_id = photo_id
        self.owner_id = photo_id.split("_")[0]


class GameTree:
    def __init__(self, list_user_photo_ids: list[str]):
        self.list_user_photo_ids: list[str] = list_user_photo_ids
        self.current_round: Optional[int] = None
        self.number_rounds: Optional[int] = int(log(len(list_user_photo_ids), 2))
        self.rounds: Optional[dict[int, list[tuple[PhotoNode, PhotoNode]]]] = None
        self.winner_nodes: Optional[list[PhotoNode]] = None

    async def start(self):
        self.current_round = 0
        self.number_rounds = int(log(len(self.list_user_photo_ids), 2))
        self.rounds: dict[int, list[tuple[PhotoNode, PhotoNode]]] = {
            number_round: [] for number_round in range(1, self.number_rounds + 1)
        }
        self.winner_nodes: list[PhotoNode] = [PhotoNode(photo_id=photo_id) for photo_id in self.list_user_photo_ids]
        await self.next_round()

    async def set_vote_for_current_pair(self, first: bool):
        current_pair = self.rounds[self.current_round][0]
        if first:
            current_pair[0].number_votes += 1
        else:
            current_pair[1].number_votes += 1

    async def next_pair(self):
        if self.rounds[self.current_round]:
            pair = self.rounds[self.current_round].pop(0)
            if pair[0].number_votes > pair[1].number_votes:
                self.winner_nodes.append(pair[0])
            elif pair[0].number_votes < pair[1].number_votes:
                self.winner_nodes.append(pair[1])
            else:
                self.winner_nodes.append(pair[randint(0, 1)])
        else:
            await self.next_round()

    async def next_round(self):
        self.current_round += 1
        for i in range(len(self.winner_nodes) // 2):
            self.rounds[self.current_round].append((self.winner_nodes.pop(0),
                                                    self.winner_nodes.pop(0)))

    @property
    def photo_ids_current_pair(self):
        return (self.rounds[self.current_round][0][0].photo_id,
                self.rounds[self.current_round][0][1].photo_id)
