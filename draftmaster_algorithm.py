import streamlit as st
import pandas as pd
import os
import random
import io
import requests

# Carica il database Excel automaticamente
@st.cache_data
def load_database():
    url = "https://raw.githubusercontent.com/FantaElite/FantaElite/main/database_fantacalcio_v2.csv"
    try:
        df = pd.read_csv(url, encoding="utf-8", delimiter=';')

        # Rimuove eventuali spazi prima e dopo i nomi delle colonne
        df.columns = df.columns.str.strip()

        # Mappa i nuovi nomi delle colonne corretti
        column_mapping = {
            "Nome": "Nome",
            "Squadra": "Squadra",
            "Ruolo": "Ruolo",
            "Media_Voto": "Media_Voto",
            "Fantamedia": "Fantamedia",
            "Quotazione": "Quotazione",
            "Partite_Voto": "Partite_Voto"
        }

        df.rename(columns=column_mapping, inplace=True)

        # Controllo colonne mancanti
        expected_columns = list(column_mapping.values())
        missing_columns = [col for col in expected_columns if col not in df.columns]
        if missing_columns:
            st.error(f"Errore: Mancano le colonne {missing_columns} nel file CSV. Ecco le colonne trovate: {df.columns.tolist()}")
            return None

        # Converti le colonne al tipo stringa
        cols_da_convertire = ["Nome", "Squadra", "Ruolo"]
        for col in cols_da_convertire:
            if col in df.columns:  # Verifica se la colonna esiste
                df[col] = df[col].astype(str, errors='coerce')

        # Converte le colonne numeriche e gestisce le virgole
        numeric_cols = ["Quotazione", "Fantamedia", "Media_Voto", "Partite_Voto"]
        for col in numeric_cols:
            if col in df.columns: #Verifica se la colonna esiste
                df[col] = pd.to_numeric(df[col].str.replace(",", "."), errors="coerce")


        # Riempie i valori NaN in Quotazione con 0
        df["Quotazione"].fillna(0, inplace=True)

        # Se Fantamedia è presente ma Media Voto è NaN, assegna Media Voto = Fantamedia
        df.loc[df["Media_Voto"].isna() & df["Fantamedia"].notna(), "Media_Voto"] = df["Fantamedia"]

        # Validazione dei dati (esempio: controllo valori positivi per Quotazione)
        if "Quotazione" in df.columns and not df["Quotazione"].ge(0).all():
            st.error("Errore: La colonna 'Quotazione' contiene valori negativi.")
            return None

        return df.to_dict(orient='records')
    except FileNotFoundError:
        st.error(f"Errore: File non trovato all'URL specificato.")
        return None
    except pd.errors.ParserError:
        st.error("Errore: Errore nel parsing del file CSV. Controlla il formato.")
        return None
    except requests.exceptions.RequestException as e:  # Gestione errore di richiesta HTTP
        st.error(f"Errore nella richiesta del file CSV: {e}")
        return None
    except Exception as e:
        st.error(f"Errore generico nel caricamento del database: {e}")
        return None

def generate_team(database, budget=500, strategy="Equilibrata", max_attempts=10):
    # ... (resto del codice generate_team)

def sort_players(players, strategy, role):
    # ... (resto del codice sort_players)

def export_to_csv(team):
    # ... (resto del codice export_to_csv)

# ... (resto del codice Streamlit)