import streamlit as st
import pandas as pd
import io

def style_df(val):
    if val == 'Eliminated': return 'color: #9C0006; font-weight: bold'
    if val == 'Titel drin': return 'color: #008000; font-weight: bold'
    if val == '👑 MEISTER': return 'background-color: #FFD966; color: black; font-weight: bold'
    if isinstance(val, int) and val > 0: return 'color: #008000; font-weight: bold'
    if isinstance(val, int) and val < 0: return 'color: #FF0000; font-weight: bold'
    if isinstance(val, str) and 'S' in val and val != "STATUS": return 'color: #008000; font-weight: bold'
    if isinstance(val, str) and 'N' in val and val != "NAME" and val != "STATUS": return 'color: #FF0000; font-weight: bold'
    return ''

def build_tabelle_data(players, matches):
    # Initialisiere manuelle Overrides im SessionState falls nicht existent
    if 'master_overrides' not in st.session_state:
        st.session_state.master_overrides = {p: {'S': 0, 'N': 0, 'DIFF': 0} for p in players}

    player_stats = []
    for i, p in enumerate(players):
        sp = s = n = diff = streak_val = 0
        for m in matches:
            t1, t2 = m['t1_score'], m['t2_score']
            wt = m.get('winner_team')
            
            if t1 is not None and t2 is not None:
                if wt == 1:
                    if i in [m['t1_p1'], m['t1_p2']]: sp += 1; s += 1; diff += (t1 - t2); streak_val = streak_val + 1 if streak_val > 0 else 1
                    elif i in [m['t2_p1'], m['t2_p2']]: sp += 1; n += 1; diff += (t2 - t1); streak_val = streak_val - 1 if streak_val < 0 else -1
                elif wt == 2:
                    if i in [m['t1_p1'], m['t1_p2']]: sp += 1; n += 1; diff += (t1 - t2); streak_val = streak_val - 1 if streak_val < 0 else -1
                    elif i in [m['t2_p1'], m['t2_p2']]: sp += 1; s += 1; diff += (t2 - t1); streak_val = streak_val + 1 if streak_val > 0 else 1
                else:
                    if i in [m['t1_p1'], m['t1_p2']]:
                        sp += 1
                        if t1 > t2: s += 1; diff += (t1 - t2); streak_val = streak_val + 1 if streak_val > 0 else 1
                        else: n += 1; diff += (t1 - t2); streak_val = streak_val - 1 if streak_val < 0 else -1
                    elif i in [m['t2_p1'], m['t2_p2']]:
                        sp += 1
                        if t2 > t1: s += 1; diff += (t2 - t1); streak_val = streak_val + 1 if streak_val > 0 else 1
                        else: n += 1; diff += (t2 - t1); streak_val = streak_val - 1 if streak_val < 0 else -1

        # MASTER MODUS: Overrides einrechnen
        mo = st.session_state.master_overrides.get(p, {'S': 0, 'N': 0, 'DIFF': 0})
        s += mo['S']
        n += mo['N']
        diff += mo['DIFF']

        score = s * 10000 + diff
        s_pct = f"{int((s/sp)*100)}%" if sp > 0 else "0%"
        st_txt = f"{streak_val}S" if streak_val > 0 else f"{abs(streak_val)}N" if streak_val < 0 else "-"
        st_emj = "🔥" if streak_val >= 3 else "💀" if streak_val <= -3 else ""
        
        player_stats.append({
            'id': i, 'NAME': p, 'SP': sp, 'S': s, 'N': n, 'DIFF': diff,
            'S%': s_pct, 'SERIE': st_txt, ' ': st_emj, 'Rest': 12 - sp, 'Score': score
        })

    is_finished = sum(1 for m in matches if m['t1_score'] is not None) == 15
    max_score = max(ps['Score'] for ps in player_stats) if player_stats else 0

    for ps in player_stats:
        max_pot = ps['Score'] + ps['Rest'] * 10010
        min_opp_scores = []
        for opp in player_stats:
            if ps['id'] == opp['id']: continue
            open_t = 0
            for m in matches:
                if m['t1_score'] is None:
                    in_t1 = (ps['id'] in [m['t1_p1'], m['t1_p2']]) and (opp['id'] in [m['t1_p1'], m['t1_p2']])
                    in_t2 = (ps['id'] in [m['t2_p1'], m['t2_p2']]) and (opp['id'] in [m['t2_p1'], m['t2_p2']])
                    if in_t1 or in_t2: open_t += 1
            min_opp_scores.append(opp['Score'] + (open_t * 10020) - (opp['Rest'] * 10))

        if is_finished: ps['STATUS'] = "👑 MEISTER" if ps['Score'] == max_score else "Eliminated"
        else: ps['STATUS'] = "Titel drin" if max_pot >= (max(min_opp_scores) if min_opp_scores else 0) else "Eliminated"

    if not is_finished and sum(1 for ps in player_stats if ps['STATUS'] == "Titel drin") == 1:
        for ps in player_stats:
            if ps['STATUS'] == "Titel drin": ps['STATUS'] = "👑 MEISTER"

    df_table = pd.DataFrame(player_stats).sort_values(by=['Score'], ascending=False).reset_index(drop=True)
    df_table.index += 1
    df_table.insert(0, 'RANG', df_table.index.map(lambda x: ["1 🏆", "2 🥈", "3 🥉", "4", "5"][x-1] if x<=5 else str(x)))
    return df_table

