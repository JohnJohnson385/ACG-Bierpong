import streamlit as st
import copy
import datenbank

def save_step():
    l = st.session_state.live
    snapshot = {k: copy.deepcopy(v) for k, v in l.items() if k != 'history'}
    l['history'].append(snapshot)

def log_action(text):
    st.session_state.live['action_log'].append(text)

def change_possession(new_poss):
    live = st.session_state.live
    if live['t1_cups'] > 0 and live['t2_cups'] > 0:
        live['cups_at_turn_start'] = {'t1_cups': live['t1_cups'], 't2_cups': live['t2_cups']}
    live['possession'] = new_poss
    if new_poss == 1: live['stats']['turns_t1'] += 1
    else: live['stats']['turns_t2'] += 1

def do_hit(team_hitting, amount, hits=[], misses=[], bombe_thrower=None):
    save_step()
    live = st.session_state.live
    names = st.session_state.players
    m = st.session_state.matches[live['match_id']]
    
    is_balls_back = True if amount >= 2 else False
    live['balls_back'] = is_balls_back
    
    t_name = f"{names[m['t1_p1']]} & {names[m['t1_p2']]}" if team_hitting == 1 else f"{names[m['t2_p1']]} & {names[m['t2_p2']]}"
    turn = live['stats'][f'turns_t{team_hitting}']
    
    scorer = bombe_thrower if bombe_thrower is not None else (hits[-1] if hits else None)
        
    if team_hitting == 1: live['t2_cups'] = max(0, live['t2_cups'] - amount)
    else: live['t1_cups'] = max(0, live['t1_cups'] - amount)
    
    s_txt = f"(Stand: {live['t1_cups']}:{live['t2_cups']})"
    if amount == 1: log_action(f"[{t_name} | Zug {turn}] 🎯 Einzeltreffer von {names[hits[0]]} {s_txt}")
    elif amount == 2: log_action(f"[{t_name} | Zug {turn}] ✌️ Doppeltreffer von {names[hits[0]]} & {names[hits[1]]} {s_txt}")
    elif amount == 3: 
        log_action(f"[{t_name} | Zug {turn}] 💣 Dreifachtreffer! Zweiter Ball von {names[bombe_thrower]} {s_txt}")
        live['bombs_events'].append(bombe_thrower)
    
    for p in hits: live['stats'][f'p{p}_h'] += 1; live['stats'][f'p{p}_t'] += 1
    for p in misses: live['stats'][f'p{p}_t'] += 1
        
    if live['t1_cups'] == 0 or live['t2_cups'] == 0:
        # REGEL-FIX: Nur wenn der Starter auf 0 stellt, geht es in den Nachwurf
        if team_hitting == live['starter']:
            live['game_state'] = 'nachwurf_dialog'
            live['anfang_last_scorer'] = scorer
            live['anfang_team'] = team_hitting
        else:
            # Das Team, das NICHT angefangen hat, wirft auf 0 -> SOFORTIGER SIEG!
            live['game_state'] = 't1_won' if team_hitting == 1 else 't2_won'
            live['winner_team'] = team_hitting
            live['last_scorer'] = scorer
    else:
        if not is_balls_back: 
            change_possession(2 if team_hitting == 1 else 1)
            
    datenbank.sync_to_cloud()

def do_miss(team):
    save_step()
    live = st.session_state.live
    live['balls_back'] = False
    m = st.session_state.matches[live['match_id']]
    names = st.session_state.players
    t_name = f"{names[m['t1_p1']]} & {names[m['t1_p2']]}" if team == 1 else f"{names[m['t2_p1']]} & {names[m['t2_p2']]}"
    turn = live['stats'][f'turns_t{team}']
    
    s_txt = f"(Stand: {live['t1_cups']}:{live['t2_cups']})"
    log_action(f"[{t_name} | Zug {turn}] 🚫 Kein Treffer {s_txt}")
    
    if team == 1:
        live['stats'][f"p{m['t1_p1']}_t"] += 1; live['stats'][f"p{m['t1_p2']}_t"] += 1
        change_possession(2)
    else:
        live['stats'][f"p{m['t2_p1']}_t"] += 1; live['stats'][f"p{m['t2_p2']}_t"] += 1
        change_possession(1)
        
    datenbank.sync_to_cloud()

def do_penalty(team, culprit_idx):
    save_step()
    live = st.session_state.live
    names = st.session_state.players
    turn = live['stats'][f'turns_t{team}']
    
    if team == 1: live['t1_cups'] = max(0, live['t1_cups'] - 1)
    else: live['t2_cups'] = max(0, live['t2_cups'] - 1)
    
    s_txt = f"(Stand: {live['t1_cups']}:{live['t2_cups']})"
    log_action(f"[Team {team} | Zug {turn}] ⚠️ Fehler von {names[culprit_idx]} (-1 Becher) {s_txt}")
    
    live['stats'][f'p{culprit_idx}_f'] += 1
    live['pending_penalty'] = None
    
    if live['t1_cups'] == 0 or live['t2_cups'] == 0:
        winner_team = 2 if live['t1_cups'] == 0 else 1
        if winner_team != live['starter']:
            live['game_state'] = f't{winner_team}_won'
            live['winner_team'] = winner_team
            live['last_scorer'] = None
        else:
            live['game_state'] = 'nachwurf_dialog'
            live['anfang_last_scorer'] = None
            live['anfang_team'] = winner_team
            
    datenbank.sync_to_cloud()
