from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class PlayerBase(BaseModel):
    name: str

class PlayerCreate(PlayerBase):
    pass

class Player(PlayerBase):
    matches: int
    wins: int
    losses: int
    kills: int
    deaths: int
    assists: int
    roundsWon: int
    roundsLost: int

    class Config:
        orm_mode = True

class MatchPlayerBase(BaseModel):
    player_name: str
    team: str
    kills: int
    deaths: int
    assists: int

class MatchPlayer(MatchPlayerBase):
    class Config:
        orm_mode = True

class MatchCreate(BaseModel):
    map: str
    score_blue: int
    score_red: int
    players: List[MatchPlayerBase]

class MatchOut(BaseModel):
    date: datetime
    map: str
    score: dict
    players: List[MatchPlayer]

    class Config:
        orm_mode = True
