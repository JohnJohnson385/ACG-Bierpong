import streamlit as st
import pandas as pd
from datetime import date

# Unsere neuen, sauberen Module importieren
import datenbank
import ui_setup
import ui_live_spiel
import ui_tabellen

try:
    from streamlit_autorefresh import st_autorefresh
    has_autorefresh = True
except ImportError:
    has_autorefresh = False

# 1. Seiten-Design initialisieren
st.set_page_config(page_title="Bierpong Live-App", page_icon="🍺", layout="wide")

# 2. Session State Grundvariablen
if 'current_tournament_id' not in st.session_state: st.session_state.current_tournament_id = None
if 't_name' not in st.session_state: st.session_state.t_name = "Bierpong Meisterschaft"
if 't_date' not in st.session_state: st.session_state.t_date = str(date.today())
if 'players' not in st.session_state: st.session_state.players = ['Spieler 1', 'Spieler 2', 'Spieler 3', 'Spieler 4', 'Spieler 5']
if 'matches' not in st.session_state: st.session_state.matches = datenbank.generate_fresh_matches()
if 'live' not in st.session_state: st.session_state.live = None
if 'confirm_abort' not in st.session_state: st.session_state.confirm_abort = False
if 'confirm_delete' not in st.session_state: st.session_state.confirm_delete = None

# Admin-Check
if 'admin_auth' not in st.session_state:
    st.session_state.admin_auth = st.query_params.get("admin") == "true"

def get_basic_standings():
    stats = []
    for i, p in enumerate(st.session_state.players):
        s = n = 0
        for m in st.session_state.matches:
            t1, t2 = m['t1_score'], m['t2_score']
            if t1 is not None and t2 is not None:
                if i in [m['t1_p1'], m['t1_p2']]:
                    if t1 > t2: s += 1
                    else: n += 1
                elif i in [m['t2_p1'], m['t2_p2']]:
                    if t2 > t1: s += 1
                    else: n += 1
        stats.append({'NAME': p, 'S': s, 'N': n, 'SCORE': s - n})
    df = pd.DataFrame(stats).sort_values(by=['SCORE', 'S'], ascending=[False, False]).reset_index(drop=True)
    df.index += 1
    df.insert(0, 'RANG', df.index)
    return df[['RANG', 'NAME', 'S', 'N']]

# 3. SIDEBAR (Login & Auswahl)
with st.sidebar:
    if not st.session_state.admin_auth:
        st.header("👀 Zuschauer-Modus")
        pwd = st.text_input("🔒 Admin Passwort:", type="password")
        if pwd == "acg987":
            st.session_state.admin_auth = True
            st.query_params["admin"] = "true" 
            st.rerun()
            
        st.write("---")
        st.write("**Aktuelles Turnier:**")
        all_t = datenbank.get_tournament_list()
        if all_t:
            sel_view = st.selectbox("Turnier auswählen", options=list(all_t.keys()), format_func=lambda x: all_t[x])
            if st.button("🔄 Manuell Aktualisieren", use_container_width=True):
                datenbank.load_tournament(sel_view)
                st.rerun()
                
            if has_autorefresh and st.session_state.current_tournament_id == sel_view:
                st_autorefresh(interval=5000, limit=None, key="viewer_refresh")
                datenbank.load_tournament(sel_view)
        else:
            st.caption("Keine Turniere gefunden.")
    else:
        st.header("👑 Master-Modus")
        if st.button("🚪 Logout (Zuschauer-Modus)", use_container_width=True):
            st.session_state.admin_auth = False
            if "admin" in st.query_params: del st.query_params["admin"] 
            st.rerun()
        
    st.write("---")
    st.write(f"**Live: {st.session_state.t_name}**")
    if st.session_state.current_tournament_id:
        st.dataframe(get_basic_standings(), hide_index=True, use_container_width=True)
    else:
        st.caption("Bitte lade oder erstelle erst ein Turnier.")

# 4. TABS BEREITSTELLEN
if st.session_state.admin_auth:
    tab1, tab2, tab3, tab4 = st.tabs(["⚙️ Setup / Archiv", "🎮 Live Spiel", "🏆 Tabelle & Spielplan", "📊 Statistiken"])
    
    with tab1: ui_setup.render_setup()
    with tab2: ui_live_spiel.render_live_spiel()
    with tab3: ui_tabellen.render_tabelle_und_spielplan()
    with tab4: ui_tabellen.render_statistiken()

else:
    tab3, tab4 = st.tabs(["🏆 Tabelle & Spielplan", "📊 Statistiken"])
    
    with tab3:
        if st.session_state.current_tournament_id: ui_tabellen.render_tabelle_und_spielplan()
        else: st.info("Warte auf Aktivierung des Turniers.")
    with tab4:
        if st.session_state.current_tournament_id: ui_tabellen.render_statistiken()
        else: st.info("Warte auf Datenfluss.")
