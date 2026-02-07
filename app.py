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
    except Exception:
        return None

# =================================================================
# 2. CONFIGURAZIONE E DESIGN
# =================================================================
st.set_page_config(page_title="SuPeR HORECA Manager", page_icon="🚀", layout="centered")

ROSSO_BRAND = "#DC0612"

st.markdown(f"""
<style>
    header {{visibility: hidden !important;}}
    .stApp {{ background-color: #ffffff !important; color: #1a1a1a !important; }}
    html, body, [class*="css"], p, h1, h2, h3, label {{ color: #1a1a1a !important; }}
    .stButton>button {{ width: 100%; border-radius: 10px; height: 3.5em; font-weight: bold; }}
    .stMetric {{ background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #eee; }}
    .history-card {{ 
        background-color: #f1f3f6; 
        padding: 15px; 
        border-radius: 10px; 
        border-left: 5px solid #800020; 
        margin-bottom: 10px; 
        font-size: 14px;
    }}
</style>
""", unsafe_allow_html=True)

st.title("🚀 SuPeR - HORECA Edition")
menu = st.selectbox("COSA DEVI FARE?", ["📅 Gestione Turni", "📝 Chiusura Cassa", "🌡️ Registro HACCP", "🍷 Margini Vini"])
st.divider()

# =================================================================
# 1. GESTIONE TURNI
# =================================================================
if menu == "📅 Gestione Turni":
    st.subheader("➕ Pianifica Turno")
    with st.container(border=True):
        data_t = st.date_input("Giorno", datetime.now())
        nome_t = st.text_input("Nome Dipendente")
        ruolo_t = st.selectbox("Ruolo", ["Sala", "Cucina", "Bar", "Lavaggio", "Extra"])
        c1, c2 = st.columns(2)
        ora_in = c1.text_input("Inizio", "18:00")
        ora_fi = c2.text_input("Fine", "00:00")
        cell_t = st.text_input("Cellulare (es. 39333...)", "39")
    
    if st.button("SALVA E AGGIORNA ELENCO 💾"):
        sheet = get_sheet("Turni")
        if sheet:
            data_it = data_t.strftime("%d/%m/%Y")
            sheet.append_row([data_it, nome_t, ruolo_t, ora_in, ora_fi, cell_t])
            st.success(f"Turno del {data_it} salvato!")
            time.sleep(1)
            st.rerun()

    st.write("---")
    st.subheader("👀 Prossimi Turni")
    sheet = get_sheet("Turni")
    if sheet:
        # Lettura sicura
        all_values = sheet.get_all_values()
        if len(all_values) > 1:
            headers = all_values[0]
            rows = all_values[1:]
            for r in reversed(rows[-10:]):
                row = dict(zip(headers, r))
                with st.container():
                    st.markdown(f"""<div class="history-card">
<b>{row.get('Data','')}</b> - {row.get('Dipendente','')} ({row.get('Ruolo','')})<br>
🕒 {row.get('Inizio','')} - {row.get('Fine','')}
</div>""", unsafe_allow_html=True)
                    msg = f"Ciao {row.get('Dipendente','')}, ti confermo il turno SuPeR per il {row.get('Data','')}: dalle {row.get('Inizio','')} alle {row.get('Fine','')}. Buon lavoro!"
                    st.link_button(f"📲 AVVISA {row.get('Dipendente','').upper()}", f"https://wa.me/{row.get('Cellulare','')}?text={msg.replace(' ', '%20')}")
                    st.write("")
        else:
            st.info("Nessun turno in archivio.")

