import streamlit as st
from datetime import date
import time
import copy

# Neue Module importieren
import datenbank
import logik_spiel
import ui_tabellen

# Optionales Auto-Refresh für Zuschauer einbinden
try:
    from streamlit_autorefresh import st_autorefresh
    has_autorefresh = True
except ImportError:
    has_autorefresh = False

# Session State initialisieren
if 'current_tournament_id' not in st.session_state: st.session_state.current_tournament_id = None
if 't_name' not in st.session_state: st.session_state.t_name = "Bierpong Meisterschaft"
if 't_date' not in st.session_state: st.session_state.t_date = str(date.today())
if 'players' not in st.session_state: st.session_state.players = ['Spieler 1', 'Spieler 2', 'Spieler 3', 'Spieler 4', 'Spieler 5']
if 'matches' not in st.session_state: st.session_state.matches = datenbank.generate_fresh_matches()
if 'live' not in st.session_state: st.session_state.live = None
if 'confirm_abort' not in st.session_state: st.session_state.confirm_abort = False
if 'confirm_delete' not in st.session_state: st.session_state.confirm_delete = None

# URL-Parameter für dauerhaften Login prüfen
if 'admin_auth' not in st.session_state:
    st.session_state.admin_auth = st.query_params.get("admin") == "true"

# SIDEBAR RENDERN
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
        st.dataframe(ui_tabellen.get_basic_standings() if hasattr(ui_tabellen, 'get_basic_standings') else ui_tabellen.build_tabelle_data(st.session_state.players, st.session_state.matches)[['RANG', 'NAME', 'S', 'N']], hide_index=True, use_container_width=True)

# TABS AUFBAUEN
if st.session_state.admin_auth:
    tab1, tab2, tab3, tab4 = st.tabs(["⚙️ Setup / Archiv", "🎮 Live Spiel", "🏆 Tabelle & Spielplan", "📊 Statistiken"])
else:
    tab3, tab4 = st.tabs(["🏆 Tabelle & Spielplan", "📊 Statistiken"])

