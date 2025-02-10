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

        # Converti le colonne numeriche correggendo eventuali errori
        numeric_columns = ["Quotazione", "Fantamedia", "Media_Voto", "Partite_Voto"]
        
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")  # Converte i valori non numerici in NaN
        
        # Riempie solo i valori NaN con la media delle quotazioni esistenti
        df["Quotazione"].fillna(df["Quotazione"].mean(), inplace=True)
        
        # 🔴 NUOVA SOLUZIONE: FORZA la colonna "Ruolo" in stringa e riempie eventuali NaN 🔴
        df["Ruolo"] = df["Ruolo"].astype(str)  # Forza tutto a stringa
        df["Ruolo"].replace({"nan": "Sconosciuto", "None": "Sconosciuto"}, inplace=True)  # Sostituisce stringhe NaN
        df["Ruolo"].fillna("Sconosciuto", inplace=True)  # Riempi con valore di default

        return df.to_dict(orient='records')
    
    except Exception as e:
        st.error(f"Errore nel caricamento del database: {e}")
        return None
