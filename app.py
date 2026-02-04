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
                sheet = get_sheet("Foglio1") 
                if sheet:
                    data_ora = datetime.now().strftime("%d/%m/%Y %H:%M")
                    stato = "✅ OK" if ((frigo == "Cella Negativa" and temp <= -18) or (frigo != "Cella Negativa" and temp <= 5)) else "🚨 ALLARME"
                    sheet.append_row([data_ora, frigo, str(temp), stato, firma])
                    st.success("Temperatura archiviata con successo!")

# =================================================================
# 4. TOOL 2: CHIUSURA SERATA
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
        note = st.text_area("Note")

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
            with st.spinner("Archiviazione..."):
                sheet = get_sheet("Chiusure")
                if sheet:
                    data = datetime.now().strftime("%d/%m/%Y")
                    sheet.append_row([data, responsabile, cassa, pos, u_spesa, u_fatture, u_extra, netto_contante, note])
                    st.success("Chiusura salvata!")
                    testo_wa = f"*CHIUSURA HORECA* %0AData: {data}%0A---%0A💰 Incasso: €{tot_incasso:.2f}%0A💸 Uscite: €{tot_uscite:.2f}%0A💵 *Netto Cassa: €{netto_contante:.2f}*"
                    st.link_button("📲 NOTIFICA WHATSAPP", f"https://wa.me/393929334563?text={testo_wa}")

# =================================================================
# 5. TOOL 3: MARGINI VINI (Aggiornato con Euro)
# =================================================================
elif menu == "🍷 Calcolo Margini Vini":
    st.subheader("Calcolo Rapido Guadagno Bottiglia")
    with st.container(border=True):
        p_acquisto = st.number_input("Costo d'acquisto (ESCLUSA IVA) (€)", min_value=0.0, value=10.0)
        p_vendita = st.number_input("Prezzo nel Menù (IVA INCLUSA) (€)", min_value=0.0, value=30.0)
    
    prezzo_netto_vendita = p_vendita / 1.22
    utile_euro = prezzo_netto_vendita - p_acquisto
    margine_perc = (utile_euro / prezzo_netto_vendita) * 100 if prezzo_netto_vendita > 0 else 0

    st.divider()
    col_v1, col_v2 = st.columns(2)
    col_v1.metric("Guadagno Netto", f"€ {utile_euro:.2f}")
    col_v2.metric("Margine Reale", f"{margine_perc:.1f}%")
    
    if margine_perc < 60:
        st.error("⚠️ Margine sotto la soglia SuPeR (60%). Valuta di alzare il prezzo.")
    else:
        st.success("✅ Margine eccellente per la gestione aziendale.")

# =================================================================
# 6. FOOTER FINALE (Unico e pulito)
# =================================================================
st.write("")
st.write("---")
st.write("### 📊 AREA TITOLARE")
st.link_button("📂 APRI REPORT COMPLETO (Google Sheets)", st.secrets["private_gsheets_url"])

st.markdown("""
    <div style="text-align: center; color: #888; font-size: 14px; margin-top: 20px;">
        Powered by 
        <a href="https://www.superstart.it" target="_blank" style="color: #b00000; text-decoration: none; font-weight: bold;">SuPeR</a> 
        & Streamlit
    </div>
    """, unsafe_allow_html=True)
