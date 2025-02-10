import streamlit as st
import pandas as pd
import random

# ... (funzioni load_database e export_to_csv invariate)

def normalize_quotations(database, budget):
    for player in database:
        original_quotazione = player['Quotazione']
        player['Quotazione'] = max(round(original_quotazione * (budget / 500), 2), 1)

# ... (funzione calculate_player_score invariata)

def generate_team(database, budget=500, strategy="Equilibrata"):
    # ... (codice precedente)

    for role in ROLES:
        # ... (codice precedente)

        # Aggiungi un elemento di casualità nella selezione
        for _ in range(count):
            eligible_players = [p for p in players if p['Quotazione'] <= remaining_budget]
            if not eligible_players:
                break

            scored_players = sorted(eligible_players, key=lambda x: (calculate_player_score(x), random.random()), reverse=True)
            if scored_players:  # Assicurati che ci siano giocatori con un punteggio
              selected_player = scored_players[0]
              selected.append(selected_player)
              remaining_budget -= selected_player['Quotazione']
              players.remove(selected_player)

        if len(selected) < count:
            st.warning(f"⚠️ Attenzione: non è stato possibile selezionare abbastanza giocatori per il ruolo {role}. Budget insufficiente o giocatori non disponibili.")
            st.write(f"Giocatori trovati: {len(selected)}, necessari: {count}")
            return None, None

        team.extend(selected)

    # ... (codice successivo)

# ... (codice interfaccia Streamlit invariato)