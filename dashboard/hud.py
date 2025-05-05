import streamlit as st
import pandas as pd
import requests

API_URL = "http://localhost:8000"

st.set_page_config(page_title="FPL Dashboard", layout="wide")
st.title("🏆 FPL Dashboard - Estatísticas de Jogadores e Partidas")

def get_players():
    try:
        res = requests.get(f"{API_URL}/players")
        if res.status_code == 200:
            return pd.DataFrame(res.json())
    except Exception as e:
        st.error("Erro ao buscar jogadores.")
        st.exception(e)
    return pd.DataFrame()

def get_match(match_id):
    try:
        res = requests.get(f"{API_URL}/matches/{match_id}")
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        st.error("Erro ao buscar HUD da partida.")
        st.exception(e)
    return None

def create_player(name):
    try:
        res = requests.post(f"{API_URL}/players", json={"name": name})
        if res.status_code == 200:
            st.success("Jogador cadastrado com sucesso!")
        else:
            st.warning(res.json().get("msg", "Erro desconhecido."))
    except Exception as e:
        st.error("Erro ao cadastrar jogador.")
        st.exception(e)

def create_match(payload):
    try:
        res = requests.post(f"{API_URL}/matches", json=payload)
        if res.status_code == 200:
            st.success("Partida cadastrada com sucesso!")
        else:
            st.error(res.json().get("error", "Erro ao salvar partida."))
    except Exception as e:
        st.error("Erro ao salvar partida.")
        st.exception(e)

# Seção 1: Estatísticas gerais dos jogadores
st.subheader("📊 Estatísticas Gerais dos Jogadores (mínimo 3 partidas)")
df_players = get_players()

if not df_players.empty:
    df_filtered = df_players[df_players["matches"] >= 1]
    st.dataframe(df_filtered.sort_values(by="kills", ascending=False).reset_index(drop=True))
else:
    st.info("Nenhum jogador com 3 partidas encontradas.")

# Seção 2: Cadastro de jogador
st.subheader("➕ Cadastrar novo jogador")
with st.form("create_player_form"):
    name = st.text_input("Nome do jogador")
    submitted = st.form_submit_button("Cadastrar")
    if submitted and name:
        create_player(name)

# Seção 3: Cadastro de partida
st.subheader("📝 Registrar nova partida")
with st.form("create_match_form"):
    map_selected = st.selectbox("Mapa", [
        "Café Dostoyevsky", "Consulado", "Clube", "Fronteira", "Litoral", "Chalé",
        "Covil", "Laboratórios Nighthaven", "Planíce Esmeralda", "Banco", "Canal",
        "Oregon", "Outback", "Arranha-Céu", "Parque Temático", "Mansão"
    ])
    score_blue = st.number_input("Placar Time Azul", 0, 8, step=1)
    score_red = st.number_input("Placar Time Vermelho", 0, 8, step=1)

    known_players = df_players["name"].tolist() if not df_players.empty else []
    players_data = []
    st.markdown("**Selecione os 10 jogadores da partida**")
    for i in range(10):
        with st.expander(f"Jogador {i+1}"):
            player_name = st.selectbox(f"Nome do jogador {i+1}", options=known_players, key=f"player_{i}_name")
            team = "blue" if i < 5 else "red"
            st.text(f"Time: {team.capitalize()}")
            kills = st.number_input(f"Kills", 0, 50, key=f"kills_{i}")
            deaths = st.number_input(f"Deaths", 0, 50, key=f"deaths_{i}")
            assists = st.number_input(f"Assists", 0, 50, key=f"assists_{i}")
            players_data.append({
                "player_name": player_name,
                "team": team,
                "kills": kills,
                "deaths": deaths,
                "assists": assists
            })

    submit_match = st.form_submit_button("Registrar partida")
    if submit_match:
        payload = {
            "map": map_selected,
            "score_blue": score_blue,
            "score_red": score_red,
            "players": players_data
        }
        create_match(payload)

# Seção 4: Visualizar HUD da partida
st.subheader("🎯 Visualizar HUD de Partida")
match_id = st.number_input("Digite o ID da partida", min_value=1, step=1)
if st.button("Buscar Partida"):
    match_data = get_match(match_id)
    if match_data:
        st.markdown(f"### HUD - {match_data['map']} ({match_data['date'][:10]})")
        st.markdown(f"**Placar:** Azul {match_data['score']['blue']} x {match_data['score']['red']} Vermelho")
        df_match = pd.DataFrame(match_data['players'])
        st.dataframe(df_match)
    else:
        st.warning("Partida não encontrada.")