# =================================================================
# 2. CHIUSURA CASSA
# =================================================================
elif menu == "📝 Chiusura Cassa":
    st.subheader("💰 Inserimento Chiusura")
    with st.container(border=True):
        col1, col2 = st.columns(2)
        cassa_inc = col1.number_input("Contanti (€)", 0.0, step=10.0)
        pos_inc = col2.number_input("POS (€)", 0.0, step=10.0)
        u_tot = st.number_input("Totale Uscite (€)", 0.0, step=5.0)
        resp = st.text_input("Responsabile")
    
    netto = cassa_inc - u_tot
    
    if st.button("ARCHIVIA CHIUSURA 🚀", type="primary"):
        sheet = get_sheet("Chiusure")
        if sheet:
            data_oggi = datetime.now().strftime("%d/%m/%Y")
            sheet.append_row([data_oggi, resp, cassa_inc, pos_inc, 0, 0, u_tot, netto, ""])
            st.success("Chiusura registrata!")
            time.sleep(1)
            st.rerun()

    st.write("---")
    st.subheader("📊 Ultime Chiusure")
    sheet = get_sheet("Chiusure")
    if sheet:
        all_values = sheet.get_all_values()
        if len(all_values) > 1:
            df = pd.DataFrame(all_values[1:], columns=all_values[0])
            st.table(df[['Data', 'Responsabile', 'Totale Netto']].tail(5).iloc[::-1])
        else:
            st.info("Nessuna chiusura presente.")

# =================================================================
# 3. REGISTRO HACCP
# =================================================================
elif menu == "🌡️ Registro HACCP":
    st.subheader("🌡️ Rilevazione Temperature")
    with st.container(border=True):
        frigo = st.selectbox("Elemento", ["Frigo Bevande", "Frigo Carne", "Frigo Pesce", "Cella Negativa", "Banco Bar"])
        temp = st.number_input("Temperatura Rilevata (°C)", value=4.0, step=0.5)
        firma = st.text_input("Firma Operatore")
    
    if st.button("REGISTRA TEMPERATURA ✅"):
        sheet = get_sheet("Foglio1")
        if sheet:
            data_h = datetime.now().strftime("%d/%m/%Y %H:%M")
            stato = "✅ OK" if temp <= 5 else "🚨 ALLARME"
            sheet.append_row([data_h, frigo, str(temp), stato, firma])
            st.success("Temperatura salvata!")
            time.sleep(1)
            st.rerun()

    st.write("---")
    st.subheader("📋 Ultime Rilevazioni")
    sheet = get_sheet("Foglio1")
    if sheet:
        all_values = sheet.get_all_values()
        if len(all_values) > 1:
            df_h = pd.DataFrame(all_values[1:], columns=all_values[0])
            st.table(df_h.tail(5).iloc[::-1])
        else:
            st.info("Nessuna rilevazione presente.")

# =================================================================
# 4. MARGINI VINI
# =================================================================
elif menu == "🍷 Margini Vini":
    st.subheader("Calcolo Margine")
    acq = st.number_input("Acquisto (No IVA)", 0.0, value=10.0)
    ven = st.number_input("Vendita (Con IVA)", 0.0, value=30.0)
    netto = ven/1.22
    utile = netto - acq
    st.divider()
    st.metric("Utile Netto", f"€ {utile:.2f}")
    st.metric("Margine Reale", f"{(utile/netto)*100:.1f}%")

# =================================================================
# 5. AREA TITOLARE E HUB
# =================================================================
st.write("")
st.write("---")
st.write("### 📊 AREA TITOLARE")
st.link_button("📂 APRI REPORT COMPLETO (Google Sheets)", st.secrets["private_gsheets_url"])

st.write("")
st.markdown("<p style='text-align:center; font-size:13px; color:#888;'>Hai bisogno di altri strumenti?</p>", unsafe_allow_html=True)
st.link_button("🌐 VEDI TUTTE LE NOSTRE WEB APP", "https://app-comunicattivamente-center.streamlit.app/")

st.markdown(f"""
    <div style="text-align: center; color: #888; font-size: 14px; margin-top: 20px;">
        Powered by <a href="https://www.superstart.it" target="_blank" style="color: {ROSSO_BRAND}; text-decoration: none; font-weight: bold;">SuPeR</a> & Streamlit
    </div>
""", unsafe_allow_html=True)
