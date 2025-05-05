from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from database import SessionLocal, engine
import models, schemas
import logging
from dotenv import load_dotenv
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
ADMIN_USER = os.getenv("ADMIN_USER")
ADMIN_PASS = os.getenv("ADMIN_PASS")

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

@app.post("/login")
def login(data: schemas.LoginRequest):
    if data.username == ADMIN_USER and data.password == ADMIN_PASS:
        return {"success": True}
    else:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

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

@app.put("/players/{old_name}")
def update_player_name(old_name: str, new_data: schemas.PlayerCreate, db: Session = Depends(get_db)):
    try:
        player = db.query(models.Player).filter(models.Player.name == old_name).first()
        if not player:
            raise HTTPException(status_code=404, detail="Jogador não encontrado")

        db.query(models.MatchPlayer).filter(models.MatchPlayer.player_name == old_name).update({"player_name": new_data.name})
        player.name = new_data.name
        db.commit()
        return {"msg": "Nome do jogador atualizado com sucesso."}
    except Exception as e:
        logger.error(f"Erro ao atualizar nome do jogador: {e}", exc_info=True)
        return {"error": "Erro interno ao atualizar nome do jogador"}

@app.delete("/matches/{match_id}")
def delete_match(match_id: int, adjust_stats: bool = True, db: Session = Depends(get_db)):
    match = db.query(models.Match).filter(models.Match.id == match_id).first()
    if not match:
        return {"error": "Partida não encontrada"}

    players = db.query(models.MatchPlayer).filter_by(match_id=match_id).all()

    if adjust_stats:
        winning_team = "blue" if match.score_blue > match.score_red else "red"

        for p in players:
            player = db.query(models.Player).filter(models.Player.name == p.player_name).first()
            if player:
                player.matches = max(0, player.matches - 1)
                if p.team == winning_team:
                    player.wins = max(0, player.wins - 1)
                else:
                    player.losses = max(0, player.losses - 1)

                player.roundsWon = max(0, player.roundsWon - (match.score_blue if p.team == "blue" else match.score_red))
                player.roundsLost = max(0, player.roundsLost - (match.score_red if p.team == "blue" else match.score_blue))
                player.kills = max(0, player.kills - p.kills)
                player.deaths = max(0, player.deaths - p.deaths)
                player.assists = max(0, player.assists - p.assists)
                db.add(player)

    for p in players:
        db.delete(p)

    db.delete(match)
    db.commit()
    return {"msg": "Partida excluída e estatísticas ajustadas com sucesso"}

@app.put("/matches/{match_id}/players/{player_name}")
def update_match_player_stats(match_id: int, player_name: str, stats: schemas.MatchPlayerBase, db: Session = Depends(get_db)):
    try:
        player_match = db.query(models.MatchPlayer).filter_by(match_id=match_id, player_name=player_name).first()
        if not player_match:
            raise HTTPException(status_code=404, detail="Dados do jogador na partida não encontrados")

        player_match.kills = stats.kills
        player_match.deaths = stats.deaths
        player_match.assists = stats.assists
        db.commit()
        return {"msg": "Estatísticas da partida atualizadas com sucesso."}
    except Exception as e:
        logger.error(f"Erro ao atualizar estatísticas do jogador na partida: {e}", exc_info=True)
        return {"error": "Erro interno ao atualizar estatísticas"}

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

@app.get("/players/{player_name}/matches")
def get_player_matches(player_name: str, db: Session = Depends(get_db)):
    try:
        matches = (
            db.query(models.MatchPlayer)
            .filter(models.MatchPlayer.player_name == player_name)
            .all()
        )
        result = []
        for mp in matches:
            match = db.query(models.Match).filter(models.Match.id == mp.match_id).first()
            result.append({
                "match_id": mp.match_id,
                "map": match.map,
                "date": match.date,
                "team": mp.team,
                "kills": mp.kills,
                "deaths": mp.deaths,
                "assists": mp.assists
            })
        return result
    except Exception as e:
        logger.error(f"Erro ao buscar partidas do jogador {player_name}: {e}", exc_info=True)
        return {"error": "Erro interno ao buscar partidas do jogador"}

@app.get("/admin/overview")
def admin_overview(db: Session = Depends(get_db)):
    try:
        total_matches = db.query(models.Match).count()
        total_players = db.query(models.Player).count()
        return {
            "total_matches": total_matches,
            "total_players": total_players
        }
    except Exception as e:
        logger.error(f"Erro ao carregar visão geral do admin: {e}", exc_info=True)
        return {"error": "Erro interno ao carregar painel admin"}