import streamlit as st
import json
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import date

@st.cache_resource
def init_firebase():
    if not firebase_admin._apps:
        key_dict = json.loads(st.secrets["FIREBASE_KEY"], strict=False)
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)
    return firestore.client()

def get_db():
    try:
        return init_firebase(), True
    except Exception as e:
        st.error(f"Datenbank-Verbindungsfehler. Fehler: {e}")
        return None, False

def generate_fresh_matches():
    games_logic = [
        [0, 1, 2, 3], [1, 2, 3, 4], [2, 3, 4, 0], [3, 4, 0, 1], [4, 0, 1, 2],
        [0, 2, 1, 3], [1, 3, 2, 4], [2, 4, 3, 0], [3, 0, 4, 1], [4, 1, 0, 2],
        [0, 3, 1, 2], [1, 4, 2, 3], [2, 0, 3, 4], [3, 1, 4, 0], [4, 2, 0, 1]
    ]
    return [
        {
            "id": i, "t1_p1": g[0], "t1_p2": g[1], "t2_p1": g[2], "t2_p2": g[3], 
            "t1_score": None, "t2_score": None, "stats": None, "last_scorer": None, 
            "winner_turns": 0, "action_log": [], "live_backup": None,
            "bombs_events": [], "clutch_nachwurf_events": []
        }
        for i, g in enumerate(games_logic)
    ]

def get_tournament_list():
    db, connected = get_db()
    if connected:
        try:
            docs = db.collection('bierpong_turniere').stream()
            return {doc.id: doc.to_dict().get("t_name", "Unbekanntes Turnier") for doc in docs}
        except Exception:
            pass
    return {}

def load_tournament(doc_id):
    db, connected = get_db()
    if connected:
        doc = db.collection('bierpong_turniere').document(doc_id).get()
        if doc.exists:
            data = doc.to_dict()
            st.session_state.current_tournament_id = doc_id
            st.session_state.t_name = data.get("t_name", "Bierpong Meisterschaft")
            st.session_state.t_date = data.get("t_date", str(date.today()))
            st.session_state.players = data.get("players", ['Spieler 1', 'Spieler 2', 'Spieler 3', 'Spieler 4', 'Spieler 5'])
            st.session_state.matches = data.get("matches", generate_fresh_matches())
            st.session_state.live = data.get("live", None)

def sync_to_cloud():
    db, connected = get_db()
    if connected and st.session_state.current_tournament_id:
        doc_ref = db.collection('bierpong_turniere').document(st.session_state.current_tournament_id)
        data = {
            "t_name": st.session_state.t_name,
            "t_date": str(st.session_state.t_date),
            "players": st.session_state.players,
            "matches": st.session_state.matches,
            "live": st.session_state.live
        }
        doc_ref.set(data)
