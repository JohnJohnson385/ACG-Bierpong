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
                    match_opts[m['id']] = f"👉 NÄCHSTES - {txt}"; next_open_found = True
                else:
                    match_opts[m['id']] = f"⚪ OFFEN - {txt}"
                    
        sel_id = st.selectbox("Wähle ein Spiel aus der Liste:", options=list(match_opts.keys()), format_func=lambda x: match_opts[x])
        sel_m = st.session_state.matches[sel_id]
        
        if sel_m['t1_score'] is not None:
            st.info(f"Dieses Spiel ist bereits beendet (Ergebnis: {sel_m['t1_score']}:{sel_m['t2_score']} Rest-Becher).")
            if st.button("✏️ Spiel im Live-Modus bearbeiten", use_container_width=True):
                st.session_state.live = copy.deepcopy(sel_m['live_backup'])
                sel_m['t1_score'] = None; sel_m['t2_score'] = None; datenbank.sync_to_cloud(); st.rerun()
        else:
            if st.button("▶️ Spiel starten", type="primary", use_container_width=True):
                st.session_state.live = {
                    'match_id': sel_id, 'starter': None, 'possession': None, 't1_cups': 10, 't2_cups': 10, 
                    'balls_back': False, 'pending_bomb': False, 'bomb_team': None, 'pending_penalty': None,
                    't1_last_scorer': None, 't2_last_scorer': None, 'last_scorer': None, 'winner_team': None,
                    'action_log': [], 'history': [], 'game_state': 'playing', 'cups_at_turn_start': {'t1_cups': 10, 't2_cups': 10},
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
            st.button("❌ Spiel abbrechen", on_click=lambda: st.session_state.update(live=None))
        
        else:
            bg_t1 = "transparent"; bg_t2 = "transparent"
            if live['game_state'] == 't1_won': bg_t1 = "#d4edda"; bg_t2 = "#f8d7da"
            elif live['game_state'] == 't2_won': bg_t1 = "#f8d7da"; bg_t2 = "#d4edda"
            elif live['game_state'] == 'nachwurf_dialog': bg_t1 = "#fff3cd"; bg_t2 = "#fff3cd"
            else:
                if live['possession'] == 1: bg_t1 = "#e6f0fa"
                elif live['possession'] == 2: bg_t2 = "#e6f0fa"

            if live['game_state'] in ['t1_won', 't2_won']: st.success("🎉 SPIEL BEENDET!")
            elif live['balls_back']: st.success("🔥 BALLS BACK! Nochmal werfen.")

            pct_p1 = get_pct(live['stats'][f'p{i_p1}_h'], live['stats'][f'p{i_p1}_t'])
            pct_p2 = get_pct(live['stats'][f'p{i_p2}_h'], live['stats'][f'p{i_p2}_t'])
            pct_p3 = get_pct(live['stats'][f'p{i_p3}_h'], live['stats'][f'p{i_p3}_t'])
            pct_p4 = get_pct(live['stats'][f'p{i_p4}_h'], live['stats'][f'p{i_p4}_t'])

            disp1, disp_vs, disp2 = st.columns([5, 1, 5])
            with disp1:
                st.markdown(f"<div style='background-color:{bg_t1}; padding:15px; border-radius:10px;'><div style='text-align: center;'><span style='font-size: 55px; font-weight: bold;'>{live['t1_cups']}</span> Becher</div><p style='text-align:center; color:gray;'>{'🏁 Starter' if live['starter']==1 else '🛡️ Nachwurf'} | Zug: {live['stats']['turns_t1']}</p><h3 style='text-align: center;'>{'👑 ' if live['game_state']=='t1_won' else ''}{p1} & {p2}</h3><p style='text-align:center; font-size:14px; margin:0;'>{p1}: {live['stats'][f'p{i_p1}_h']} ({pct_p1}%) | {p2}: {live['stats'][f'p{i_p2}_h']} ({pct_p2}%)</p></div>", unsafe_allow_html=True)
            with disp_vs:
                st.markdown("<h3 style='text-align: center; margin-top: 45px; color: gray;'>VS</h3>", unsafe_allow_html=True)
            with disp2:
                st.markdown(f"<div style='background-color:{bg_t2}; padding:15px; border-radius:10px;'><div style='text-align: center;'><span style='font-size: 55px; font-weight: bold;'>{live['t2_cups']}</span> Becher</div><p style='text-align:center; color:gray;'>{'🏁 Starter' if live['starter']==2 else '🛡️ Nachwurf'} | Zug: {live['stats']['turns_t2']}</p><h3 style='text-align: center;'>{'👑 ' if live['game_state']=='t2_won' else ''}{p3} & {p4}</h3><p style='text-align:center; font-size:14px; margin:0;'>{p3}: {live['stats'][f'p{i_p3}_h']} ({pct_p3}%) | {p4}: {live['stats'][f'p{i_p4}_h']} ({pct_p4}%)</p></div>", unsafe_allow_html=True)

            st.write("---")

            # =========================================================================
            # DER MANUELLE NACHWURF-BILDSCHIRM
            # =========================================================================
            if live['game_state'] == 'nachwurf_dialog':
                anfang_team = live.get('anfang_team', 1)
                nw_team = 2 if anfang_team == 1 else 1
                
                p_nw_1 = p1 if nw_team == 1 else p3
                p_nw_2 = p2 if nw_team == 1 else p4
                i_nw_1 = i_p1 if nw_team == 1 else i_p3
                i_nw_2 = i_p2 if nw_team == 1 else i_p4
                
                st.error("🚨 NACHWURF-MODUS AKTIV 🚨")
                st.markdown(f"**Team {anfang_team} hat abgeräumt! Team {nw_team} hat nun Nachwurf.**")
                
                st.write("**1. Statistiken für den Nachwurf eintragen:**")
                col_nw1, col_nw2 = st.columns(2)
                with col_nw1:
                    st.markdown(f"**{p_nw_1}**")
                    w_1 = st.number_input(f"Würfe {p_nw_1}:", min_value=0, max_value=10, value=0, key="nw_w1")
                    t_1 = st.number_input(f"Treffer {p_nw_1}:", min_value=0, max_value=w_1, value=0, key="nw_t1")
                with col_nw2:
                    st.markdown(f"**{p_nw_2}**")
                    w_2 = st.number_input(f"Würfe {p_nw_2}:", min_value=0, max_value=10, value=0, key="nw_w2")
                    t_2 = st.number_input(f"Treffer {p_nw_2}:", min_value=0, max_value=w_2, value=0, key="nw_t2")

                # FEINARBEIT: Dreifachtreffer-Abfrage im Nachwurf
                st.write("---")
                nw_bombe = st.checkbox("💣 Gab es einen Dreifachtreffer (Bombe) im Nachwurf?")
                bombe_scorer_idx = None
                if nw_bombe:
                    bombe_scorer = st.selectbox("Wer hat den Dreifachtreffer erzielt?", options=[p_nw_1, p_nw_2], key="nw_bombe_p")
                    bombe_scorer_idx = i_nw_1 if bombe_scorer == p_nw_1 else i_nw_2

                st.write("---")
                st.write("**2. Wer hat im Nachwurf getroffen? (Für die Retter / Vollstrecker Statistik)**")
                retter_opts = ["Keiner"] + [p_nw_1, p_nw_2]
                retter_name = st.selectbox("Wer hat den entscheidenden Becher versenkt?", options=retter_opts)
                v_idx = None
                if retter_name == p_nw_1: v_idx = i_nw_1
                elif retter_name == p_nw_2: v_idx = i_nw_2

                st.write("---")
                st.write("**3. Schiedsrichter-Entscheidung treffen:**")
                c_btn1, c_btn2 = st.columns(2)
                
                # RETTUNG GEGLÜCKT
                if c_btn1.button("🟢 Rettung geglückt (Verlängerung)", use_container_width=True):
                    live['t1_cups'] = live['cups_at_turn_start']['t1_cups']
                    live['t2_cups'] = live['cups_at_turn_start']['t2_cups']
                    live['game_state'] = 'playing'
                    live['possession'] = anfang_team
                    live['anfang_last_scorer'] = None 
                    if v_idx is not None: live['clutch_nachwurf_events'].append(v_idx)
                    if nw_bombe and bombe_scorer_idx is not None: live['bombs_events'].append(bombe_scorer_idx)
                    live['stats'][f"p{i_nw_1}_t"] += w_1; live['stats'][f"p{i_nw_1}_h"] += t_1
                    live['stats'][f"p{i_nw_2}_t"] += w_2; live['stats'][f"p{i_nw_2}_h"] += t_2
                    logik_spiel.log_action("🔄 Nachwurf erfolgreich! Becher zurückgesetzt, Verlängerung gestartet.")
                    datenbank.sync_to_cloud(); st.rerun()

                # TEAM ANFANG GEWINNT
                if c_btn2.button(f"🏆 Team {anfang_team} gewinnt endgültig", use_container_width=True):
                    live['stats'][f"p{i_nw_1}_t"] += w_1; live['stats'][f"p{i_nw_1}_h"] += t_1
                    live['stats'][f"p{i_nw_2}_t"] += w_2; live['stats'][f"p{i_nw_2}_h"] += t_2
                    cups_hit = t_1 + t_2
                    if nw_team == 1: live['t2_cups'] = max(0, live['t2_cups'] - cups_hit)
                    else: live['t1_cups'] = max(0, live['t1_cups'] - cups_hit)
                    
                    live['game_state'] = 't1_won' if anfang_team == 1 else 't2_won'
                    live['winner_team'] = anfang_team
                    live['last_scorer'] = live.get('anfang_last_scorer') # Bestätigter Vollstrecker von Team Anfang!
                    logik_spiel.log_action(f"🎉 Team {anfang_team} gewinnt das Spiel endgültig!")
                    datenbank.sync_to_cloud(); st.rerun()
                    
                st.write("---")
                # KONTER-SIEG
                if st.button(f"🏆 Team {nw_team} dreht das Spiel und gewinnt!", use_container_width=True):
                    live['stats'][f"p{i_nw_1}_t"] += w_1; live['stats'][f"p{i_nw_1}_h"] += t_1
                    live['stats'][f"p{i_nw_2}_t"] += w_2; live['stats'][f"p{i_nw_2}_h"] += t_2
                    if nw_team == 1: live['t2_cups'] = 0
                    else: live['t1_cups'] = 0
                    
                    live['game_state'] = 't1_won' if nw_team == 1 else 't2_won'
                    live['winner_team'] = nw_team
                    # Wenn Bombe aktiv war, zählt die Bombe auch als Vollstrecker, sonst die manuelle Auswahl!
                    live['last_scorer'] = bombe_thrower_idx if (nw_bombe and bombe_scorer_idx is not None) else v_idx
                    if v_idx is not None: live['clutch_nachwurf_events'].append(v_idx)
                    if nw_bombe and bombe_scorer_idx is not None: live['bombs_events'].append(bombe_scorer_idx)
                    logik_spiel.log_action(f"🎉 Team {nw_team} dreht das Spiel im Nachwurf und gewinnt!")
                    datenbank.sync_to_cloud(); st.rerun()

            # =========================================================================
            # NORMALES SPIEL
            # =========================================================================
            elif live['game_state'] == 'playing':
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

                # FEINARBEIT: Dreifachtreffer-Vollstrecker Logik
                elif live.get('pending_bomb', False):
                    st.warning("💣 DREIFACHTREFFER zum Finish! Welcher Spieler hat den ZWEITEN Ball versenkt?")
                    bp1, bp2 = st.columns(2)
                    if live['bomb_team'] == 1:
                        if bp1.button(f"{p1} hat nachgeworfen", use_container_width=True): 
                            live['pending_bomb'] = False; logik_spiel.do_hit(1, 3, hits=[i_p1, i_p2], bombe_thrower=i_p1); st.rerun()
                        if bp2.button(f"{p2} hat nachgeworfen", use_container_width=True): 
                            live['pending_bomb'] = False; logik_spiel.do_hit(1, 3, hits=[i_p1, i_p2], bombe_thrower=i_p2); st.rerun()
                    else:
                        if bp1.button(f"{p3} hat nachgeworfen", use_container_width=True): 
                            live['pending_bomb'] = False; logik_spiel.do_hit(2, 3, hits=[i_p3, i_p4], bombe_thrower=i_p3); st.rerun()
                        if bp2.button(f"{p4} hat nachgeworfen", use_container_width=True): 
                            live['pending_bomb'] = False; logik_spiel.do_hit(2, 3, hits=[i_p3, i_p4], bombe_thrower=i_p4); st.rerun()
                
                else:
                    colL, colR = st.columns(2)
                    with colL:
                        if live['possession'] == 1:
                            st.button("🚫 Kein Treffer (Wechsel)", use_container_width=True, on_click=lambda: logik_spiel.do_miss(1))
                            c_h1, c_h2 = st.columns(2)
                            # FEINARBEIT: Wurfquoten-Abfrage bei nur 1 Becher Rest
                            if c_h1.button(f"🎯 Treffer {p1}", use_container_width=True): 
                                if live['t2_cups'] == 1:
                                    st.session_state.last_cup_click = {'team': 1, 'hitter': i_p1, 'partner': i_p2}
                                else:
                                    logik_spiel.do_hit(1, 1, hits=[i_p1], misses=[i_p2]); st.rerun()
                            if c_h2.button(f"🎯 Treffer {p2}", use_container_width=True): 
                                if live['t2_cups'] == 1:
                                    st.session_state.last_cup_click = {'team': 1, 'hitter': i_p2, 'partner': i_p1}
                                else:
                                    logik_spiel.do_hit(1, 1, hits=[i_p2], misses=[i_p1]); st.rerun()
                            
                            if live['t2_cups'] > 1:
                                c_s1, c_s2 = st.columns(2)
                                if c_s1.button("✌️ Doppel (-2)", use_container_width=True): 
                                    logik_spiel.do_hit(1, 2, hits=[i_p1, i_p2]); st.rerun()
                                if c_s2.button("💣 Dreifach (-3)", use_container_width=True): 
                                    logik_spiel.save_step(); live['pending_bomb'] = True; live['bomb_team'] = 1; datenbank.sync_to_cloud(); st.rerun()
                        st.write("")
                        if st.button("⚠️ Fehler Team 1", use_container_width=True): logik_spiel.save_step(); live['pending_penalty'] = 1; datenbank.sync_to_cloud(); st.rerun()

                    with colR:
                        if live['possession'] == 2:
                            st.button("🚫 Kein Treffer (Wechsel)", use_container_width=True, on_click=lambda: logik_spiel.do_miss(2))
                            c_h3, c_h4 = st.columns(2)
                            if c_h3.button(f"🎯 Treffer {p3}", use_container_width=True): 
                                if live['t1_cups'] == 1:
                                    st.session_state.last_cup_click = {'team': 2, 'hitter': i_p3, 'partner': i_p4}
                                else:
                                    logik_spiel.do_hit(2, 1, hits=[i_p3], misses=[i_p4]); st.rerun()
                            if c_h4.button(f"🎯 Treffer {p4}", use_container_width=True): 
                                if live['t1_cups'] == 1:
                                    st.session_state.last_cup_click = {'team': 2, 'hitter': i_p4, 'partner': i_p3}
                                else:
                                    logik_spiel.do_hit(2, 1, hits=[i_p4], misses=[i_p3]); st.rerun()
                            
                            if live['t1_cups'] > 1:
                                c_s3, c_s4 = st.columns(2)
                                if c_s3.button("✌️ Doppel (-2)", use_container_width=True): 
                                    logik_spiel.do_hit(2, 2, hits=[i_p3, i_p4]); st.rerun()
                                if c_s4.button("💣 Dreifach (-3)", use_container_width=True): 
                                    logik_spiel.save_step(); live['pending_bomb'] = True; live['bomb_team'] = 2; datenbank.sync_to_cloud(); st.rerun()
                        st.write("")
                        if st.button("⚠️ Fehler Team 2", use_container_width=True): logik_spiel.save_step(); live['pending_penalty'] = 2; datenbank.sync_to_cloud(); st.rerun()

                # FEINARBEIT: Wurfquoten-Abfrage Overlay für 1 Becher Rest
                if st.session_state.get('last_cup_click'):
                    cc = st.session_state.last_cup_click
                    st.markdown("---")
                    st.warning(f"🏆 Letzter Becher getroffen von {names[cc['hitter']]}! In welchem Wurf?")
                    col_fc1, col_fc2 = st.columns(2)
                    if col_fc1.button("Im 1. Wurf (Partner hatte keinen Wurf, kein Fehlwurf!)", use_container_width=True):
                        del st.session_state['last_cup_click']
                        logik_spiel.do_hit(cc['team'], 1, hits=[cc['hitter']], misses=[])
                        st.rerun()
                    if col_fc2.button("Im 2. Wurf (Partner hatte einen Fehlwurf!)", use_container_width=True):
                        del st.session_state['last_cup_click']
                        logik_spiel.do_hit(cc['team'], 1, hits=[cc['hitter']], misses=[cc['partner']])
                        st.rerun()

            else:
                st.write("### 📊 Spiel-Statistiken (Wurfquoten)")
                stats = live['stats']
                p1_h, p1_t = stats.get(f"p{i_p1}_h", 0), stats.get(f"p{i_p1}_t", 0)
                p1_q = (p1_h / p1_t * 100) if p1_t > 0 else 0.0
                p2_h, p2_t = stats.get(f"p{i_p2}_h", 0), stats.get(f"p{i_p2}_t", 0)
                p2_q = (p2_h / p2_t * 100) if p2_t > 0 else 0.0
                p3_h, p3_t = stats.get(f"p{i_p3}_h", 0), stats.get(f"p{i_p3}_t", 0)
                p3_q = (p3_h / p3_t * 100) if p3_t > 0 else 0.0
                p4_h, p4_t = stats.get(f"p{i_p4}_h", 0), stats.get(f"p{i_p4}_t", 0)
                p4_q = (p4_h / p4_t * 100) if p4_t > 0 else 0.0
                
                t1_s = [(p1, p1_h, p1_t, p1_q), (p2, p2_h, p2_t, p2_q)] if p1_q >= p2_q else [(p2, p2_h, p2_t, p2_q), (p1, p1_h, p1_t, p1_q)]
                t2_s = [(p3, p3_h, p3_t, p3_q), (p4, p4_h, p4_t, p4_q)] if p3_q >= p4_q else [(p4, p4_h, p4_t, p4_q), (p3, p3_h, p3_t, p3_q)]
                
                c_st1, c_st2 = st.columns(2)
                with c_st1:
                    st.markdown(f"**Team 1 ({p1} & {p2}):**")
                    for name, h, t, q in t1_s: st.write(f"🎯 **{name}**: {h} Treffer / {t} Würfe ({q:.2f}%)")
                with c_st2:
                    st.markdown(f"**Team 2 ({p3} & {p4}):**")
                    for name, h, t, q in t2_s: st.write(f"🎯 **{name}**: {h} Treffer / {t} Würfe ({q:.2f}%)")
                
                # ANZEIGEN-ERWEITERUNG: Wer war der Vollstrecker?
                st.write("---")
                v_id = live.get('last_scorer')
                v_name = names[v_id] if v_id is not None else "Keiner"
                st.markdown(f"🗡️ **Vollstrecker dieses Spiels:** `{v_name}`")

            # --- KONTROLL-LEISTE ---
            st.write("---")
            ctrl1, ctrl2, ctrl3 = st.columns(3)
            with ctrl1:
                if st.button("↩️ Undo", use_container_width=True, disabled=not live['history']):
                    last = live['history'].pop(); live.update(last); datenbank.sync_to_cloud(); st.rerun()
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
                        m['t1_score'] = live['t1_cups']; m['t2_score'] = live['t2_cups']; m['stats'] = copy.deepcopy(live['stats'])
                        m['last_scorer'] = live.get('last_scorer')
                        m['winner_team'] = live.get('winner_team') 
                        m['action_log'] = copy.deepcopy(live['action_log']); m['bombs_events'] = copy.deepcopy(live['bombs_events']); m['clutch_nachwurf_events'] = copy.deepcopy(live['clutch_nachwurf_events'])
                        m['winner_turns'] = live['stats']['turns_t1'] if live['game_state'] == 't1_won' else live['stats']['turns_t2']
                        m['live_backup'] = copy.deepcopy(live); st.session_state.live = None; datenbank.sync_to_cloud(); st.rerun()
                else: st.button("💾 Ergebnis speichern", use_container_width=True, disabled=True)

            # =========================================================================
            # SCHIEDSRICHTER-PANEL
            # =========================================================================
            st.write("---")
            with st.expander("🛠️ Schiedsrichter-Panel: Spielstand manuell überschreiben / Fehlerkorrektur"):
                st.warning("⚠️ Achtung: Änderungen hier überschreiben den aktuellen Zustand sofort in der Cloud!")
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    adj_t1_cups = st.number_input(f"Becher Team 1 ({p1} & {p2}):", min_value=0, max_value=10, value=int(live['t1_cups']), key="adj_t1_cups")
                    pos_options = [f"Team 1 ({p1} & {p2})", f"Team 2 ({p3} & {p4})"]
                    pos_index = 0 if live['possession'] == 1 else 1
                    adj_pos_str = st.radio("Wer hat aktuell Ballbesitz?", options=pos_options, index=pos_index, key="adj_pos")
                    adj_pos = 1 if adj_pos_str == pos_options[0] else 2
                with col_m2:
                    adj_t2_cups = st.number_input(f"Becher Team 2 ({p3} & {p4}):", min_value=0, max_value=10, value=int(live['t2_cups']), key="adj_t2_cups")
                    state_options = ["Laufendes Spiel (playing)", "Nachwurf-Dialog (nachwurf_dialog)", "Sieg Team 1 (t1_won)", "Sieg Team 2 (t2_won)"]
                    state_index = 0
                    if live['game_state'] == 'nachwurf_dialog': state_index = 1
                    elif live['game_state'] == 't1_won': state_index = 2
                    elif live['game_state'] == 't2_won': state_index = 3
                    adj_state_str = st.selectbox("Spiel-Status überschreiben:", options=state_options, index=state_index, key="adj_state")
                
                if st.button("💾 Manuelle Anpassungen übernehmen", type="primary", use_container_width=True):
                    logik_spiel.save_step()
                    live['t1_cups'] = adj_t1_cups; live['t2_cups'] = adj_t2_cups; live['possession'] = adj_pos
                    if adj_state_str == state_options[0]: live['game_state'] = 'playing'
                    elif adj_state_str == state_options[1]: live['game_state'] = 'nachwurf_dialog'
                    elif adj_state_str == state_options[2]: live['game_state'] = 't1_won'
                    elif adj_state_str == state_options[3]: live['game_state'] = 't2_won'
                    logik_spiel.log_action(f"🛠️ Schiedsrichter-Eingriff: Spielstand manuell angepasst! (Stand {live['t1_cups']}:{live['t2_cups']})")
                    datenbank.sync_to_cloud(); st.success("Geändert!"); st.rerun()
