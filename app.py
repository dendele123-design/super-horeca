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
        sheet = client.open_by_url(st.secrets["private_gsheets_url"]).worksheet(sheet_name)
        return sheet
    except Exception as e:
        st.error(f"Errore connessione '{sheet_name}': {e}")
        return None

# =================================================================
# 2. CONFIGURAZIONE E DESIGN
# =================================================================
st.set_page_config(page_title="SuPeR HORECA Manager", page_icon="🚀", layout="centered")

st.markdown("""
<style>
    header {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    .stApp { background-color: #ffffff !important; }
    html, body, [class*="css"], p, h1, h2, h3, label { color: #1a1a1a !important; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3.5em; font-weight: bold; }
    .stMetric { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #eee; }
</style>
""", unsafe_allow_html=True)

st.title("🏢 SuPeR - HORECA Edition")

# --- MENU DI NAVIGAZIONE (Le scritte qui devono essere IDENTICHE a quelle sotto) ---
opzione = st.selectbox("COSA DEVI FARE?", [
    "🌡️ Registro HACCP", 
    "📝 Chiusura Cassa",
    "🍷 Calcolo Margini Vini"
])

st.divider()

# =================================================================
# 3. TOOL 1: REGISTRO HACCP
# =================================================================
if opzione == "🌡️ Registro HACCP":
    st.subheader("Registrazione Temperatura Frigoriferi")
    with st.container(border=True):
        frigo = st.selectbox("Elemento", ["Frigo Bevande", "Frigo Carne", "Frigo Pesce", "Cella Negativa", "Banco Bar"])
        temp = st.number_input("Temperatura Rilevata (°C)", value=4.0, step=0.5)
        firma = st.text_input("Firma Operatore")
    
    if st.button("SALVA NEL REGISTRO ☁️", type="primary"):
        if not firma:
            st.warning("La firma è obbligatoria!")
        else:
            with st.spinner("Archiviazione..."):
                sheet = get_sheet("Foglio1") # Assicurati che si chiami così su Sheets
                if sheet:
                    data_ora = datetime.now().strftime("%d/%m/%Y %H:%M")
                    stato = "✅ OK" if ((frigo == "Cella Negativa" and temp <= -18) or (frigo != "Cella Negativa" and temp <= 5)) else "🚨 ALLARME"
                    sheet.append_row([data_ora, frigo, str(temp), stato, firma])
                    st.success("Dato salvato sul registro Cloud!")

# =================================================================
# 4. TOOL 2: CHIUSURA CASSA
# =================================================================
elif opzione == "📝 Chiusura Cassa":
    st.subheader("Chiusura Giornaliera e Uscite")
    with st.container(border=True):
        st.write("--- 💰 INCASSI ---")
        col1, col2 = st.columns(2)
        cassa_inc = col1.number_input("Contanti (€)", min_value=0.0, step=10.0)
        pos_inc = col2.number_input("POS (€)", min_value=0.0, step=10.0)
        
        st.write("--- 💸 USCITE (Piccola Cassa) ---")
        c3, c4, c5 = st.columns(3)
        u_spesa = c3.number_input("Spesa (€)", min_value=0.0)
        u_fatture = c4.number_input("Fatture (€)", min_value=0.0)
        u_extra = c5.number_input("Extra (€)", min_value=0.0)
        
        resp = st.text_input("Responsabile")
        note = st.text_area("Note")

    tot_inc = cassa_inc + pos_inc
    tot_usc = u_spesa + u_fatture + u_extra
    netto_contante = cassa_inc - tot_usc

    st.divider()
    m1, m2, m3 = st.columns(3)
    m1.metric("Incasso Tot", f"€ {tot_inc:.2f}")
    m2.metric("Uscite Tot", f"€ {tot_usc:.2f}")
    m3.metric("Netto Cassa", f"€ {netto_contante:.2f}")

    if st.button("ARCHIVIA E INVIA REPORT 🚀", type="primary"):
        if not resp:
            st.warning("Manca il nome del responsabile!")
        else:
            with st.spinner("Salvataggio..."):
                sheet = get_sheet("Chiusure")
                if sheet:
                    data = datetime.now().strftime("%d/%m/%Y")
                    sheet.append_row([data, resp, cassa_inc, pos_inc, u_spesa, u_fatture, u_extra, netto_contante, note])
                    st.success("Chiusura registrata!")
                    msg = f"*CHIUSURA HORECA*%0AData: {data}%0A---%0A💰 Incasso: €{tot_inc:.2f}%0A💸 Uscite: €{tot_usc:.2f}%0A💵 *Netto: €{netto_contante:.2f}*"
                    st.link_button("📲 NOTIFICA WHATSAPP", f"https://wa.me/393929334563?text={msg}")

# =================================================================
# 5. TOOL 3: MARGINI VINI
# =================================================================
elif opzione == "🍷 Calcolo Margini Vini":
    st.subheader("Calcolo Guadagno Netto (Scorporo IVA 22%)")
    with st.container(border=True):
        acquisto = st.number_input("Costo d'acquisto Bottiglia (No IVA) (€)", min_value=0.0, value=10.0)
        vendita = st.number_input("Prezzo in Carta (IVA Inclusa) (€)", min_value=0.0, value=30.0)
    
    netto_vendita = vendita / 1.22
    guadagno_euro = netto_vendita - acquisto
    percentuale = (guadagno_euro / netto_vendita) * 100 if netto_vendita > 0 else 0
    moltiplicatore = vendita / (acquisto * 1.22) if acquisto > 0 else 0

    st.divider()
    cv1, cv2 = st.columns(2)
    cv1.metric("Guadagno Netto", f"€ {guadagno_euro:.2f}")
    cv2.metric("Margine Reale", f"{percentuale:.1f}%")
    
    st.write(f"ℹ️ Questa bottiglia ha un moltiplicatore di **{moltiplicatore:.1f}x** sul prezzo ivato.")
    
    if percentuale < 60:
        st.error("⚠️ MARGINE BASSO: Sei sotto la soglia SuPeR del 60%.")
    else:
        st.success("✅ MARGINE OTTIMO: La gestione è in salute.")

# =================================================================
# 6. FOOTER FINALE (Area Titolare + Brand)
# =================================================================
st.write("")
st.write("---")
st.write("### 📊 AREA TITOLARE")
st.link_button("📂 APRI REPORT COMPLETO (Google Sheets)", st.secrets["private_gsheets_url"])

st.markdown("""
    <div style="text-align: center; color: #888; font-size: 14px; margin-top: 30px;">
        Powered by 
        <a href="https://www.superstart.it" target="_blank" style="color: #b00000; text-decoration: none; font-weight: bold;">SuPeR</a> 
        & Streamlit
    </div>
    """, unsafe_allow_html=True)
