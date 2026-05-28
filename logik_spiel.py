import streamlit as st
import copy
import datenbank
import logik_nachwurf

def save_step():
    l = st.session_state.live
    l['history'].append(copy.deepcopy({
        't1_cups': l['t1_cups'], 't2_cups': l['t2_cups'],
        'nachwurf': l['nachwurf'], 'possession': l['possession'],
        'balls_back': l['balls_back'], 'pending_bomb': l.get('pending_bomb', False),
        'pending_double_win': l.get('pending_double_win', False),
        'pending_last_cup': l.get('pending_last_cup', False),
        'pending_penalty': l.get('pending_penalty', None),
        'single_nachwurf_team': l.get('single_nachwurf_team', None),
        'single_nachwurf_shooter': l.get('single_nachwurf_shooter', None),
        'last_cup_hitter': l.get('last_cup_hitter', None),
        't1_last_scorer': l.get('t1_last_scorer', None),
        't2_last_scorer': l.get('t2_last_scorer', None),
        'game_state': l.get('game_state', 'playing'),
        'cups_at_turn_start': l.get('cups_at_turn_start'),
        'stats': l['stats'], 'action_log': l['action_log'],
        'bombs_events': l['bombs_events'], 'clutch_nachwurf_events': l['clutch_nachwurf_events']
    }))

def log_action(text):
    st.session_state.live['action_log'].append(text)

def change_possession(new_poss):
    live = st.session_state.live
    if live['t1_cups'] > 0 and live['t2_cups'] > 0:
        live['cups_at_turn_start'] = {'t1_cups': live['t1_cups'], 't2_cups': live['t2_cups']}
    live['possession'] = new_poss
    if new_poss == 1: live['stats']['turns_t1'] += 1
    else: live['stats']['turns_t2'] += 1

def do_hit(team_hitting, amount, hits=[], misses=[], bombe_thrower=None, is_balls_back=False, is_clutch_nachwurf=False):
    save_step()
    live = st.session_state.live
    names = st.session_state.players
    m = st.session_state.matches[live['match_id']]
    
    live['balls_back'] = is_balls_back
    t_name = f"{names[m['t1_p1']]} & {names[m['t1_p2']]}" if team_hitting == 1 else f"{names[m['t2_p1']]} & {names[m['t2_p2']]}"
    turn = live['stats'][f'turns_t{team_hitting}']
    
    scorer = bombe_thrower if bombe_thrower is not None else (hits[-1] if hits else None)
    if scorer is not None:
        if team_hitting == 1: live['t1_last_scorer'] = scorer
        else: live['t2_last_scorer'] = scorer
        
    if team_hitting == 1: live['t2_cups'] = max(0, live['t2_cups'] - amount)
    else: live['t1_cups'] = max(0, live['t1_cups'] - amount)
    
    s_txt = f"(Stand: {live['t1_cups']}:{live['t2_cups']})"
    if amount == 1: log_action(f"[{t_name} | Zug {turn}] 🎯 Einzeltreffer von {names[hits[0]]} {s_txt}")
    elif amount == 2: log_action(f"[{t_name} | Zug {turn}] ✌️ Doppeltreffer von {names[hits[0]]} & {names[hits[1]]} {s_txt}")
    elif amount == 3: 
        log_action(f"[{t_name} | Zug {turn}] 💣 Dreifachtreffer! Zweiter Ball von {names[bombe_thrower]} {s_txt}")
        live['bombs_events'].append(bombe_thrower)

    if is_clutch_nachwurf and ((team_hitting == 1 and live['t2_cups'] == 0) or (team_hitting == 2 and live['t1_cups'] == 0)):
        live['clutch_nachwurf_events'].append(scorer)
    
    for p in hits: live['stats'][f'p{p}_h'] += 1; live['stats'][f'p{p}_t'] += 1
    for p in misses: live['stats'][f'p{p}_t'] += 1
        
    if not is_balls_back: 
        change_possession(2 if team_hitting == 1 else 1)
        if live.get('nachwurf') == team_hitting: live['nachwurf'] = None
        if live.get('single_nachwurf_team') == team_hitting: live['single_nachwurf_team'] = None
        
    logik_nachwurf.trigger_nachwurf(team_hitting, is_balls_back)
    logik_nachwurf.check_game_over()
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
        
    if live.get('nachwurf') == team: live['nachwurf'] = None
    logik_nachwurf.check_game_over()
    datenbank.sync_to_cloud()

def do_miss_single(team, shooter_idx):
    save_step()
    live = st.session_state.live
    live['balls_back'] = False
    names = st.session_state.players
    turn = live['stats'][f'turns_t{team}']
    
    s_txt = f"(Stand: {live['t1_cups']}:{live['t2_cups']})"
    log_action(f"[Team {team} | Zug {turn}] 🚫 Nachwurf verfehlt von {names[shooter_idx]} {s_txt}")
    live['stats'][f"p{shooter_idx}_t"] += 1
    
    live['single_nachwurf_team'] = None 
    change_possession(2 if team == 1 else 1)
    logik_nachwurf.check_game_over()
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
    logik_nachwurf.check_game_over()
    datenbank.sync_to_cloud()