def render_tabelle_und_spielplan():
    st.subheader("Die Meister-Tabelle")
    players = st.session_state.players
    matches = st.session_state.matches
    
    df_table = build_tabelle_data(players, matches)
    st.dataframe(df_table[['RANG', 'NAME', 'SP', 'S', 'N', 'DIFF', 'S%', 'SERIE', ' ', 'STATUS']].style.map(style_df), hide_index=True, use_container_width=True)

    st.divider()
    st.subheader("📅 Spielplan")
    
    for m in matches:
        p1, p2 = players[m['t1_p1']], players[m['t1_p2']]
        p3, p4 = players[m['t2_p1']], players[m['t2_p2']]
        
        if m['t1_score'] is not None:
            wt = m.get('winner_team')
            if wt == 1: t1_c, t2_c = "#198754", "#dc3545"
            elif wt == 2: t1_c, t2_c = "#dc3545", "#198754"
            else:
                if m['t1_score'] > m['t2_score']: t1_c, t2_c = "#198754", "#dc3545"
                elif m['t2_score'] > m['t1_score']: t1_c, t2_c = "#dc3545", "#198754"
                else: t1_c, t2_c = "inherit", "inherit"
            
            st.markdown(f"<div style='padding:10px; background-color:#f8f9fa; border-radius:5px; margin-bottom:5px; text-align:center; font-size:16px;'>"
                        f"<b>Spiel {m['id']+1}:</b> &nbsp;&nbsp;&nbsp; <span style='color:{t1_c}; font-weight:bold;'>{p1} & {p2}</span> "
                        f"&nbsp;&nbsp;&nbsp;<b>{m['t1_score']} : {m['t2_score']}</b>&nbsp;&nbsp;&nbsp; "
                        f"<span style='color:{t2_c}; font-weight:bold;'>{p3} & {p4}</span></div>", 
                        unsafe_allow_html=True)
            
            with st.expander("📄 Spielbericht anzeigen"):
                # ANZEIGEN-ERWEITERUNG: Vollstrecker ganz oben einfügen!
                v_id = m.get('last_scorer')
                v_name = players[v_id] if v_id is not None else "Keiner (z.B. Fehler-Punkt)"
                st.markdown(f"🗡️ **Vollstrecker (Siegtreffer):** `{v_name}`")
                st.write("")

                if m.get('stats'):
                    st.markdown("**🎯 Wurfquoten & Treffer aus diesem Spiel:**")
                    stats = m['stats']
                    i_p1, i_p2, i_p3, i_p4 = m['t1_p1'], m['t1_p2'], m['t2_p1'], m['t2_p2']
                    
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
                    
                    st.write(f"🟢 **Team 1:** {t1_s[0][0]} ({t1_s[0][1]} Treffer / {t1_s[0][2]} Würfe | {t1_s[0][3]:.2f}%) &nbsp;|&nbsp; {t1_s[1][0]} ({t1_s[1][1]} Treffer / {t1_s[1][2]} Würfe | {t1_s[1][3]:.2f}%)")
                    st.write(f"🔵 **Team 2:** {t2_s[0][0]} ({t2_s[0][1]} Treffer / {t2_s[0][2]} Würfe | {t2_s[0][3]:.2f}%) &nbsp;|&nbsp; {t2_s[1][0]} ({t2_s[1][1]} Treffer / {t2_s[1][2]} Würfe | {t2_s[1][3]:.2f}%)")
                    st.divider()

                if m.get('action_log'):
                    for entry in m['action_log']: st.caption(entry)
                else: st.caption("Kein Log vorhanden")
        elif st.session_state.live and st.session_state.live['match_id'] == m['id']:
            st.warning(f"🔴 LÄUFT GERADE: Spiel {m['id']+1} | {p1} & {p2} VS {p3} & {p4}")
        else:
            st.write(f"⚪ Spiel {m['id']+1} | {p1} & {p2} VS {p3} & {p4}")

    # ANZEIGEN-ERWEITERUNG: Matrix der verbleibenden Team-Paarungen
    st.divider()
    st.subheader("🧩 Matrix der verbleibenden Paarungen")
    st.write("Wie viele offene Spiele hat jeder Spieler noch mit welchem Partner?")
    matrix_data = {p: {p2: 0 for p2 in players} for p in players}
    for m in matches:
        if m['t1_score'] is None:
            pl1, pl2 = players[m['t1_p1']], players[m['t1_p2']]
            pl3, pl4 = players[m['t2_p1']], players[m['t2_p2']]
            matrix_data[pl1][pl2] += 1; matrix_data[pl2][pl1] += 1
            matrix_data[pl3][pl4] += 1; matrix_data[pl4][pl3] += 1
    df_matrix = pd.DataFrame(matrix_data)
    st.dataframe(df_matrix, use_container_width=True)

