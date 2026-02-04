import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import time

# =================================================================
# 1. CONNESSIONE A GOOGLE SHEETS
# =================================================================
def get_sheet(sheet_name):
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        # Apre il foglio specifico (HACCP o Chiusure)
        sheet = client.open_by_url(st.secrets["private_gsheets_url"]).worksheet(sheet_name)
        return sheet
    except Exception as e:
        st.error(f"Errore connessione '{sheet_name}': {e}")
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
    .stMetric { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #eee; }
</style>
""", unsafe_allow_html=True)

st.title("🏢 SuPeR - HORECA Edition")
menu = st.selectbox("COSA DEVI FARE?", [
    "🌡️ Registro HACCP", 
    "📝 Report Chiusura & Cassa",
    "🍷 Calcolo Margini Vini"
])
st.divider()

# =================================================================
# 3. TOOL 1: HACCP
# =================================================================
if menu == "🌡️ Registro Temperature HACCP":
    st.subheader("Registrazione Temperatura Frigoriferi")
    with st.container(border=True):
        frigo = st.selectbox("Elemento", ["Frigo Bevande", "Frigo Carne", "Frigo Pesce", "Cella Negativa", "Banco Bar"])
        temp = st.number_input("Temperatura Rilevata (°C)", value=4.0, step=0.5)
        firma = st.text_input("Firma Operatore")
    
    if st.button("SALVA NEL REGISTRO ☁️", type="primary"):
        if not firma:
            st.warning("La firma è obbligatoria!")
        else:
            with st.spinner("Salvataggio..."):
                sheet = get_sheet("Foglio1") # Assicurati che il primo foglio si chiami così o cambialo
                if sheet:
                    data_ora = datetime.now().strftime("%d/%m/%Y %H:%M")
                    stato = "✅ OK" if ((frigo == "Cella Negativa" and temp <= -18) or (frigo != "Cella Negativa" and temp <= 5)) else "🚨 ALLARME"
                    sheet.append_row([data_ora, frigo, str(temp), stato, firma])
                    st.success("Temperatura archiviata con successo!")

# =================================================================
# 4. TOOL 2: CHIUSURA SERATA (CON USCITE)
# =================================================================
elif menu == "📝 Report Chiusura & Cassa":
    st.subheader("Chiusura Giornaliera e Gestione Cassa")
    
    with st.container(border=True):
        st.write("--- 💰 INCASSI ---")
        col1, col2 = st.columns(2)
        cassa = col1.number_input("Incasso Contanti (€)", min_value=0.0, step=10.0)
        pos = col2.number_input("Incasso POS (€)", min_value=0.0, step=10.0)
        
        st.write("--- 💸 USCITE (Cassa Contanti) ---")
        c3, c4, c5 = st.columns(3)
        u_spesa = c3.number_input("Spesa/Fornitori (€)", min_value=0.0)
        u_fatture = c4.number_input("Fatture pagate (€)", min_value=0.0)
        u_extra = c5.number_input("Extra/Personale (€)", min_value=0.0)
        
        responsabile = st.text_input("Nome Responsabile Chiusura")
        note = st.text_area("Note (es. ammanchi, guasti, eventi)")

    # Calcolo Totali
    tot_incasso = cassa + pos
    tot_uscite = u_spesa + u_fatture + u_extra
    netto_contante = cassa - tot_uscite

    st.divider()
    m1, m2, m3 = st.columns(3)
    m1.metric("Tot. Incasso", f"€ {tot_incasso:.2f}")
    m2.metric("Tot. Uscite", f"€ {tot_uscite:.2f}")
    m3.metric("Netto in Cassa", f"€ {netto_contante:.2f}")

    if st.button("SALVA CHIUSURA E INVIA 🚀", type="primary"):
        if not responsabile:
            st.warning("Inserisci il nome del responsabile!")
        else:
            with st.spinner("Archiviazione chiusura..."):
                sheet = get_sheet("Chiusure")
                if sheet:
                    data = datetime.now().strftime("%d/%m/%Y")
                    # Salvataggio su Google Sheets
                    sheet.append_row([data, responsabile, cassa, pos, u_spesa, u_fatture, u_extra, netto_contante, note])
                    
                    st.success("Chiusura salvata nel database!")
                    
                    # Messaggio per WhatsApp
                    testo_wa = f"*CHIUSURA HORECA* 🏢%0AData: {data}%0AResp: {responsabile}%0A---%0A💰 Incasso Tot: €{tot_incasso:.2f}%0A💳 di cui POS: €{pos:.2f}%0A💸 Uscite Tot: €{tot_uscite:.2f}%0A💵 *Contante Netto: €{netto_contante:.2f}*%0A---%0ANote: {note}"
                    st.link_button("📲 NOTIFICA AL TITOLARE (WhatsApp)", f"https://wa.me/393929334563?text={testo_wa}")

# =================================================================
# 5. TOOL 3: MARGINI VINI
# =================================================================
elif menu == "🍷 Calcolo Margini Vini":
    st.subheader("Calcolatrice Margini SuPeR")
    p_acquisto = st.number_input("Costo d'acquisto (No IVA) (€)", min_value=0.0, value=10.0)
    p_vendita = st.number_input("Prezzo vendita (Con IVA) (€)", min_value=0.0, value=35.0)
    prezzo_netto = p_vendita / 1.22
    utile = prezzo_netto - p_acquisto
    margine = (utile / prezzo_netto) * 100 if prezzo_netto > 0 else 0
    st.metric("Margine Reale", f"{margine:.1f}%")
    if margine < 60: st.error("Margine troppo basso!")
    else: st.success("Margine in linea!")

# --- FOOTER FISSO CON LINK AL REPORT ---
st.write("")
st.write("---")
st.write("### 📊 AREA TITOLARE")
st.link_button("📂 APRI REPORT COMPLETO (Google Sheets)", st.secrets["private_gsheets_url"])
st.caption("Powered by SuPeR | HORECA Edition")
