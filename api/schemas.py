from pydantic import BaseModel
from typing import List
from datetime import datetime

class LoginRequest(BaseModel):
    username: str
    password: str

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

    model_config = {
        "from_attributes": True
    }

class MatchPlayerBase(BaseModel):
    player_name: str
    team: str
    kills: int
    deaths: int
    assists: int

class MatchPlayer(MatchPlayerBase):
    model_config = {
        "from_attributes": True
    }

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

    model_config = {
        "from_attributes": True
    }
