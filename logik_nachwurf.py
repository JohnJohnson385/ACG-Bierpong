import streamlit as st

def check_game_over():
    """Die isolierte Nachwurf-Regel: Prüft, wer gewinnt oder ob Nachwurf/Overtime startet."""
    l = st.session_state.live
    
    # 1. OVERTIME (Beide Teams auf 0)
    if l['t1_cups'] == 0 and l['t2_cups'] == 0: 
        l['game_state'] = 'nachwurf_erfolgreich'
        return

    # 2. TEAM 1 GEWINNT (Sie haben T2 auf 0 gebracht)
    if l['t2_cups'] == 0 and l['t1_cups'] > 0:
        if l['starter'] == 2: 
            # Team 2 startete. Team 1 hat Nachwurf und trifft auf 0 -> Sieg Team 1!
            l['game_state'] = 't1_won'
        elif l['starter'] == 1:
            # Team 1 startete. Warten auf Nachwurf von Team 2.
            if l['nachwurf'] is None and l.get('single_nachwurf_team') != 2: 
                l['game_state'] = 't1_won'

    # 3. TEAM 2 GEWINNT (Sie haben T1 auf 0 gebracht)
    elif l['t1_cups'] == 0 and l['t2_cups'] > 0:
        if l['starter'] == 1: 
            # Team 1 startete. Team 2 hat Nachwurf und trifft auf 0 -> Sieg Team 2!
            l['game_state'] = 't2_won'
        elif l['starter'] == 2:
            # Team 2 startete. Warten auf Nachwurf von Team 1.
            if l['nachwurf'] is None and l.get('single_nachwurf_team') != 1: 
                l['game_state'] = 't2_won'

def trigger_nachwurf(team_hitting, is_balls_back):
    """Prüft, ob der Gegner auf 0 ist und löst den passenden Nachwurf aus."""
    live = st.session_state.live
    names = st.session_state.players
    m = st.session_state.matches[live['match_id']]
    
    # Nachwurf für Team 2?
    if live['t2_cups'] == 0 and live['starter'] == 1 and live['nachwurf'] is None and live.get('single_nachwurf_team') != 2:
        live['nachwurf'] = 2
        if is_balls_back: 
            live['possession'] = 2
            live['stats']['turns_t2'] += 1
        live['action_log'].append(f"🚨 NACHWURF für {names[m['t2_p1']]} & {names[m['t2_p2']]}!")
        
    # Nachwurf für Team 1?
    elif live['t1_cups'] == 0 and live['starter'] == 2 and live['nachwurf'] is None and live.get('single_nachwurf_team') != 1:
        live['nachwurf'] = 1
        if is_balls_back: 
            live['possession'] = 1
            live['stats']['turns_t1'] += 1
        live['action_log'].append(f"🚨 NACHWURF für {names[m['t1_p1']]} & {names[m['t1_p2']]}!")