def render_statistiken():
    st.subheader("📊 Einzel- & Event-Statistiken")
    players = st.session_state.players
    matches = st.session_state.matches
    
    # MASTER-MODUS ERWEITERUNG: Korrekturfläche für Fehlerbehebung
    if 'stat_overrides' not in st.session_state:
        st.session_state.stat_overrides = {p: {'H': 0, 'T': 0, 'GW': 0, 'B': 0, 'C': 0, 'F': 0} for p in players}
        
    master_on = st.checkbox("🔓 Master-Modus: Manuelle Statistik-Korrekturen freischalten")
    if master_on:
        st.info("Hier kannst du Tippfehler durch direktes Addieren/Subtrahieren (+1 / -1) blitzschnell korrigieren.")
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1: target_p = st.selectbox("Spieler wählen:", options=players)
        with col_m2: target_stat = st.selectbox("Wert wählen:", options=["Treffer", "Würfe", "Vollstrecker", "Bomben", "Nachwurf-Retter", "Fehler"])
        with col_m3:
            st.write("Aktion:")
            c_a1, c_a2 = st.columns(2)
            stat_map = {"Treffer": "H", "Würfe": "T", "Vollstrecker": "GW", "Bomben": "B", "Nachwurf-Retter": "C", "Fehler": "F"}
            key = stat_map[target_stat]
            if c_a1.button("➕ +1", key="btn_p1"): st.session_state.stat_overrides[target_p][key] += 1; st.rerun()
            if c_a2.button("➖ -1", key="btn_m1"): st.session_state.stat_overrides[target_p][key] -= 1; st.rerun()

    ind_stats = []
    for i, p in enumerate(players):
        hits = throws = gw = fehler = bombs = clutch = 0
        for m in matches:
            if m['t1_score'] is not None and m['stats'] is not None:
                hits += m['stats'].get(f'p{i}_h', 0)
                throws += m['stats'].get(f'p{i}_t', 0)
                fehler += m['stats'].get(f'p{i}_f', 0)
                if m.get('last_scorer') == i: gw += 1
                bombs += sum(1 for b in m.get('bombs_events', []) if b == i)
                clutch += sum(1 for c in m.get('clutch_nachwurf_events', []) if c == i)
        
        # Manuelle Korrekturen einrechnen
        so = st.session_state.stat_overrides.get(p, {'H': 0, 'T': 0, 'GW': 0, 'B': 0, 'C': 0, 'F': 0})
        hits += so['H']
        throws += so['T']
        gw += so['GW']
        bombs += so['B']
        clutch += so['C']
        fehler += so['F']

        quote = (hits / throws * 100) if throws > 0 else 0.0
        ind_stats.append({
            'NAME': p, 'TREFFER': hits, 'WÜRFE': throws, 'QUOTE_VAL': quote, 'QUOTE': f"{quote:.2f} %", 
            'SIEGTREFFER': gw, 'DREIFACHBECHER-TREFFER': bombs, 'NACHWURF RETTER': clutch, 'FEHLER': fehler
        })
    
    df_ind = pd.DataFrame(ind_stats)
    
    c_s1, c_s2 = st.columns(2)
    with c_s1:
        st.write("**🎯 Trefferquoten**")
        df_quote = df_ind.sort_values(by=['QUOTE_VAL', 'TREFFER'], ascending=[False, False]).reset_index(drop=True)
        df_quote.index += 1; df_quote.insert(0, 'RANG', df_quote.index)
        st.dataframe(df_quote[['RANG', 'NAME', 'TREFFER', 'WÜRFE', 'QUOTE']], hide_index=True, use_container_width=True)

    with c_s2:
        st.write("**🔪 Vollstrecker (Game Winners)**")
        df_gw = df_ind[df_ind['SIEGTREFFER'] > 0].sort_values(by='SIEGTREFFER', ascending=False).reset_index(drop=True)
        if not df_gw.empty:
            df_gw.index += 1; df_gw.insert(0, 'RANG', df_gw.index)
            st.dataframe(df_gw[['RANG', 'NAME', 'SIEGTREFFER']], hide_index=True, use_container_width=True)
        else: st.caption("Noch kein Ereignis.")

    st.write("---")
    col_e1, col_e2, col_e3 = st.columns(3)
    with col_e1:
        st.write("**💣 Dreifachbecher-Treffer**")
        df_bomb = df_ind[df_ind['DREIFACHBECHER-TREFFER'] > 0].sort_values(by='DREIFACHBECHER-TREFFER', ascending=False).reset_index(drop=True)
        if not df_bomb.empty:
            df_bomb.index += 1; df_bomb.insert(0, 'RANG', df_bomb.index)
            st.dataframe(df_bomb[['RANG', 'NAME', 'DREIFACHBECHER-TREFFER']], hide_index=True, use_container_width=True)
        else: st.caption("Noch kein Ereignis.")
            
    with col_e2:
        st.write("**🚑 Nachwurf Retter**")
        df_clutch = df_ind[df_ind['NACHWURF RETTER'] > 0].sort_values(by='NACHWURF RETTER', ascending=False).reset_index(drop=True)
        if not df_clutch.empty:
            df_clutch.index += 1; df_clutch.insert(0, 'RANG', df_clutch.index)
            st.dataframe(df_clutch[['RANG', 'NAME', 'NACHWURF RETTER']], hide_index=True, use_container_width=True)
        else: st.caption("Noch kein Ereignis.")
            
    with col_e3:
        st.write("**🤡 Dummkopf (Fehler)**")
        df_dk = df_ind[df_ind['FEHLER'] > 0].sort_values(by='FEHLER', ascending=False).reset_index(drop=True)
        if not df_dk.empty:
            df_dk.index += 1; df_dk.insert(0, 'RANG', df_dk.index)
            st.dataframe(df_dk[['RANG', 'NAME', 'FEHLER']], hide_index=True, use_container_width=True)
        else: st.caption("Noch kein Fehler begangen.")

    st.divider()
    
    match_data = []
    match_export = []
    for m in matches:
        p1, p2 = players[m['t1_p1']], players[m['t1_p2']]
        p3, p4 = players[m['t2_p1']], players[m['t2_p2']]
        if m['t1_score'] is not None:
            diff = abs(m['t1_score'] - m['t2_score'])
            turns = m.get('winner_turns', 0)
            txt = f"Spiel {m['id']+1}: {p1} & {p2} vs {p3} & {p4}"
            res = f"{m['t1_score']} : {m['t2_score']}"
            match_data.append({'SPIEL': txt, 'ERGEBNIS': res, 'DIFF': diff, 'ZÜGE (SIEGER)': turns})
            match_export.append({'Spiel': f"Spiel {m['id']+1}", 'Team 1': f"{p1} & {p2}", 'Team 2': f"{p3} & {p4}", 'Ergebnis': res})
        else:
            if st.session_state.live and st.session_state.live['match_id'] == m['id']:
                match_export.append({'Spiel': f"Spiel {m['id']+1}", 'Team 1': f"{p1} & {p2}", 'Team 2': f"{p3} & {p4}", 'Ergebnis': "LÄUFT GERADE"})
            else:
                match_export.append({'Spiel': f"Spiel {m['id']+1}", 'Team 1': f"{p1} & {p2}", 'Team 2': f"{p3} & {p4}", 'Ergebnis': "- : -"})
    
    df_matches = pd.DataFrame(match_export)
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.write("**🏆 Höchster Sieg (Top 3)**")
        if match_data:
            df_hs = pd.DataFrame(match_data).sort_values(by=['DIFF', 'ZÜGE (SIEGER)'], ascending=[False, True]).head(3).reset_index(drop=True)
            df_hs.index += 1; df_hs.insert(0, 'RANG', df_hs.index)
            st.dataframe(df_hs[['RANG', 'SPIEL', 'ERGEBNIS', 'DIFF', 'ZÜGE (SIEGER)']], hide_index=True, use_container_width=True)
        else: st.caption("Noch keine Spiele absolviert.")

    with col_m2:
        st.write("**⚡ Schnellste Siege (Blitzkrieg - Top 3)**")
        if match_data:
            df_bk = pd.DataFrame(match_data).sort_values(by='ZÜGE (SIEGER)', ascending=True).head(3).reset_index(drop=True)
            df_bk.index += 1; df_bk.insert(0, 'RANG', df_bk.index)
            st.dataframe(df_bk[['RANG', 'SPIEL', 'ZÜGE (SIEGER)', 'ERGEBNIS']], hide_index=True, use_container_width=True)
        else: st.caption("Noch keine Spiele absolviert.")

    st.write("---")
    st.subheader("💾 Turnier Archivieren")
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_table[['RANG', 'NAME', 'SP', 'S', 'N', 'DIFF', 'S%', 'SERIE', 'STATUS']].to_excel(writer, sheet_name="Tabelle", index=False)
        df_matches.to_excel(writer, sheet_name="Spielplan", index=False)
        df_quote[['RANG', 'NAME', 'TREFFER', 'WÜRFE', 'QUOTE']].to_excel(writer, sheet_name="Trefferquoten", index=False)
        if not df_gw.empty: df_gw[['RANG', 'NAME', 'SIEGTREFFER']].to_excel(writer, sheet_name="Vollstrecker", index=False)
        
    st.download_button(
        label="📥 Gesamtes Turnier als Excel speichern",
        data=buffer.getvalue(),
        file_name=f"Bierpong_Turnier_{st.session_state.t_date}.xlsx",
        mime="application/vnd.ms-excel",
        type="primary"
    )
