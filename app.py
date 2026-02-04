import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# =================================================================
# 1. CONNESSIONE A GOOGLE SHEETS
# =================================================================
# Qui useremo i "Secrets" di Streamlit per non mostrare le chiavi nel codice
def connect_to_sheet():
    try:
        # Recuperiamo le credenziali dai segreti di Streamlit Cloud
        creds_dict = st.secrets["gcp_service_account"]
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        # Inserisci qui l'URL del tuo foglio Google
        sheet = client.open_by_url(st.secrets["private_gsheets_url"]).sheet1
        return sheet
    except Exception as e:
        st.error(f"Errore di connessione a Google Sheets: {e}")
        return None

# =================================================================
# 2. CONFIGURAZIONE E DESIGN
# =================================================================
st.set_page_config(page_title="SuPeR HORECA Manager", page_icon="🏢", layout="centered")

st.markdown("""
<style>
    header {visibility: hidden !important;}
    .stApp { background-color: #ffffff !important; }
    html, body, [class*="css"], p, h1, h2, h3, label { color: #1a1a1a !important; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3.5em; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("🏢 SuPeR - HORECA Edition")
menu = st.selectbox("COSA DEVI FARE?", ["🌡️ Registro Temperature HACCP", "🍷 Calcolo Margini Listino Vini", "📝 Report Chiusura"])
st.divider()

# =================================================================
# 3. TOOL 1: HACCP (Salvataggio su Google Sheets)
# =================================================================
if menu == "🌡️ Registro Temperature HACCP":
    st.subheader("Registro Digitale Permanente")
    
    with st.container(border=True):
        frigo = st.selectbox("Elemento", ["Frigo Bevande", "Frigo Carne", "Frigo Pesce", "Cella Negativa", "Banco Bar"])
        temp = st.number_input("Temperatura Rilevata (°C)", value=4.0, step=0.5)
        firma = st.text_input("Firma Operatore")
    
    if st.button("SALVA NEL REGISTRO GOOGLE ☁️", type="primary"):
        if not firma:
            st.warning("La firma è obbligatoria per legge!")
        else:
            with st.spinner("Scrittura nel database in corso..."):
                sheet = connect_to_sheet()
                if sheet:
                    stato = "✅ OK"
                    if (frigo == "Cella Negativa" and temp > -18) or (frigo != "Cella Negativa" and temp > 5):
                        stato = "🚨 ALLARME"
                    
                    data_ora = datetime.now().strftime("%d/%m/%Y %H:%M")
                    # Invia i dati a Google
                    sheet.append_row([data_ora, frigo, str(temp), stato, firma])
                    st.success(f"Dato salvato correttamente nel foglio Google!")
                    st.balloons()

# =================================================================
# 4. TOOL 2: LISTINO VINI (Semplificato)
# =================================================================
elif menu == "🍷 Calcolo Margini Listino Vini":
    st.subheader("Calcolo Rapido Margine Bottiglia")
    
    with st.container(border=True):
        p_acquisto = st.number_input("Costo d'acquisto (ESCLUSA IVA) (€)", min_value=0.0, value=10.0)
        p_vendita = st.number_input("Prezzo nel Menù (IVA INCLUSA) (€)", min_value=0.0, value=35.0)
    
    # Calcoli onesti
    prezzo_netto_vendita = p_vendita / 1.22
    utile = prezzo_netto_vendita - p_acquisto
    margine = (utile / prezzo_netto_vendita) * 100 if prezzo_netto_vendita > 0 else 0

    st.divider()
    c1, c2 = st.columns(2)
    c1.metric("Utile Netto", f"€ {utile:.2f}")
    c2.metric("Margine Reale", f"{margine:.1f}%")
    
    if margine < 60:
        st.error("⚠️ Margine troppo basso per la gestione SuPeR!")
    else:
        st.success("✅ Margine corretto.")

# --- FOOTER ---
st.divider()
st.markdown("<div style='text-align: center; color: #888;'>Powered by <b>SuPeR</b> | HORECA Edition</div>", unsafe_allow_html=True)
