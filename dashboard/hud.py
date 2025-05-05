import streamlit as st
import pandas as pd
import requests

API_URL = "http://localhost:8000"
st.set_page_config(page_title="FPL Dashboard", layout="wide")

if "is_admin" not in st.session_state:
    st.session_state["is_admin"] = False

def login(username, password):
    try:
        res = requests.post(f"{API_URL}/login", json={"username": username, "password": password})
        if res.status_code == 200:
            st.session_state["is_admin"] = True
            st.success("Login realizado com sucesso!")
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")
    except Exception as e:
        st.error("Erro ao realizar login.")
        st.exception(e)

def logout():
    st.session_state["is_admin"] = False
    st.success("Logout realizado.")
    st.rerun()

tabs_labels = ["🏆 Estatísticas"]
if st.session_state["is_admin"]:
    tabs_labels.append("🛠️ Administração")
else:
    tabs_labels.append("🔐 Login")

tabs = st.tabs(tabs_labels)

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

def get_player_matches(player_name):
    try:
        res = requests.get(f"{API_URL}/players/{player_name}/matches")
        if res.status_code == 200:
            return pd.DataFrame(res.json())
    except Exception as e:
        st.error("Erro ao buscar partidas do jogador.")
        st.exception(e)
    return pd.DataFrame()

def update_player_name(old_name, new_name):
    try:
        res = requests.put(f"{API_URL}/players/{old_name}", json={"name": new_name})
        if res.status_code == 200:
            st.success("Nome atualizado com sucesso!")
        else:
            st.error(res.json().get("error", "Erro ao atualizar nome."))
    except Exception as e:
        st.exception(e)

def delete_match(match_id):
    try:
        res = requests.delete(f"{API_URL}/matches/{match_id}?adjust_stats=true")
        if res.status_code == 200:
            st.success("Partida excluída com sucesso!")
        else:
            st.error(res.json().get("error", "Erro ao excluir partida."))
    except Exception as e:
        st.exception(e)

# Estatísticas (sempre visível)
with tabs[0]:
    st.title("🏆 FPL Dashboard - Estatísticas de Jogadores e Partidas")
    st.subheader("📊 Estatísticas Gerais dos Jogadores (mínimo 3 partidas)")
    df_players = get_players()
    if not df_players.empty:
        df_filtered = df_players[df_players["matches"] >= 3].copy()
        df_filtered = df_filtered[["name", "matches", "wins", "losses", "kills", "deaths", "assists", "roundsWon", "roundsLost"]]

        df_filtered["kd"] = (df_filtered["kills"] / df_filtered["deaths"]).round(2).fillna(0)
        df_filtered["winrate"] = ((df_filtered["wins"] / df_filtered["matches"]) * 100).round(2)
        df_filtered["saldo"] = df_filtered["roundsWon"] - df_filtered["roundsLost"]

        df_filtered["ranking_points"] = (
            (df_filtered["kills"] * 2) +
            (df_filtered["assists"]) +
            (df_filtered["wins"] * 7) +
            (df_filtered["kd"] * 10) +
            (df_filtered["winrate"] * 0.5) -
            (df_filtered["deaths"] * 2) -
            (df_filtered["losses"] * 7)
        ).round(1)

        df_filtered = df_filtered.sort_values(by="ranking_points", ascending=False).reset_index(drop=True)
        df_filtered.insert(0, "#", df_filtered.index + 1)

        df_filtered = df_filtered[[
            "#", "name", "ranking_points", "kills", "assists", "deaths", "wins", "losses",
            "kd", "winrate", "roundsWon", "roundsLost", "saldo"
        ]]

        selected_player = st.selectbox("Clique para ver histórico de um jogador", df_filtered["name"].tolist())
        st.dataframe(df_filtered)

        if selected_player:
            st.markdown(f"### Histórico de partidas de {selected_player}")
            df_history = get_player_matches(selected_player)
            if not df_history.empty:
                st.dataframe(df_history)
            else:
                st.info("Esse jogador ainda não possui partidas registradas.")
    else:
        st.info("Nenhum jogador com 3 partidas encontradas.")

# Administração (apenas se logado)
if st.session_state["is_admin"] and len(tabs) > 1:
    with tabs[1]:
        st.title("🛠️ Painel Administrativo")

        st.subheader("➕ Cadastrar novo jogador")
        with st.form("create_player_form"):
            name = st.text_input("Nome do jogador")
            submitted = st.form_submit_button("Cadastrar")
            if submitted and name:
                create_player(name)

        st.subheader("🔁 Atualizar nome do jogador")
        if not df_players.empty:
            old_name = st.selectbox("Selecione o nome atual", df_players["name"].tolist(), key="old_name")
            new_name = st.text_input("Novo nome", key="new_name")
            if st.button("Atualizar nome"):
                if old_name and new_name:
                    update_player_name(old_name, new_name)

        st.subheader("🗑️ Excluir partida")
        match_id_to_delete = st.number_input("ID da partida a ser excluída", min_value=1, step=1, key="delete_match")
        if st.button("Excluir partida"):
            delete_match(match_id_to_delete)

        st.subheader("📝 Adicionar nova partida")
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

        st.button("🚪 Logout", on_click=logout)
# Login
elif not st.session_state["is_admin"] and len(tabs) > 1:
    with tabs[1]:
        st.title("🔐 Login de Administrador")
        with st.form("login_form"):
            user = st.text_input("Usuário")
            passwd = st.text_input("Senha", type="password")
            submit = st.form_submit_button("Entrar")
            if submit:
                login(user, passwd)