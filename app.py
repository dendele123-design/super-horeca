import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import time

# --- CONNESSIONE A GOOGLE SHEETS ---
def connect_to_sheet():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_url(st.secrets["private_gsheets_url"]).sheet1
        return sheet
    except Exception as e:
        st.error(f"Errore di connessione: {e}")
        return None

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="SuPeR HORECA", page_icon="🏢")

st.markdown("""
<style>
    header {visibility: hidden !important;}
    .stApp { background-color: #ffffff !important; }
    html, body, [class*="css"], p, h1, h2, h3, label { color: #1a1a1a !important; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3.5em; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("🏢 SuPeR - HORECA Edition")
menu = st.selectbox("COSA DEVI FARE?", ["🌡️ Registro HACCP", "🍷 Calcolo Margini Vini", "📝 Report Chiusura"])
st.divider()

if menu == "🌡️ Registro HACCP":
    st.subheader("Registrazione Temperatura")
    with st.container(border=True):
        frigo = st.selectbox("Elemento", ["Frigo Bevande", "Frigo Carne", "Frigo Pesce", "Cella Negativa", "Banco Bar"])
        temp = st.number_input("Temperatura (°C)", value=4.0, step=0.5)
        firma = st.text_input("Firma Operatore")
    
    if st.button("SALVA SU GOOGLE SHEETS ☁️", type="primary"):
        if not firma:
            st.warning("Firma obbligatoria!")
        else:
            with st.spinner("Salvataggio..."):
                sheet = connect_to_sheet()
                if sheet:
                    stato = "✅ OK"
                    if (frigo == "Cella Negativa" and temp > -18) or (frigo != "Cella Negativa" and temp > 5):
                        stato = "🚨 ALLARME"
                    data_ora = datetime.now().strftime("%d/%m/%Y %H:%M")
                    sheet.append_row([data_ora, frigo, str(temp), stato, firma])
                    st.success("Dato salvato sul Foglio Google!")

elif menu == "🍷 Calcolo Margini Vini":
    st.subheader("Calcolo Rapido Margine")
    with st.container(border=True):
        p_acquisto = st.number_input("Costo d'acquisto (No IVA) (€)", min_value=0.0, value=10.0)
        p_vendita = st.number_input("Prezzo vendita (Con IVA) (€)", min_value=0.0, value=35.0)
    
    prezzo_netto = p_vendita / 1.22
    utile = prezzo_netto - p_acquisto
    margine = (utile / prezzo_netto) * 100 if prezzo_netto > 0 else 0

    st.divider()
    st.metric("Utile Netto", f"€ {utile:.2f}")
    st.metric("Margine Reale", f"{margine:.1f}%")
    
    if margine < 60: st.error("Margine basso!")
    else: st.success("Margine OK!")

elif menu == "📝 Report Chiusura":
    st.subheader("Chiusura Cassa")
    with st.container(border=True):
        cassa = st.number_input("Contanti (€)", min_value=0.0)
        pos = st.number_input("POS (€)", min_value=0.0)
        note = st.text_area("Note")
    
    if st.button("INVIA REPORT WHATSAPP 📲"):
        testo = f"*REPORT* %0AContanti: €{cassa} %0APOS: €{pos} %0ANote: {note}"
        st.link_button("APRI WHATSAPP", f"https://wa.me/393929334563?text={testo}")

st.divider()
st.caption("Powered by SuPeR | HORECA Edition")
