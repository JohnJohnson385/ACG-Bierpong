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
    player_stats = []
    for i, p in enumerate(players):
        sp = s = n = diff = streak_val = 0
        for m in matches:
            t1, t2 = m['t1_score'], m['t2_score']
            wt = m.get('winner_team') # Neues, exaktes Gewinner-Feld!
            
            if t1 is not None and t2 is not None:
                # WENN WIR WISSEN, WER GEWONNEN HAT (auch bei 0:0 wichtig!):
                if wt == 1:
                    if i in [m['t1_p1'], m['t1_p2']]:
                        sp += 1; s += 1; diff += (t1 - t2); streak_val = streak_val + 1 if streak_val > 0 else 1
                    elif i in [m['t2_p1'], m['t2_p2']]:
                        sp += 1; n += 1; diff += (t2 - t1); streak_val = streak_val - 1 if streak_val < 0 else -1
                elif wt == 2:
                    if i in [m['t1_p1'], m['t1_p2']]:
                        sp += 1; n += 1; diff += (t1 - t2); streak_val = streak_val - 1 if streak_val < 0 else -1
                    elif i in [m['t2_p1'], m['t2_p2']]:
                        sp += 1; s += 1; diff += (t2 - t1); streak_val = streak_val + 1 if streak_val > 0 else 1
                else: 
                    # Fallback für ganz alte Turniere
                    if i in [m['t1_p1'], m['t1_p2']]:
                        sp += 1
                        if t1 > t2: s += 1; diff += (t1 - t2); streak_val = streak_val + 1 if streak_val > 0 else 1
                        else: n += 1; diff += (t1 - t2); streak_val = streak_val - 1 if streak_val < 0 else -1
                    elif i in [m['t2_p1'], m['t2_p2']]:
                        sp += 1
                        if t2 > t1: s += 1; diff += (t2 - t1); streak_val = streak_val + 1 if streak_val > 0 else 1
                        else: n += 1; diff += (t2 - t1); streak_val = streak_val - 1 if streak_val < 0 else -1

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
