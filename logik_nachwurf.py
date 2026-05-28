import streamlit as st

def trigger_nachwurf(team_hitting, amount, misses=[]):
    """
    Bestimmt die exakte Finish-Qualität von Team Anfang und leitet
    den entsprechenden Nachwurf (1 oder 2 Würfe) für Team Nachwurf ein.
    """
    live = st.session_state.live
    names = st.session_state.players
    m = st.session_state.matches[live['match_id']]
    
    opponent = 2 if team_hitting == 1 else 1
    
    # Nur triggern, wenn Team Anfang (Starter) gerade das Spiel auf 0 Becher gebracht hat
    if team_hitting == live['starter']:
        if (team_hitting == 1 and live['t2_cups'] == 0) or (team_hitting == 2 and live['t1_cups'] == 0):
            
            # Wir setzen den Nachwurf nur, wenn er noch nicht initialisiert wurde
            if 'anfang_finish_quality' not in live:
                
                # Hierarchie der Stärke: 3.0 (Bombe) > 2.0 (Doppel) > 1.5 (1. Wurf) > 1.0 (2. Wurf)
                q = 1.0  
                if amount == 3: q = 3.0
                elif amount == 2: q = 2.0
                elif amount == 1: 
                    # Wenn misses leer ist, wurde im allerersten Wurf getroffen!
                    q = 1.5 if len(misses) == 0 else 1.0
                
                live['anfang_finish_quality'] = q
                live['anfang_last_scorer'] = live.get('t1_last_scorer' if team_hitting == 1 else 't2_last_scorer')
                
                # Wenn es ein hocheffizienter Einzelwurf war (1.5), gibt es nur 1 Nachwurf
                if q == 1.5:
                    live['single_nachwurf_team'] = opponent
                else:
                    live['nachwurf'] = opponent
                    
                # Ball geht für den Nachwurf zwingend an den Gegner
                live['possession'] = opponent
                live['action_log'].append(f"🚨 NACHWURF für {names[m[f't{opponent}_p1']]} & {names[m[f't{opponent}_p2']]}!")

def check_game_over():
    """
    Das Herzstück. Vergleicht bei 0 Bechern die Qualität des Finishs
    und beendet das Spiel sofort, falls der Nachwurf mathematisch gescheitert ist.
    """
    live = st.session_state.live
    if live is None: return
    
    c1 = live['t1_cups']
    c2 = live['t2_cups']
    starter = live['starter']
    possession = live['possession']
    
    # 1. Quartett der Finish-Stärken (Beide Teams haben 0 Becher)
    if c1 == 0 and c2 == 0:
        q_anfang = live.get('anfang_finish_quality', 1.0)
        q_nachwurf = live.get('nachwurf_finish_quality', 1.0)
        
        if q_nachwurf > q_anfang:
            # Nachwurf-Team kontert mit stärkerem Finish -> Sieg Nachwurf-Team!
            live['game_state'] = 't2_won' if starter == 1 else 't1_won'
        elif q_nachwurf == q_anfang:
            # Rettung geglückt! Verlängerung aktiv.
            live['game_state'] = 'nachwurf_erfolgreich'
        else:
            # Schwächeres Finish -> Sieg Team Anfang.
            live['game_state'] = 't1_won' if starter == 1 else 't2_won'
            live['last_scorer'] = live.get('anfang_last_scorer')
        return
        
    # 2. Team 1 hat auf 0 gestellt (Team 2 hat 0 Becher, Team 1 hat noch Becher)
    if c2 == 0 and c1 > 0:
        if starter == 1:
            # Warten auf Nachwurf von Team 2. Endet bei Ballverlust ohne Rettung.
            nw_active = live.get('nachwurf') == 2 or live.get('single_nachwurf_team') == 2
            if not nw_active and possession == 1:
                live['game_state'] = 't1_won'
                live['last_scorer'] = live.get('anfang_last_scorer', live.get('t1_last_scorer'))
        elif starter == 2:
            # Team 2 startete, Team 1 hat nun abgeräumt -> Team 1 gewinnt sofort!
            live['game_state'] = 't1_won'
        return
        
    # 3. Team 2 hat auf 0 gestellt (Team 1 hat 0 Becher, Team 2 hat noch Becher)
    if c1 == 0 and c2 > 0:
        if starter == 2:
            # Warten auf Nachwurf von Team 1. Endet bei Ballverlust ohne Rettung.
            nw_active = live.get('nachwurf') == 1 or live.get('single_nachwurf_team') == 1
            if not nw_active and possession == 2:
                live['game_state'] = 't2_won'
                live['last_scorer'] = live.get('anfang_last_scorer', live.get('t2_last_scorer'))
        elif starter == 1:
            # Team 1 startete, Team 2 hat nun abgeräumt -> Team 2 gewinnt sofort!
            live['game_state'] = 't2_won'
        return
