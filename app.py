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
        
        # HIER IST DER FIX: Die Seitenleiste greift auf die zentrale Logik der ui_tabellen zu!
        st.subheader("🏆 Live Tabelle")
        try:
            df_side = ui_tabellen.build_tabelle_data(st.session_state.players, st.session_state.matches)
            # Eine kompakte Version für die Sidebar ohne Treffer-Differenz-Gewusel
            st.dataframe(
                df_side[['RANG', 'NAME', 'SP', 'S', 'N', 'DIFF', 'STATUS']].style.map(ui_tabellen.style_df), 
                hide_index=True, 
                use_container_width=True
            )
        except Exception as e:
            st.caption("Tabelle wird aktualisiert...")
            
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
