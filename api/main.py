from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from database import SessionLocal, engine
import models, schemas
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/players")
def create_player(player: schemas.PlayerCreate, db: Session = Depends(get_db)):
    try:
        existing = db.query(models.Player).filter(models.Player.name == player.name).first()
        if existing:
            return {"msg": "Jogador já cadastrado."}

        new_player = models.Player(name=player.name)
        db.add(new_player)
        db.commit()
        db.refresh(new_player)
        return {"msg": "Jogador cadastrado com sucesso."}
    except Exception as e:
        logger.error(f"Erro ao cadastrar jogador: {e}", exc_info=True)
        return {"error": "Erro interno ao cadastrar jogador"}

@app.post("/matches")
def create_match(data: schemas.MatchCreate, db: Session = Depends(get_db)):
    try:
        match = models.Match(
            map=data.map,
            score_blue=data.score_blue,
            score_red=data.score_red
        )
        db.add(match)
        db.commit()
        db.refresh(match)

        winning_team = "blue" if match.score_blue > match.score_red else "red"

        for p in data.players:
            player = db.query(models.Player).filter(models.Player.name == p.player_name).first()

            if not player:
                continue

            player.matches += 1
            if p.team == winning_team:
                player.wins += 1
            else:
                player.losses += 1

            player.roundsWon += match.score_blue if p.team == "blue" else match.score_red
            player.roundsLost += match.score_red if p.team == "blue" else match.score_blue

            player.kills += p.kills
            player.deaths += p.deaths
            player.assists += p.assists

            db.add(player)

            mp = models.MatchPlayer(
                match_id=match.id,
                player_name=p.player_name,
                team=p.team,
                kills=p.kills,
                deaths=p.deaths,
                assists=p.assists
            )
            db.add(mp)

        db.commit()
        return {"match_id": match.id, "msg": "Partida salva com sucesso"}

    except Exception as e:
        logger.error(f"Erro ao criar partida: {e}", exc_info=True)
        return {"error": "Erro interno ao registrar a partida"}

@app.get("/matches/{match_id}", response_model=schemas.MatchOut)
def get_match(match_id: int, db: Session = Depends(get_db)):
    try:
        match = db.query(models.Match).filter(models.Match.id == match_id).first()
        if not match:
            return {"error": "Partida não encontrada"}

        players = db.query(models.MatchPlayer).filter_by(match_id=match.id).all()

        return {
            "date": match.date,
            "map": match.map,
            "score": {
                "blue": match.score_blue,
                "red": match.score_red
            },
            "players": players
        }

    except Exception as e:
        logger.error(f"Erro ao buscar HUD da partida {match_id}: {e}", exc_info=True)
        return {"error": "Erro interno ao buscar dados da partida"}

@app.get("/players")
def get_players(db: Session = Depends(get_db)):
    try:
        return db.query(models.Player).all()
    except Exception as e:
        logger.error(f"Erro ao buscar jogadores: {e}", exc_info=True)
        return {"error": "Erro interno ao buscar jogadores"}
