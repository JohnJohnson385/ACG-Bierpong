import streamlit as st
import time
from datetime import date
import datenbank

def render_setup():
    st.subheader("📁 Turnier-Verwaltung")
    
    st.write("**Bestehendes Turnier laden**")
    all_t = datenbank.get_tournament_list()
    if all_t:
        col_l1, col_l2 = st.columns([3, 1])
        with col_l1:
            sel_load = st.selectbox("Wähle ein Turnier aus der Datenbank:", options=list(all_t.keys()), format_func=lambda x: all_t[x])
        with col_l2:
            st.write("") 
            st.write("")
            if st.button("📂 Turnier laden", use_container_width=True):
                datenbank.load_tournament(sel_load)
                st.success(f"Turnier '{all_t[sel_load]}' geladen!")
                st.rerun()
    else:
        st.info("Noch keine Turniere in der Datenbank.")
        
    st.divider()
    
    st.write("**Neues Turnier anlegen**")
    c1, c2 = st.columns(2)
    with c1:
        new_name = st.text_input("Name für das neue Turnier", "Neues Turnier")
        new_date = st.date_input("Datum", date.today())
    with c2:
        st.write("Spieler:")
        new_p = []
        for i in range(5):
            new_p.append(st.text_input(f"Slot {i+1}", value=f"Spieler {i+1}", key=f"new_p{i}"))
            
    if st.button("🆕 Neues Turnier erstellen & speichern", type="primary"):
        new_id = f"turnier_{int(time.time())}"
        st.session_state.current_tournament_id = new_id
        st.session_state.t_name = new_name
        st.session_state.t_date = str(new_date)
        st.session_state.players = new_p
        st.session_state.matches = datenbank.generate_fresh_matches()
        st.session_state.live = None
        datenbank.sync_to_cloud()
        st.success(f"Turnier '{new_name}' erfolgreich erstellt! Du kannst jetzt zu 'Live Spiel' wechseln.")
        st.rerun()

    st.divider()
    
    st.write("**🗑️ Turnier löschen**")
    if all_t:
        col_d1, col_d2 = st.columns([3, 1])
        with col_d1:
            sel_del = st.selectbox("Welches Turnier soll gelöscht werden?", options=list(all_t.keys()), format_func=lambda x: all_t[x], key="del_box")
        with col_d2:
            st.write("")
            st.write("")
            if st.button("🗑️ Löschen", use_container_width=True):
                st.session_state.confirm_delete = sel_del
                st.rerun()

        if st.session_state.confirm_delete == sel_del:
            st.error(f"⚠️ Bist du sicher, dass '{all_t[sel_del]}' unwiderruflich gelöscht werden soll?")
            cd1, cd2 = st.columns(2)
            if cd1.button("✔️ Ja, endgültig löschen", type="primary", use_container_width=True):
                db, connected = datenbank.get_db()
                if connected:
                    db.collection('bierpong_turniere').document(sel_del).delete()
                    st.session_state.confirm_delete = None
                    if st.session_state.current_tournament_id == sel_del:
                        st.session_state.current_tournament_id = None
                    st.success("Turnier erfolgreich gelöscht.")
                    st.rerun()
            if cd2.button("❌ Abbrechen", use_container_width=True):
                st.session_state.confirm_delete = None
                st.rerun()