# SYSTEM-ZUTEILUNG NACH TAB
if st.session_state.admin_auth:
    with tab1:
        st.subheader("📁 Turnier-Verwaltung")
        all_t = datenbank.get_tournament_list()
        if all_t:
            col_l1, col_l2 = st.columns([3, 1])
            with col_l1: sel_load = st.selectbox("Wähle ein Turnier aus der Datenbank:", options=list(all_t.keys()), format_func=lambda x: all_t[x])
            with col_l2:
                st.write(""); st.write("")
                if st.button("📂 Turnier laden", use_container_width=True):
                    datenbank.load_tournament(sel_load); st.success(f"Turnier geladen!"); st.rerun()
        
        st.divider()
        st.write("**Neues Turnier anlegen**")
        c1, c2 = st.columns(2)
        with c1:
            new_name = st.text_input("Name für das neue Turnier", "Neues Turnier")
            new_date = st.date_input("Datum", date.today())
        with c2:
            st.write("Spieler:")
            new_p = [st.text_input(f"Slot {i+1}", value=f"Spieler {i+1}", key=f"new_p{i}") for i in range(5)]
                
        if st.button("🆕 Neues Turnier erstellen & speichern", type="primary"):
            st.session_state.current_tournament_id = f"turnier_{int(time.time())}"
            st.session_state.t_name = new_name
            st.session_state.t_date = str(new_date)
            st.session_state.players = new_p
            st.session_state.matches = datenbank.generate_fresh_matches()
            st.session_state.live = None
            datenbank.sync_to_cloud(); st.success(f"Turnier erstellt!"); st.rerun()

        st.divider()
        st.write("**🗑️ Turnier löschen**")
        if all_t:
            col_d1, col_d2 = st.columns([3, 1])
            with col_d1: sel_del = st.selectbox("Welches Turnier soll gelöscht werden?", options=list(all_t.keys()), format_func=lambda x: all_t[x], key="del_box")
            with col_d2:
                st.write(""); st.write("")
                if st.button("🗑️ Löschen", use_container_width=True): st.session_state.confirm_delete = sel_del; st.rerun()

            if st.session_state.confirm_delete == sel_del:
                st.error(f"⚠️ Unwiderruflich löschen?")
                cd1, cd2 = st.columns(2)
                if cd1.button("✔️ Ja, löschen", type="primary", use_container_width=True):
                    datenbank.get_db()[0].collection('bierpong_turniere').document(sel_del).delete()
                    st.session_state.confirm_delete = None
                    if st.session_state.current_tournament_id == sel_del: st.session_state.current_tournament_id = None
                    st.success("Gelöscht."); st.rerun()
                if cd2.button("❌ Abbrechen", use_container_width=True): st.session_state.confirm_delete = None; st.rerun()

    with tab2:
        if not st.session_state.current_tournament_id:
            st.warning("⚠️ Bitte lade zuerst ein Turnier im Setup-Reiter oder erstelle ein neues.")
        elif st.session_state.live is None:
            st.subheader("Spiel auswählen")
            match_opts = {}
            next_open_found = False
            for m in st.session_state.matches:
                p1, p2 = st.session_state.players[m['t1_p1']], st.session_state.players[m['t1_p2']]
                p3, p4 = st.session_state.players[m['t2_p1']], st.session_state.players[m['t2_p2']]
                txt = f"Spiel {m['id']+1}: {p1} & {p2} vs {p3} & {p4}"
                if m['t1_score'] is not None: match_opts[m['id']] = f"🟢 BEENDET - {txt} ({m['t1_score']}:{m['t2_score']})"
                else:
                    if not next_open_found: match_opts[m['id']] = f"👉 NÄCHSTES - {txt}"; next_open_found = True
                    else: match_opts[m['id']] = f"⚪ OFFEN - {txt}"
                        
            sel_id = st.selectbox("Wähle ein Spiel aus der Liste:", options=list(match_opts.keys()), format_func=lambda x: match_opts[x])
            sel_m = st.session_state.matches[sel_id]
            
            if sel_m['t1_score'] is not None:
                st.info(f"Dieses Spiel ist bereits beendet.")
                if st.button("✏️ Spiel im Live-Modus bearbeiten", use_container_width=True):
                    st.session_state.live = copy.deepcopy(sel_m['live_backup'])
                    sel_m['t1_score'] = None; sel_m['t2_score'] = None
                    datenbank.sync_to_cloud(); st.rerun()
            else:
                if st.button("▶️ Spiel starten", type="primary", use_container_width=True):
                    st.session_state.live = {
                        'match_id': sel_id, 'starter': None, 'possession': None, 't1_cups': 10, 't2_cups': 10, 'nachwurf': None, 
                        'balls_back': False, 'pending_bomb': False, 'bomb_team': None, 'pending_double_win': False, 'pending_last_cup': False, 'pending_penalty': None,
                        'single_nachwurf_team': None, 'single_nachwurf_shooter': None, 'last_cup_hitter': None, 't1_last_scorer': None, 't2_last_scorer': None,
                        'last_scorer': None, 'action_log': [], 'history': [], 'game_state': 'playing', 'cups_at_turn_start': {'t1_cups': 10, 't2_cups': 10},
                        'bombs_events': [], 'clutch_nachwurf_events': [],
                        'stats': {
                            'turns_t1': 0, 'turns_t2': 0,
                            f"p{sel_m['t1_p1']}_h": 0, f"p{sel_m['t1_p1']}_t": 0, f"p{sel_m['t1_p1']}_f": 0,
                            f"p{sel_m['t1_p2']}_h": 0, f"p{sel_m['t1_p2']}_t": 0, f"p{sel_m['t1_p2']}_f": 0,
                            f"p{sel_m['t2_p1']}_h": 0, f"p{sel_m['t2_p1']}_t": 0, f"p{sel_m['t2_p1']}_f": 0,
                            f"p{sel_m['t2_p2']}_h": 0, f"p{sel_m['t2_p2']}_t": 0, f"p{sel_m['t2_p2']}_f": 0,
                        }
                    }
                    datenbank.sync_to_cloud(); st.rerun()
        else:
            live = st.session_state.live
            m = st.session_state.matches[live['match_id']]
            names = st.session_state.players
            i_p1, i_p2, i_p3, i_p4 = m['t1_p1'], m['t1_p2'], m['t2_p1'], m['t2_p2']
            p1, p2, p3, p4 = names[i_p1], names[i_p2], names[i_p3], names[i_p4]

            if live['starter'] is None:
                st.info("🪨✂️📄 Wer fängt an?")
                cA, cB = st.columns(2)
                if cA.button(f"{p1} & {p2} beginnen", use_container_width=True): 
                    live['starter'] = 1; live['possession'] = 1; live['stats']['turns_t1'] = 1
                    logik_spiel.log_action(f"🏁 {p1} & {p2} fangen an."); datenbank.sync_to_cloud(); st.rerun()
                if cB.button(f"{p3} & {p4} beginnen", use_container_width=True): 
                    live['starter'] = 2; live['possession'] = 2; live['stats']['turns_t2'] = 1
                    logik_spiel.log_action(f"🏁 {p3} & {p4} fangen an."); datenbank.sync_to_cloud(); st.rerun()
            else:
                bg_t1 = "#e6f0fa" if live['possession'] == 1 else "transparent"
                bg_t2 = "#e6f0fa" if live['possession'] == 2 else "transparent"
                if live['game_state'] == 't1_won': bg_t1 = "#d4edda"; bg_t2 = "#f8d7da"
                elif live['game_state'] == 't2_won': bg_t1 = "#f8d7da"; bg_t2 = "#d4edda"

                if live['game_state'] == 'nachwurf_erfolgreich': st.success("🔥 NACHWURF ERFOLGREICH! Spiel geht weiter.")
                elif live['game_state'] in ['t1_won', 't2_won']: st.success("🎉 SPIEL BEENDET!")
                elif live.get('single_nachwurf_team') or live['nachwurf']: st.error(f"🚨 NACHWURF FÜR TEAM {live.get('single_nachwurf_team') or live['nachwurf']}!")
                elif live['balls_back']: st.success("🔥 BALLS BACK!")

                disp1, disp_vs, disp2 = st.columns([5, 1, 5])
                with disp1:
                    st.markdown(f"<div style='background-color:{bg_t1}; padding:15px; border-radius:10px;'><div style='text-align: center;'><span style='font-size: 55px; font-weight: bold;'>{live['t1_cups']}</span> Becher</div><p style='text-align:center; color:gray;'>{'🏁 Starter' if live['starter']==1 else '🛡️ Nachwurf'} | Zug: {live['stats']['turns_t1']}</p><h3 style='text-align: center;'>{'👑 ' if live['game_state']=='t1_won' else ''}{p1} & {p2}</h3></div>", unsafe_allow_html=True)
                with disp_vs: st.markdown("<h3 style='text-align: center; margin-top: 45px; color: gray;'>VS</h3>", unsafe_allow_html=True)
                with disp2:
                    st.markdown(f"<div style='background-color:{bg_t2}; padding:15px; border-radius:10px;'><div style='text-align: center;'><span style='font-size: 55px; font-weight: bold;'>{live['t2_cups']}</span> Becher</div><p style='text-align:center; color:gray;'>{'🏁 Starter' if live['starter']==2 else '🛡️ Nachwurf'} | Zug: {live['stats']['turns_t2']}</p><h3 style='text-align: center;'>{'👑 ' if live['game_state']=='t2_won' else ''}{p3} & {p4}</h3></div>", unsafe_allow_html=True)

                st.write("---")
                if live['game_state'] == 'playing':
                    if live.get('pending_penalty'):
                        team = live['pending_penalty']
                        c_f1, c_f2 = st.columns(2)
                        if team == 1:
                            if c_f1.button(f"Schuld war {p1}", use_container_width=True): logik_spiel.do_penalty(1, i_p1); st.rerun()
                            if c_f2.button(f"Schuld war {p2}", use_container_width=True): logik_spiel.do_penalty(1, i_p2); st.rerun()
                        else:
                            if c_f1.button(f"Schuld war {p3}", use_container_width=True): logik_spiel.do_penalty(2, i_p3); st.rerun()
                            if c_f2.button(f"Schuld war {p4}", use_container_width=True): logik_spiel.do_penalty(2, i_p4); st.rerun()
                    elif live.get('pending_bomb', False):
                        bp1, bp2 = st.columns(2)
                        is_n = bool(live['nachwurf'] or live.get('single_nachwurf_team'))
                        if live['bomb_team'] == 1:
                            if bp1.button(f"{p1}", use_container_width=True): logik_spiel.do_hit(1, 3, hits=[i_p1, i_p2], bombe_thrower=i_p1, is_balls_back=not is_n, is_clutch_nachwurf=is_n); live['pending_bomb'] = False; st.rerun()
                            if bp2.button(f"{p2}", use_container_width=True): logik_spiel.do_hit(1, 3, hits=[i_p1, i_p2], bombe_thrower=i_p2, is_balls_back=not is_n, is_clutch_nachwurf=is_n); live['pending_bomb'] = False; st.rerun()
                        else:
                            if bp1.button(f"{p3}", use_container_width=True): logik_spiel.do_hit(2, 3, hits=[i_p3, i_p4], bombe_thrower=i_p3, is_balls_back=not is_n, is_clutch_nachwurf=is_n); live['pending_bomb'] = False; st.rerun()
                            if bp2.button(f"{p4}", use_container_width=True): logik_spiel.do_hit(2, 3, hits=[i_p3, i_p4], bombe_thrower=i_p4, is_balls_back=not is_n, is_clutch_nachwurf=is_n); live['pending_bomb'] = False; st.rerun()
                    elif live.get('pending_double_win', False):
                        cw1, cw2 = st.columns(2)
                        is_n = bool(live['nachwurf'] or live.get('single_nachwurf_team'))
                        if live['bomb_team'] == 1:
                            if cw1.button(f"{p1} war der Letzte", use_container_width=True): logik_spiel.do_hit(1, 2, hits=[i_p2, i_p1], misses=[], is_clutch_nachwurf=is_n); live['pending_double_win'] = False; st.rerun()
                            if cw2.button(f"{p2} war der Letzte", use_container_width=True): logik_spiel.do_hit(1, 2, hits=[i_p1, i_p2], misses=[], is_clutch_nachwurf=is_n); live['pending_double_win'] = False; st.rerun()
                        else:
                            if cw1.button(f"{p3} war der Letzte", use_container_width=True): logik_spiel.do_hit(2, 2, hits=[i_p4, i_p3], misses=[], is_clutch_nachwurf=is_n); live['pending_double_win'] = False; st.rerun()
                            if cw2.button(f"{p4} war der Letzte", use_container_width=True): logik_spiel.do_hit(2, 2, hits=[i_p3, i_p4], misses=[], is_clutch_nachwurf=is_n); live['pending_double_win'] = False; st.rerun()
                    elif live.get('pending_last_cup', False):
                        c_w1, c_w2 = st.columns(2)
                        team = 1 if live['possession'] == 1 else 2
                        hitter_idx = live['last_cup_hitter']
                        partner_idx = i_p2 if hitter_idx == i_p1 else (i_p1 if hitter_idx == i_p2 else (i_p4 if hitter_idx == i_p3 else i_p3))
                        is_n = bool(live['nachwurf'] or live.get('single_nachwurf_team'))
                        if c_w1.button("Im 1. Wurf (Gegner hat 1 Nachwurf)", use_container_width=True):
                            if team == 1 and live['starter'] == 1: live['single_nachwurf_team'] = 2
                            if team == 2 and live['starter'] == 2: live['single_nachwurf_team'] = 1
                            logik_spiel.do_hit(team, 1, hits=[hitter_idx], misses=[], is_clutch_nachwurf=is_n); live['pending_last_cup'] = False; st.rerun()
                        if c_w2.button("Im 2. Wurf (Gegner hat 2 Nachwürfe)", use_container_width=True):
                            logik_spiel.do_hit(team, 1, hits=[hitter_idx], misses=[partner_idx], is_clutch_nachwurf=is_n); live['pending_last_cup'] = False; st.rerun()
                    elif live.get('single_nachwurf_team') == 1 and live['possession'] == 1:
                        if live.get('single_nachwurf_shooter') is None:
                            sn1, sn2 = st.columns(2)
                            if sn1.button(f"🎯 {p1} wirft", use_container_width=True): logik_spiel.save_step(); live['single_nachwurf_shooter'] = i_p1; datenbank.sync_to_cloud(); st.rerun()
                            if sn2.button(f"🎯 {p2} wirft", use_container_width=True): logik_spiel.save_step(); live['single_nachwurf_shooter'] = i_p2; datenbank.sync_to_cloud(); st.rerun()
                        else:
                            shooter_idx = live['single_nachwurf_shooter']
                            snc1, snc2 = st.columns(2)
                            if snc1.button("🎯 Treffer!", use_container_width=True): logik_spiel.do_hit(1, 1, hits=[shooter_idx], misses=[], is_clutch_nachwurf=True); st.rerun()
                            if snc2.button("🚫 Verfehlt (Verloren)", use_container_width=True): logik_spiel.do_miss_single(1, shooter_idx); st.rerun()
                    elif live.get('single_nachwurf_team') == 2 and live['possession'] == 2:
                        if live.get('single_nachwurf_shooter') is None:
                            sn1, sn2 = st.columns(2)
                            if sn1.button(f"🎯 {p3} wirft", use_container_width=True): logik_spiel.save_step(); live['single_nachwurf_shooter'] = i_p3; datenbank.sync_to_cloud(); st.rerun()
                            if sn2.button(f"🎯 {p4} wirft", use_container_width=True): logik_spiel.save_step(); live['single_nachwurf_shooter'] = i_p4; datenbank.sync_to_cloud(); st.rerun()
                        else:
                            shooter_idx = live['single_nachwurf_shooter']
                            snc1, snc2 = st.columns(2)
                            if snc1.button("🎯 Treffer!", use_container_width=True): logik_spiel.do_hit(2, 1, hits=[shooter_idx], misses=[], is_clutch_nachwurf=True); st.rerun()
                            if snc2.button("🚫 Verfehlt (Verloren)", use_container_width=True): logik_spiel.do_miss_single(2, shooter_idx); st.rerun()
                    else:
                        colL, colR = st.columns(2)
                        with colL:
                            if live['possession'] == 1:
                                st.button("🚫 Kein Treffer (Wechsel)", use_container_width=True, on_click=lambda: logik_spiel.do_miss(1))
                                c_h1, c_h2 = st.columns(2)
                                is_n = bool(live['nachwurf'])
                                if c_h1.button(f"🎯 Treffer {p1}", use_container_width=True):
                                    if live['t2_cups'] == 1: logik_spiel.save_step(); live['pending_last_cup'] = True; live['last_cup_hitter'] = i_p1; datenbank.sync_to_cloud(); st.rerun()
                                    else: logik_spiel.do_hit(1, 1, hits=[i_p1], misses=[i_p2], is_clutch_nachwurf=is_n); st.rerun()
                                if c_h2.button(f"🎯 Treffer {p2}", use_container_width=True):
                                    if live['t2_cups'] == 1: logik_spiel.save_step(); live['pending_last_cup'] = True; live['last_cup_hitter'] = i_p2; datenbank.sync_to_cloud(); st.rerun()
                                    else: logik_spiel.do_hit(1, 1, hits=[i_p2], misses=[i_p1], is_clutch_nachwurf=is_n); st.rerun()
                                if live['t2_cups'] > 1:
                                    c_s1, c_s2 = st.columns(2)
                                    if c_s1.button("✌️ Doppel (-2)", use_container_width=True):
                                        if live['t2_cups'] == 2: logik_spiel.save_step(); live['pending_double_win'] = True; live['bomb_team'] = 1; datenbank.sync_to_cloud(); st.rerun()
                                        else: logik_spiel.do_hit(1, 2, hits=[i_p1, i_p2], is_balls_back=not is_n, is_clutch_nachwurf=is_n); st.rerun()
                                    if c_s2.button("💣 Dreifach (-3)", use_container_width=True): logik_spiel.save_step(); live['pending_bomb'] = True; live['bomb_team'] = 1; datenbank.sync_to_cloud(); st.rerun()
                            if st.button("⚠️ Fehler Team 1", use_container_width=True): logik_spiel.save_step(); live['pending_penalty'] = 1; datenbank.sync_to_cloud(); st.rerun()
                        with colR:
                            if live['possession'] == 2:
                                st.button("🚫 Kein Treffer (Wechsel)", use_container_width=True, on_click=lambda: logik_spiel.do_miss(2))
                                c_h3, c_h4 = st.columns(2)
                                is_n = bool(live['nachwurf'])
                                if c_h3.button(f"🎯 Treffer {p3}", use_container_width=True):
                                    if live['t1_cups'] == 1: logik_spiel.save_step(); live['pending_last_cup'] = True; live['last_cup_hitter'] = i_p3; datenbank.sync_to_cloud(); st.rerun()
                                    else: logik_spiel.do_hit(2, 1, hits=[i_p3], misses=[i_p4], is_clutch_nachwurf=is_n); st.rerun()
                                if c_h4.button(f"🎯 Treffer {p4}", use_container_width=True):
                                    if live['t1_cups'] == 1: logik_spiel.save_step(); live['pending_last_cup'] = True; live['last_cup_hitter'] = i_p4; datenbank.sync_to_cloud(); st.rerun()
                                    else: logik_spiel.do_hit(2, 1, hits=[i_p4], misses=[i_p3], is_clutch_nachwurf=is_n); st.rerun()
                                if live['t1_cups'] > 1:
                                    c_s3, c_s4 = st.columns(2)
                                    if c_s3.button("✌️ Doppel (-2)", use_container_width=True):
                                        if live['t1_cups'] == 2: logik_spiel.save_step(); live['pending_double_win'] = True; live['bomb_team'] = 2; datenbank.sync_to_cloud(); st.rerun()
                                        else: logik_spiel.do_hit(2, 2, hits=[i_p3, i_p4], is_balls_back=not is_n, is_clutch_nachwurf=is_n); st.rerun()
                                    if c_s4.button("💣 Dreifach (-3)", use_container_width=True): logik_spiel.save_step(); live['pending_bomb'] = True; live['bomb_team'] = 2; datenbank.sync_to_cloud(); st.rerun()
                            if st.button("⚠️ Fehler Team 2", use_container_width=True): logik_spiel.save_step(); live['pending_penalty'] = 2; datenbank.sync_to_cloud(); st.rerun()

                st.write("---")
                ctrl1, ctrl2, ctrl3 = st.columns(3)
                with ctrl1:
                    if st.button("↩️ Undo", use_container_width=True, disabled=not live['history']):
                        last = live['history'].pop(); live.update(last); datenbank.sync_to_cloud(); st.rerun()
                with ctrl2:
                    if st.session_state.confirm_abort:
                        cy, cn = st.columns(2)
                        if cy.button("✔️ Ja", use_container_width=True): st.session_state.live = None; st.session_state.confirm_abort = False; datenbank.sync_to_cloud(); st.rerun()
                        if cn.button("❌ Nein", use_container_width=True): st.session_state.confirm_abort = False; st.rerun()
                    else:
                        if st.button("❌ Spiel Abbrechen", use_container_width=True): st.session_state.confirm_abort = True; st.rerun()
                with ctrl3:
                    if live['game_state'] in ['t1_won', 't2_won']:
                        if st.button("💾 Speichern & Schließen", use_container_width=True, type="primary"):
                            m['t1_score'] = live['t1_cups']; m['t2_score'] = live['t2_cups']; m['stats'] = copy.deepcopy(live['stats'])
                            m['last_scorer'] = live.get('t1_last_scorer') if live['game_state'] == 't1_won' else live.get('t2_last_scorer')
                            m['action_log'] = copy.deepcopy(live['action_log']); m['bombs_events'] = copy.deepcopy(live['bombs_events']); m['clutch_nachwurf_events'] = copy.deepcopy(live['clutch_nachwurf_events'])
                            m['winner_turns'] = live['stats']['turns_t1'] if live['game_state'] == 't1_won' else live['stats']['turns_t2']
                            m['live_backup'] = copy.deepcopy(live); st.session_state.live = None; datenbank.sync_to_cloud(); st.rerun()
                    elif live['game_state'] == 'nachwurf_erfolgreich':
                        if st.button("🔄 Zurücksetzen (Verlängerung)", use_container_width=True, type="primary"):
                            logik_spiel.log_action("🔄 Nachwurf erfolgreich! Reset auf Rundenbeginn.")
                            live['t1_cups'] = live['cups_at_turn_start']['t1_cups']; live['t2_cups'] = live['cups_at_turn_start']['t2_cups']
                            live['nachwurf'] = None; live['single_nachwurf_team'] = None; live['single_nachwurf_shooter'] = None; live['game_state'] = 'playing'; live['possession'] = live['starter']
                            if live['starter'] == 1: live['stats']['turns_t1'] += 1
                            else: live['stats']['turns_t2'] += 1
                            datenbank.sync_to_cloud(); st.rerun()
                    else: st.button("💾 Ergebnis speichern", use_container_width=True, disabled=True)

# RENDERE DIE PASSIEN VISUELLEN TABS (Für Zuschauer und Admins identisch)
with tab3:
    if st.session_state.current_tournament_id: ui_tabellen.render_tabelle_und_spielplan()
    else: st.info("Warte auf Aktivierung des Turniers.")

with tab4:
    if st.session_state.current_tournament_id: ui_tabellen.render_statistiken()
    else: st.info("Warte auf Datenfluss.")
