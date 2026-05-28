import streamlit as st
import copy
import datenbank
import logik_spiel

def get_pct(hits, throws):
    return int((hits / throws) * 100) if throws > 0 else 0

def render_live_spiel():
    if not st.session_state.current_tournament_id:
        st.warning("⚠️ Bitte lade zuerst ein Turnier im Setup-Reiter oder erstelle ein neues.")
        return
        
    if st.session_state.live is None:
        st.subheader("Spiel auswählen")
        match_opts = {}
        next_open_found = False
        for m in st.session_state.matches:
            p1, p2 = st.session_state.players[m['t1_p1']], st.session_state.players[m['t1_p2']]
            p3, p4 = st.session_state.players[m['t2_p1']], st.session_state.players[m['t2_p2']]
            txt = f"Spiel {m['id']+1}: {p1} & {p2} vs {p3} & {p4}"
            
            if m['t1_score'] is not None:
                match_opts[m['id']] = f"🟢 BEENDET - {txt} ({m['t1_score']}:{m['t2_score']})"
            else:
                if not next_open_found:
                    match_opts[m['id']] = f"👉 NÄCHSTES - {txt}"
                    next_open_found = True
                else:
                    match_opts[m['id']] = f"⚪ OFFEN - {txt}"
                    
        sel_id = st.selectbox("Wähle ein Spiel aus der Liste:", options=list(match_opts.keys()), format_func=lambda x: match_opts[x])
        sel_m = st.session_state.matches[sel_id]
        
        if sel_m['t1_score'] is not None:
            st.info(f"Dieses Spiel ist bereits beendet (Ergebnis: {sel_m['t1_score']}:{sel_m['t2_score']} Rest-Becher).")
            if st.button("✏️ Spiel im Live-Modus bearbeiten", use_container_width=True):
                st.session_state.live = copy.deepcopy(sel_m['live_backup'])
                sel_m['t1_score'] = None
                sel_m['t2_score'] = None
                datenbank.sync_to_cloud()
                st.rerun()
        else:
            if st.button("▶️ Spiel starten", type="primary", use_container_width=True):
                st.session_state.live = {
                    'match_id': sel_id, 'starter': None, 'possession': None,
                    't1_cups': 10, 't2_cups': 10, 'nachwurf': None, 
                    'balls_back': False, 'pending_bomb': False, 'bomb_team': None,
                    'pending_double_win': False, 'pending_last_cup': False, 'pending_penalty': None,
                    'single_nachwurf_team': None, 'single_nachwurf_shooter': None, 'last_cup_hitter': None,
                    't1_last_scorer': None, 't2_last_scorer': None,
                    'last_scorer': None, 'action_log': [], 'history': [], 'game_state': 'playing',
                    'cups_at_turn_start': {'t1_cups': 10, 't2_cups': 10},
                    'bombs_events': [], 'clutch_nachwurf_events': [],
                    'stats': {
                        'turns_t1': 0, 'turns_t2': 0,
                        f"p{sel_m['t1_p1']}_h": 0, f"p{sel_m['t1_p1']}_t": 0, f"p{sel_m['t1_p1']}_f": 0,
                        f"p{sel_m['t1_p2']}_h": 0, f"p{sel_m['t1_p2']}_t": 0, f"p{sel_m['t1_p2']}_f": 0,
                        f"p{sel_m['t2_p1']}_h": 0, f"p{sel_m['t2_p1']}_t": 0, f"p{sel_m['t2_p1']}_f": 0,
                        f"p{sel_m['t2_p2']}_h": 0, f"p{sel_m['t2_p2']}_t": 0, f"p{sel_m['t2_p2']}_f": 0,
                    }
                }
                datenbank.sync_to_cloud()
                st.rerun()

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
                logik_spiel.log_action(f"🏁 {p1} & {p2} fangen an.")
                datenbank.sync_to_cloud(); st.rerun()
            if cB.button(f"{p3} & {p4} beginnen", use_container_width=True): 
                live['starter'] = 2; live['possession'] = 2; live['stats']['turns_t2'] = 1
                logik_spiel.log_action(f"🏁 {p3} & {p4} fangen an.")
                datenbank.sync_to_cloud(); st.rerun()
            st.button("❌ Spiel abbrechen", on_click=lambda: st.session_state.update(live=None))
        
        else:
            bg_t1 = "transparent"
            bg_t2 = "transparent"
            
            if live['game_state'] == 't1_won': bg_t1 = "#d4edda"; bg_t2 = "#f8d7da"
            elif live['game_state'] == 't2_won': bg_t1 = "#f8d7da"; bg_t2 = "#d4edda"
            else:
                if live['possession'] == 1: bg_t1 = "#e6f0fa"
                elif live['possession'] == 2: bg_t2 = "#e6f0fa"

            if live['game_state'] == 'nachwurf_erfolgreich': st.success("🔥 NACHWURF ERFOLGREICH! Spiel geht weiter.")
            elif live['game_state'] in ['t1_won', 't2_won']: st.success("🎉 SPIEL BEENDET!")
            elif live.get('single_nachwurf_team') or live['nachwurf']: st.error(f"🚨 NACHWURF FÜR TEAM {live.get('single_nachwurf_team') or live['nachwurf']}!")
            elif live['balls_back']: st.success("🔥 BALLS BACK! Nochmal werfen.")

            pct_p1 = get_pct(live['stats'][f'p{i_p1}_h'], live['stats'][f'p{i_p1}_t'])
            pct_p2 = get_pct(live['stats'][f'p{i_p2}_h'], live['stats'][f'p{i_p2}_t'])
            pct_p3 = get_pct(live['stats'][f'p{i_p3}_h'], live['stats'][f'p{i_p3}_t'])
            pct_p4 = get_pct(live['stats'][f'p{i_p4}_h'], live['stats'][f'p{i_p4}_t'])

            disp1, disp_vs, disp2 = st.columns([5, 1, 5])
            
            with disp1:
                st.markdown(f"<div style='background-color:{bg_t1}; padding:15px; border-radius:10px;'>"
                            f"<div style='text-align: center; line-height: 1.1; margin-bottom: 5px;'>"
                            f"<span style='font-size: 55px; font-weight: bold;'>{live['t1_cups']}</span><span style='font-size: 16px;'> Becher</span></div>"
                            f"<p style='text-align:center; color:gray; font-size:14px; margin:0;'>{'🏁 Starter' if live['starter']==1 else '🛡️ Hat Nachwurf'} | Zug: {live['stats']['turns_t1']}</p>"
                            f"<h3 style='text-align: center; margin-bottom:5px;'>{'👑 ' if live['game_state']=='t1_won' else ''}{p1} & {p2}</h3>"
                            f"<p style='text-align:center; font-size:14px; margin:0;'>{p1}: {live['stats'][f'p{i_p1}_h']} ({pct_p1}%) | {p2}: {live['stats'][f'p{i_p2}_h']} ({pct_p2}%)</p>"
                            f"</div>", unsafe_allow_html=True)

            with disp_vs:
                st.markdown("<h3 style='text-align: center; margin-top: 45px; color: gray;'>VS</h3>", unsafe_allow_html=True)
                
            with disp2:
                st.markdown(f"<div style='background-color:{bg_t2}; padding:15px; border-radius:10px;'>"
                            f"<div style='text-align: center; line-height: 1.1; margin-bottom: 5px;'>"
                            f"<span style='font-size: 55px; font-weight: bold;'>{live['t2_cups']}</span><span style='font-size: 16px;'> Becher</span></div>"
                            f"<p style='text-align:center; color:gray; font-size:14px; margin:0;'>{'🏁 Starter' if live['starter']==2 else '🛡️ Hat Nachwurf'} | Zug: {live['stats']['turns_t2']}</p>"
                            f"<h3 style='text-align: center; margin-bottom:5px;'>{'👑 ' if live['game_state']=='t2_won' else ''}{p3} & {p4}</h3>"
                            f"<p style='text-align:center; font-size:14px; margin:0;'>{p3}: {live['stats'][f'p{i_p3}_h']} ({pct_p3}%) | {p4}: {live['stats'][f'p{i_p4}_h']} ({pct_p4}%)</p>"
                            f"</div>", unsafe_allow_html=True)

            st.write("---")

            if live['game_state'] == 'playing':
                if live.get('pending_penalty'):
                    team = live['pending_penalty']
                    st.warning(f"⚠️ Wer aus Team {team} hat den Fehler begangen?")
                    c_f1, c_f2 = st.columns(2)
                    if team == 1:
                        if c_f1.button(f"Schuld war {p1}", use_container_width=True): logik_spiel.do_penalty(1, i_p1); st.rerun()
                        if c_f2.button(f"Schuld war {p2}", use_container_width=True): logik_spiel.do_penalty(1, i_p2); st.rerun()
                    else:
                        if c_f1.button(f"Schuld war {p3}", use_container_width=True): logik_spiel.do_penalty(2, i_p3); st.rerun()
                        if c_f2.button(f"Schuld war {p4}", use_container_width=True): logik_spiel.do_penalty(2, i_p4); st.rerun()

                elif live.get('pending_bomb', False):
                    st.warning("💣 DREIFACHTREFFER! Welcher Spieler hat den ZWEITEN Ball versenkt?")
                    bp1, bp2 = st.columns(2)
                    is_n = bool(live['nachwurf'] or live.get('single_nachwurf_team'))
                    if live['bomb_team'] == 1:
                        if bp1.button(f"{p1}", use_container_width=True): logik_spiel.do_hit(1, 3, hits=[i_p1, i_p2], bombe_thrower=i_p1, is_balls_back=not is_n, is_clutch_nachwurf=is_n); live['pending_bomb'] = False; st.rerun()
                        if bp2.button(f"{p2}", use_container_width=True): logik_spiel.do_hit(1, 3, hits=[i_p1, i_p2], bombe_thrower=i_p2, is_balls_back=not is_n, is_clutch_nachwurf=is_n); live['pending_bomb'] = False; st.rerun()
                    else:
                        if bp1.button(f"{p3}", use_container_width=True): logik_spiel.do_hit(2, 3, hits=[i_p3, i_p4], bombe_thrower=i_p3, is_balls_back=not is_n, is_clutch_nachwurf=is_n); live['pending_bomb'] = False; st.rerun()
                        if bp2.button(f"{p4}", use_container_width=True): logik_spiel.do_hit(2, 3, hits=[i_p3, i_p4], bombe_thrower=i_p4, is_balls_back=not is_n, is_clutch_nachwurf=is_n); live['pending_bomb'] = False; st.rerun()
                
                elif live.get('pending_double_win', False):
                    st.warning("✌️ Doppeltreffer zum Sieg! Wer hat den ZWEITEN Becher getroffen?")
                    cw1, cw2 = st.columns(2)
                    is_n = bool(live['nachwurf'] or live.get('single_nachwurf_team'))
                    if live['bomb_team'] == 1: 
                        if cw1.button(f"{p1} war der Letzte", use_container_width=True): logik_spiel.do_hit(1, 2, hits=[i_p2, i_p1], misses=[], is_clutch_nachwurf=is_n, is_balls_back=False); live['pending_double_win'] = False; st.rerun()
                        if cw2.button(f"{p2} war der Letzte", use_container_width=True): logik_spiel.do_hit(1, 2, hits=[i_p1, i_p2], misses=[], is_clutch_nachwurf=is_n, is_balls_back=False); live['pending_double_win'] = False; st.rerun()
                    else:
                        if cw1.button(f"{p3} war der Letzte", use_container_width=True): logik_spiel.do_hit(2, 2, hits=[i_p4, i_p3], misses=[], is_clutch_nachwurf=is_n, is_balls_back=False); live['pending_double_win'] = False; st.rerun()
                        if cw2.button(f"{p4} war der Letzte", use_container_width=True): logik_spiel.do_hit(2, 2, hits=[i_p3, i_p4], misses=[], is_clutch_nachwurf=is_n, is_balls_back=False); live['pending_double_win'] = False; st.rerun()

                elif live.get('pending_last_cup', False):
                    st.warning("🏆 Letzter Treffer! In welchem Wurf wurde der Becher getroffen?")
                    c_w1, c_w2 = st.columns(2)
                    team = 1 if live['possession'] == 1 else 2
                    hitter_idx = live['last_cup_hitter']
                    partner_idx = i_p2 if hitter_idx == i_p1 else (i_p1 if hitter_idx == i_p2 else (i_p4 if hitter_idx == i_p3 else i_p3))
                    is_n = bool(live['nachwurf'] or live.get('single_nachwurf_team'))
                    
                    if c_w1.button("Im 1. Wurf (Gegner hat 1 Nachwurf)", use_container_width=True):
                        if team == 1 and live['starter'] == 1: live['single_nachwurf_team'] = 2
                        if team == 2 and live['starter'] == 2: live['single_nachwurf_team'] = 1
                        logik_spiel.do_hit(team, 1, hits=[hitter_idx], misses=[], is_clutch_nachwurf=is_n, is_balls_back=False)
                        live['pending_last_cup'] = False; st.rerun()
                    
                    if c_w2.button("Im 2. Wurf (Gegner hat 2 Nachwürfe)", use_container_width=True):
                        logik_spiel.do_hit(team, 1, hits=[hitter_idx], misses=[partner_idx], is_clutch_nachwurf=is_n, is_balls_back=False) 
                        live['pending_last_cup'] = False; st.rerun()

                elif live.get('single_nachwurf_team') == 1 and live['possession'] == 1:
                    if live.get('single_nachwurf_shooter') is None:
                        st.warning("🚨 Euer Team hat nur EINEN EINZIGEN Nachwurf! Wer wirft?")
                        sn1, sn2 = st.columns(2)
                        if sn1.button(f"🎯 {p1} wirft", use_container_width=True): logik_spiel.save_step(); live['single_nachwurf_shooter'] = i_p1; datenbank.sync_to_cloud(); st.rerun()
                        if sn2.button(f"🎯 {p2} wirft", use_container_width=True): logik_spiel.save_step(); live['single_nachwurf_shooter'] = i_p2; datenbank.sync_to_cloud(); st.rerun()
                    else:
                        shooter_idx = live['single_nachwurf_shooter']
                        st.info(f"Nachwurf von {names[shooter_idx]}")
                        snc1, snc2 = st.columns(2)
                        if snc1.button("🎯 Treffer!", use_container_width=True): logik_spiel.do_hit(1, 1, hits=[shooter_idx], misses=[], is_clutch_nachwurf=True); st.rerun()
                        if snc2.button("🚫 Verfehlt (Verloren)", use_container_width=True): logik_spiel.do_miss_single(1, shooter_idx); st.rerun()

                elif live.get('single_nachwurf_team') == 2 and live['possession'] == 2:
                    if live.get('single_nachwurf_shooter') is None:
                        st.warning("🚨 Euer Team hat nur EINEN EINZIGEN Nachwurf! Wer wirft?")
                        sn1, sn2 = st.columns(2)
                        if sn1.button(f"🎯 {p3} wirft", use_container_width=True): logik_spiel.save_step(); live['single_nachwurf_shooter'] = i_p3; datenbank.sync_to_cloud(); st.rerun()
                        if sn2.button(f"🎯 {p4} wirft", use_container_width=True): logik_spiel.save_step(); live['single_nachwurf_shooter'] = i_p4; datenbank.sync_to_cloud(); st.rerun()
                    else:
                        shooter_idx = live['single_nachwurf_shooter']
                        st.info(f"Nachwurf von {names[shooter_idx]}")
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
                                if c_s2.button("💣 Dreifach (-3)", use_container_width=True): 
                                    logik_spiel.save_step(); live['pending_bomb'] = True; live['bomb_team'] = 1; datenbank.sync_to_cloud(); st.rerun()
                        st.write("")
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
                                if c_s4.button("💣 Dreifach (-3)", use_container_width=True): 
                                    logik_spiel.save_step(); live['pending_bomb'] = True; live['bomb_team'] = 2; datenbank.sync_to_cloud(); st.rerun()
                        st.write("")
                        if st.button("⚠️ Fehler Team 2", use_container_width=True): logik_spiel.save_step(); live['pending_penalty'] = 2; datenbank.sync_to_cloud(); st.rerun()

            st.write("---")
            ctrl1, ctrl2, ctrl3 = st.columns(3)
            with ctrl1:
                if st.button("↩️ Undo", use_container_width=True, disabled=not live['history']):
                    last = live['history'].pop()
                    live.update(last)
                    datenbank.sync_to_cloud()
                    st.rerun()
                    
            with ctrl2:
                if st.session_state.confirm_abort:
                    st.warning("Wirklich abbrechen?")
                    cy, cn = st.columns(2)
                    if cy.button("✔️ Ja", use_container_width=True): st.session_state.live = None; st.session_state.confirm_abort = False; datenbank.sync_to_cloud(); st.rerun()
                    if cn.button("❌ Nein", use_container_width=True): st.session_state.confirm_abort = False; st.rerun()
                else:
                    if st.button("❌ Spiel Abbrechen", use_container_width=True): st.session_state.confirm_abort = True; st.rerun()
                        
            with ctrl3:
                if live['game_state'] in ['t1_won', 't2_won']:
                    if st.button("💾 Ergebnis speichern & Schließen", use_container_width=True, type="primary"):
                        m['t1_score'] = live['t1_cups']
                        m['t2_score'] = live['t2_cups']
                        m['stats'] = copy.deepcopy(live['stats'])
                        
                        if live['game_state'] == 't1_won': m['last_scorer'] = live.get('t1_last_scorer')
                        else: m['last_scorer'] = live.get('t2_last_scorer')
                        
                        m['action_log'] = copy.deepcopy(live['action_log'])
                        m['bombs_events'] = copy.deepcopy(live['bombs_events'])
                        m['clutch_nachwurf_events'] = copy.deepcopy(live['clutch_nachwurf_events'])
                        
                        if live['game_state'] == 't1_won': m['winner_turns'] = live['stats']['turns_t1'] 
                        else: m['winner_turns'] = live['stats']['turns_t2']
                        
                        m['live_backup'] = copy.deepcopy(live)
                        st.session_state.live = None
                        datenbank.sync_to_cloud()
                        st.rerun()
                elif live['game_state'] == 'nachwurf_erfolgreich':
                    if st.button("🔄 Spielstand zurücksetzen (Verlängerung)", use_container_width=True, type="primary"):
                        logik_spiel.log_action("🔄 Nachwurf erfolgreich! Spielstand auf Beginn der Runde zurückgesetzt.")
                        live['t1_cups'] = live['cups_at_turn_start']['t1_cups']
                        live['t2_cups'] = live['cups_at_turn_start']['t2_cups']
                        live['nachwurf'] = None 
                        live['single_nachwurf_team'] = None
                        live['single_nachwurf_shooter'] = None
                        live['game_state'] = 'playing'
                        live['possession'] = live['starter'] 
                        if live['starter'] == 1: live['stats']['turns_t1'] += 1
                        else: live['stats']['turns_t2'] += 1
                        datenbank.sync_to_cloud()
                        st.rerun()
                else:
                    st.button("💾 Ergebnis speichern", use_container_width=True, disabled=True)
