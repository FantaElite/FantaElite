import streamlit as st
import pandas as pd

# 🔴 Pulizia cache per evitare errori precedenti
st.cache_data.clear()

# 🔹 Funzione per caricare e pulire il database
@st.cache_data
def load_database():
    url = "https://raw.githubusercontent.com/FantaElite/FantaElite/main/database_fantacalcio_v2.csv"
    
    try:
        df = pd.read_csv(url, encoding="utf-8", delimiter=';')

        # 🔹 Rimuove spazi nei nomi delle colonne
        df.columns = df.columns.str.strip()

        # 🔹 Mostra anteprima del dataset originale
        st.write("📌 **Anteprima del Database Originale:**")
        st.dataframe(df.head())

        # 🔹 Mostra i tipi di dati originali
        st.write("🔍 **Tipi di Dati Originali:**")
        st.write(df.dtypes)

        # 🔹 Controlla valori NaN nella colonna "Ruolo"
        st.write("⚠️ **Valori NaN nella colonna Ruolo:**", df["Ruolo"].isna().sum())

        # 🔹 Rinomina le colonne
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

        # 🔹 Forza la colonna "Ruolo" a essere una stringa e riempie i NaN con "Sconosciuto"
        df["Ruolo"] = df["Ruolo"].astype(str)  # Converte tutto in stringa
        df["Ruolo"] = df["Ruolo"].fillna("Sconosciuto")  # Riempie eventuali NaN
        df["Ruolo"] = df["Ruolo"].str.strip()  # Rimuove spazi extra

        # 🔹 Converte i numeri e sostituisce le virgole con punti
        numeric_columns = ["Quotazione", "Fantamedia", "Media_Voto", "Partite_Voto"]
        for col in numeric_columns:
            df[col] = df[col].astype(str).str.replace(",", ".", regex=False)  # Sostituisce virgole con punti
            df[col] = pd.to_numeric(df[col], errors="coerce")  # Converte in numerico

        # 🔹 Controlla se ci sono ancora valori NaN nelle colonne numeriche
        for col in numeric_columns:
            df[col] = df[col].fillna(0)  # Riempie i NaN con 0

        # 🔹 Mostra i tipi di dati dopo la conversione
        st.write("✅ **Tipi di Dati Dopo la Conversione:**")
        st.write(df.dtypes)

        return df.to_dict(orient='records')

    except Exception as e:
        st.error(f"Errore nel caricamento del database: {e}")
        return None

# 🔹 Caricamento Database
database = load_database()

# 🔹 Se il database non è stato caricato, interrompi il programma
if database is None:
    st.stop()

st.write("✅ **Database caricato con successo!**")
