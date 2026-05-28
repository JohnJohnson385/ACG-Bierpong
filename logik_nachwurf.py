import streamlit as st

def trigger_nachwurf(team_hitting, amount):
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
            if live.get('nachwurf') is None and live.get('single_nachwurf_team') is None:
                
                # Ermittle die exakte Qualität des Finishs von Team Anfang
                is_single_throw = (live.get('single_nachwurf_team') == opponent) or (live.get('pending_last_cup', False))
                
                q = 1.2  # Standard: Einzeltreffer im 2. Wurf
                if amount == 3: q = 3.0   # Dreifachtreffer (Bombe)
                elif amount == 2: q = 2.0 # Doppeltreffer
                elif amount == 1: q = 1.1 if is_single_throw else 1.2 # Einzeltreffer 1. vs 2. Wurf
                
                # Merke dir das Finish und den Torschützen von Team Anfang
                live['anfang_finish_quality'] = q
                live['anfang_last_scorer'] = live.get('t1_last_scorer' if team_hitting == 1 else 't2_last_scorer')
                
                # Nachwurf-Modus basierend auf der Effizienz setzen
                if q == 1.1:
                    live['single_nachwurf_team'] = opponent
                    live['possession'] = opponent
                else:
                    live['nachwurf'] = opponent
                    live['possession'] = opponent
                    
                live['action_log'].append(f"🚨 NACHWURF eingeleitet! Team Anfang hat vorgelegt mit Qualität: {q}")

def check_game_over():
    """
    Das Herzstück eurer Regeln. Vergleicht bei 0 Bechern die Qualität des Finishs
    und beendet das Spiel sofort, falls der Nachwurf mathematisch gescheitert ist.
    """
    live = st.session_state.live
    if live is None: return
    
    anfang_team = live['starter']
    nachwurf_team = 2 if anfang_team == 1 else 1
    
    anfang_cups = live['t1_cups'] if anfang_team == 1 else live['t2_cups']
    nachwurf_cups = live['t2_cups'] if anfang_team == 1 else live['t1_cups']
    
    # REGEL 1: Team Nachwurf beendet das Spiel zuerst -> Sofortiger Sieg für Team Nachwurf
    if nachwurf_cups == 0 and anfang_cups > 0:
        live['game_state'] = 't2_won' if nachwurf_team == 2 else 't1_won'
        return
        
    # REGEL 2: Team Anfang hat auf 0 gestellt, Nachwurf läuft.
    # Wenn der Ballbesitz wieder an Team Anfang zurückgeht, ist der Nachwurf-Zug vorbei.
    if anfang_cups == 0 and nachwurf_cups > 0:
        if live['possession'] == anfang_team:
            # Nachwurf gescheitert (Becher übrig)! Sieg für Team Anfang.
            live['game_state'] = 't1_won' if anfang_team == 1 else 't2_won'
            # Der Vollstrecker-Punkt geht sicher an den Schützen von Team Anfang!
            live['last_scorer'] = live.get('anfang_last_scorer')
            return
            
    # REGEL 3: Das "Quartett" der Finish-Stärken (Beide Teams haben 0 Becher erreicht)
    if anfang_cups == 0 and nachwurf_cups == 0:
        q_anfang = live.get('anfang_finish_quality', 1.2)
        q_nachwurf = live.get('nachwurf_finish_quality', 1.2)
        
        if q_nachwurf > q_anfang:
            # Höhere Qualität -> Team Nachwurf gewinnt das Spiel sofort im Nachzug! (z.B. Dreifach schlägt Doppel)
            live['game_state'] = 't2_won' if nachwurf_team == 2 else 't1_won'
        elif q_nachwurf == q_anfang:
            # Exakt gleiche Qualität -> Rettung geglückt! (Zurücksetzen-Button wird aktiv)
            live['game_state'] = 'nachwurf_erfolgreich'
        else:
            # Geringere Qualität -> Trotz 0 Becher verloren! (z.B. Doppel verliert gegen Dreifach)
            live['game_state'] = 't1_won' if anfang_team == 1 else 't2_won'
            live['last_scorer'] = live.get('anfang_last_scorer')
