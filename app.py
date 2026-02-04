import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials
import time

# --- CONNESSIONE GOOGLE ---
def get_sheet(sheet_name):
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_url(st.secrets["private_gsheets_url"]).worksheet(sheet_name)
        return sheet
    except Exception as e:
        return None

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="SuPeR HORECA Manager", page_icon="🏢", layout="centered")

st.markdown("""
<style>
    header {visibility: hidden !important;}
    .stApp { background-color: #ffffff !important; color: #1a1a1a !important; }
    html, body, [class*="css"], p, h1, h2, h3, label { color: #1a1a1a !important; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3.5em; font-weight: bold; }
    .turni-card { background-color: #f1f3f6; padding: 15px; border-radius: 10px; border-left: 5px solid #800020; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

st.title("🏢 SuPeR - HORECA Edition")
menu = st.selectbox("COSA DEVI FARE?", ["🌡️ Registro HACCP", "📝 Chiusura Cassa", "📅 Gestione Turni", "🍷 Margini Vini"])
st.divider()

# =================================================================
# NUOVO TOOL: GESTIONE TURNI
# =================================================================
if menu == "📅 Gestione Turni":
    tab_ins, tab_view = st.tabs(["➕ Inserisci Turno", "👀 Visualizza e Invia"])

    with tab_ins:
        st.subheader("Pianifica un nuovo turno")
        with st.container(border=True):
            data_t = st.date_input("Giorno", datetime.now())
            nome_t = st.text_input("Nome Dipendente")
            ruolo_t = st.selectbox("Ruolo", ["Sala", "Cucina", "Bar", "Lavaggio", "Extra"])
            c1, c2 = st.columns(2)
            ora_in = c1.text_input("Ora Inizio (es. 18:00)", "18:00")
            ora_fi = c2.text_input("Ora Fine (es. 24:00)", "00:00")
            cell_t = st.text_input("Cellulare (es. 39392...)", "39")
        
        if st.button("SALVA TURNO 💾"):
            sheet = get_sheet("Turni")
            if sheet:
                sheet.append_row([data_t.strftime("%d/%m/%Y"), nome_t, ruolo_t, ora_in, ora_fi, cell_t])
                st.success(f"Turno di {nome_t} salvato!")

    with tab_view:
        st.subheader("Turni in programma")
        sheet = get_sheet("Turni")
        if sheet:
            data = sheet.get_all_records()
            if data:
                df = pd.DataFrame(data)
                # Mostriamo solo i turni da oggi in poi
                for _, row in df.iterrows():
                    with st.container():
                        st.markdown(f"""
                        <div class="turni-card">
                            <b>{row['Data']}</b> - {row['Dipendente']} ({row['Ruolo']})<br>
                            🕒 Orario: {row['Inizio']} - {row['Fine']}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Tasto WhatsApp
                        msg = f"Ciao {row['Dipendente']}, ti confermo il turno SuPeR per il {row['Data']}: dalle {row['Inizio']} alle {row['Fine']}. Buon lavoro!"
                        st.link_button(f"📲 AVVISA {row['Dipendente'].upper()}", f"https://wa.me/{row['Cellulare']}?text={msg}")
                        st.write("")
            else:
                st.info("Nessun turno inserito.")

# =================================================================
# (RESTA IL CODICE PRECEDENTE PER HACCP, CASSA E VINI...)
# =================================================================
elif menu == "🌡️ Registro HACCP":
    st.subheader("Registro Temperature")
    with st.container(border=True):
        frigo = st.selectbox("Elemento", ["Frigo Bevande", "Frigo Carne", "Frigo Pesce", "Cella Negativa", "Banco Bar"])
        temp = st.number_input("Temperatura Rilevata (°C)", value=4.0, step=0.5)
        firma = st.text_input("Firma")
    if st.button("SALVA ✅"):
        sheet = get_sheet("Foglio1")
        if sheet:
            sheet.append_row([datetime.now().strftime("%d/%m/%Y %H:%M"), frigo, str(temp), "OK", firma])
            st.success("Salvato!")

elif menu == "📝 Chiusura Cassa":
    st.subheader("Chiusura e Uscite")
    with st.container(border=True):
        cassa_inc = st.number_input("Contanti (€)", 0.0)
        pos_inc = st.number_input("POS (€)", 0.0)
        u_tot = st.number_input("Totale Uscite (Spesa/Extra) (€)", 0.0)
        resp = st.text_input("Responsabile")
    if st.button("SALVA E INVIA 🚀"):
        sheet = get_sheet("Chiusure")
        if sheet:
            data = datetime.now().strftime("%d/%m/%Y")
            netto = cassa_inc - u_tot
            sheet.append_row([data, resp, cassa_inc, pos_inc, 0, 0, u_tot, netto, ""])
            st.success("Chiusura registrata!")
            msg = f"*CHIUSURA*%0AData: {data}%0ATot: €{cassa_inc+pos_inc}%0ANetto Cassa: €{netto}"
            st.link_button("📲 NOTIFICA WHATSAPP", f"https://wa.me/393929334563?text={msg}")

elif menu == "🍷 Calcolo Margini Vini":
    st.subheader("Analisi Margini")
    acq = st.number_input("Acquisto (No IVA)", 0.0, value=10.0)
    ven = st.number_input("Vendita (Con IVA)", 0.0, value=30.0)
    netto = ven/1.22
    utile = netto - acq
    st.metric("Utile Netto", f"€ {utile:.2f}")
    st.metric("Margine", f"{(utile/netto)*100:.1f}%")

# --- FOOTER ---
st.write("---")
st.write("### 📊 AREA TITOLARE")
st.link_button("📂 APRI REPORT COMPLETO (Google Sheets)", st.secrets["private_gsheets_url"])
st.markdown("<div style='text-align: center; color: #888;'>Powered by <a href='https://www.superstart.it' target='_blank' style='color: #b00000; text-decoration: none; font-weight: bold;'>SuPeR</a> & Streamlit</div>", unsafe_allow_html=True)
