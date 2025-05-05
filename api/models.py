from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    matches = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    kills = Column(Integer, default=0)
    deaths = Column(Integer, default=0)
    assists = Column(Integer, default=0)
    roundsWon = Column(Integer, default=0)
    roundsLost = Column(Integer, default=0)

class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=datetime.utcnow)
    map = Column(String)
    score_blue = Column(Integer)
    score_red = Column(Integer)

    players = relationship("MatchPlayer", back_populates="match")

class MatchPlayer(Base):
    __tablename__ = "match_players"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"))
    player_name = Column(String, ForeignKey("players.name"))
    team = Column(String)
    kills = Column(Integer)
    deaths = Column(Integer)
    assists = Column(Integer)

    match = relationship("Match", back_populates="players")
