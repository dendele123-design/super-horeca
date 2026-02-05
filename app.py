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

st.markdown("""
<style>
    header {visibility: hidden !important;}
    .stApp { background-color: #ffffff !important; color: #1a1a1a !important; }
    html, body, [class*="css"], p, h1, h2, h3, label { color: #1a1a1a !important; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3.5em; font-weight: bold; }
    .stMetric { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #eee; }
    .history-card { 
        background-color: #f1f3f6; 
        padding: 15px; 
        border-radius: 10px; 
        border-left: 5px solid #800020; 
        margin-bottom: 10px; 
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)

st.title("🚀 SuPeR - HORECA Edition2")
menu = st.selectbox("COSA DEVI FARE?", ["📅 Gestione Turni", "📝 Chiusura Cassa", "🌡️ Registro HACCP", "🍷 Margini Vini"])
st.divider()

# =================================================================
# 1. GESTIONE TURNI (Inserimento + Visualizzazione sotto)
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
            # Salviamo la data in formato GG/MM/AAAA
            data_formattata = data_t.strftime("%d/%m/%Y")
            sheet.append_row([data_formattata, nome_t, ruolo_t, ora_in, ora_fi, cell_t])
            st.success("Turno salvato!")
            time.sleep(1)
            st.rerun()

    st.write("---")
    st.subheader("👀 Turni in Programma")
    sheet = get_sheet("Turni")
    if sheet:
        data = sheet.get_all_records()
        if data:
            # Mostriamo gli ultimi 10 turni inseriti (dal più recente)
            for row in reversed(data[-10:]):
                with st.container():
                    st.markdown(f"""
                    <div class="history-card">
                        <b>{row['Data']}</b> - {row['Dipendente']} ({row['Ruolo']})<br>
                        🕒 {row['Inizio']} - {row['Fine']}
                    </div>
                    """, unsafe_allow_html=True)
                    msg = f"Ciao {row['Dipendente']}, ti confermo il turno SuPeR per il {row['Data']}: {row['Inizio']}-{row['Fine']}. Buon lavoro!"
                    st.link_button(f"📲 AVVISA {row['Dipendente'].upper()}", f"https://wa.me/{row['Cellulare']}?text={msg.replace(' ', '%20')}")
                    st.write("")

# =================================================================
# 2. CHIUSURA CASSA (Inserimento + Visualizzazione sotto)
# =================================================================
elif menu == "📝 Chiusura Cassa":
    st.subheader("💰 Inserimento Chiusura")
    with st.container(border=True):
        col1, col2 = st.columns(2)
        cassa_inc = col1.number_input("Contanti (€)", 0.0, step=10.0)
        pos_inc = col2.number_input("POS (€)", 0.0, step=10.0)
        u_tot = st.number_input("Totale Uscite (Spesa/Extra) (€)", 0.0, step=5.0)
        resp = st.text_input("Responsabile")
    
    tot_inc = cassa_inc + pos_inc
    netto = cassa_inc - u_tot
    
    if st.button("ARCHIVIA CHIUSURA 🚀", type="primary"):
        sheet = get_sheet("Chiusure")
        if sheet:
            data_c = datetime.now().strftime("%d/%m/%Y")
            sheet.append_row([data_c, resp, cassa_inc, pos_inc, 0, 0, u_tot, netto, ""])
            st.success("Chiusura registrata!")
            time.sleep(1)
            st.rerun()

    st.write("---")
    st.subheader("📊 Ultime Chiusure")
    sheet = get_sheet("Chiusure")
    if sheet:
        data = sheet.get_all_records()
        if data:
            df = pd.DataFrame(data).tail(5).iloc[::-1] # Ultime 5 chiusure
            st.table(df[['Data', 'Responsabile', 'Totale Netto']])

# =================================================================
# 3. REGISTRO HACCP (Inserimento + Visualizzazione sotto)
# =================================================================
elif menu == "🌡️ Registro HACCP":
    st.subheader("🌡️ Nuova Rilevazione")
    with st.container(border=True):
        frigo = st.selectbox("Elemento", ["Frigo Bevande", "Frigo Carne", "Frigo Pesce", "Cella Negativa", "Banco Bar"])
        temp = st.number_input("Temperatura (°C)", value=4.0, step=0.5)
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
    st.subheader("📋 Log Temperature Recenti")
    sheet = get_sheet("Foglio1")
    if sheet:
        data = sheet.get_all_records()
        if data:
            df_h = pd.DataFrame(data).tail(5).iloc[::-1]
            st.table(df_h)

# =================================================================
# 4. MARGINI VINI
# =================================================================
elif menu == "🍷 Margini Vini":
    st.subheader("Calcolatrice Margine SuPeR")
    acq = st.number_input("Acquisto (No IVA)", 0.0, value=10.0)
    ven = st.number_input("Vendita (Con IVA)", 0.0, value=30.0)
    netto = ven/1.22
    utile = netto - acq
    st.divider()
    st.metric("Utile Netto", f"€ {utile:.2f}")
    st.metric("Margine Reale", f"{(utile/netto)*100:.1f}%")

# =================================================================
# FOOTER FINALE
# =================================================================
st.write("---")
st.write("### 📊 AREA TITOLARE")
st.link_button("📂 APRI REPORT COMPLETO (Google Sheets)", st.secrets["private_gsheets_url"])
st.markdown(f"""
    <div style="text-align: center; color: #888; font-size: 14px; margin-top: 20px;">
        Powered by <a href="https://www.superstart.it" target="_blank" style="color: #b00000; text-decoration: none; font-weight: bold;">SuPeR</a> & Streamlit
    </div>
""", unsafe_allow_html=True)
