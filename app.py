import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import time
import random

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
# 2. CONFIGURAZIONE E DESIGN (#DC0612)
# =================================================================
st.set_page_config(page_title="SuPeR HORECA Manager", page_icon="🚀", layout="centered")
ROSSO_BRAND = "#DC0612"

st.markdown(f"""
<style>
    /* ANTI DARK MODE */
    header {{visibility: hidden !important;}}
    .stApp {{ background-color: #ffffff !important; color: #1a1a1a !important; }}
    html, body, [class*="css"], p, h1, h2, h3, label, div {{ color: #1a1a1a !important; }}
    
    /* BOTTONI */
    .stButton>button {{ width: 100%; border-radius: 10px; height: 3.5em; font-weight: bold; }}
    div.stButton > button:first-child[kind="primary"] {{
        background-color: {ROSSO_BRAND} !important;
        color: white !important;
        border: none;
    }}
    
    /* SCHEDE STORICO */
    .history-card {{ 
        background-color: #f8f9fa; 
        padding: 15px; 
        border-radius: 10px; 
        border-left: 5px solid {ROSSO_BRAND}; 
        margin-bottom: 10px; 
        font-size: 14px;
    }}
    .stMetric {{ background-color: #f1f3f6; padding: 15px; border-radius: 10px; border: 1px solid #ddd; }}
</style>
""", unsafe_allow_html=True)

st.title("🚀 SuPeR - HORECA Edition")
menu = st.selectbox("COSA DEVI FARE?", ["📅 Gestione Turni", "📝 Chiusura Cassa Analitica", "🌡️ Registro HACCP", "🍷 Margini Vini"])
st.divider()

# =================================================================
# 1. GESTIONE TURNI
# =================================================================
if menu == "📅 Gestione Turni":
    st.subheader("➕ Pianifica Nuovo Turno")
    with st.container(border=True):
        data_t = st.date_input("Giorno", datetime.now())
        nome_t = st.text_input("Nome Dipendente")
        ruolo_t = st.selectbox("Ruolo", ["Sala", "Cucina", "Bar", "Lavaggio", "Extra"])
        c1, c2 = st.columns(2)
        ora_in = c1.text_input("Inizio", "18:00")
        ora_fi = c2.text_input("Fine", "00:00")
        cell_t = st.text_input("Cellulare (es. 39333...)", "39")
    
    if st.button("SALVA TURNO 💾", type="primary"):
        sheet = get_sheet("Turni")
        if sheet:
            data_it = data_t.strftime("%d/%m/%Y")
            sheet.append_row([data_it, nome_t, ruolo_t, ora_in, ora_fi, cell_t])
            st.success(f"Turno salvato per il {data_it}")
            time.sleep(1)
            st.rerun()

    st.write("---")
    st.subheader("👀 Turni in Programma")
    sheet = get_sheet("Turni")
    if sheet:
        all_v = sheet.get_all_values()
        if len(all_v) > 1:
            headers = all_v[0]
            for r in reversed(all_v[1:]):
                row = dict(zip(headers, r))
                with st.container():
                    st.markdown(f"""<div class="history-card"><b>{row.get('Data','')}</b> - {row.get('Dipendente','')} ({row.get('Ruolo','')})<br>🕒 {row.get('Inizio','')} - {row.get('Fine','')}</div>""", unsafe_allow_html=True)
                    msg = f"Ciao {row.get('Dipendente','')}, ti confermo il turno SuPeR per il {row.get('Data','')}: {row.get('Inizio','')}-{row.get('Fine','')}"
                    st.link_button(f"📲 AVVISA {row.get('Dipendente','').upper()}", f"https://wa.me/{row.get('Cellulare','')}?text={msg.replace(' ', '%20')}")
        else: st.info("Nessun turno presente.")

# =================================================================
# 2. CHIUSURA CASSA ANALITICA (Ripristinata!)
# =================================================================
elif menu == "📝 Chiusura Cassa Analitica":
    st.subheader("💰 Report Incassi e Uscite")
    with st.container(border=True):
        st.write("**--- 💰 INCASSI ---**")
        col_i1, col_i2 = st.columns(2)
        cassa_inc = col_i1.number_input("Incasso Contanti (€)", 0.0, step=10.0)
        pos_inc = col_i2.number_input("Incasso POS (€)", 0.0, step=10.0)
        
        st.write("**--- 💸 USCITE (Piccola Cassa) ---**")
        col_u1, col_u2, col_u3 = st.columns(3)
        u_spesa = col_u1.number_input("Spesa (€)", 0.0)
        u_fatture = col_u2.number_input("Fatture (€)", 0.0)
        u_extra = col_u3.number_input("Extra/Personale (€)", 0.0)
        
        resp = st.text_input("Responsabile Chiusura")
        note = st.text_area("Note e Ammanchi")

    # Calcoli
    tot_incasso = cassa_inc + pos_inc
    tot_uscite = u_spesa + u_fatture + u_extra
    netto_contante = cassa_inc - tot_uscite

    st.divider()
    m1, m2, m3 = st.columns(3)
    m1.metric("Incasso Tot", f"€ {tot_incasso:.2f}")
    m2.metric("Uscite Tot", f"€ {tot_uscite:.2f}")
    m3.metric("Netto Cassa", f"€ {netto_contante:.2f}")

    if st.button("ARCHIVIA E INVIA REPORT 🚀", type="primary"):
        if not resp:
            st.warning("Inserisci il nome del responsabile!")
        else:
            sheet = get_sheet("Chiusure")
            if sheet:
                data_it = datetime.now().strftime("%d/%m/%Y")
                sheet.append_row([data_it, resp, cassa_inc, pos_inc, u_spesa, u_fatture, u_extra, netto_contante, note])
                st.success("Chiusura archiviata!")
                msg = f"*CHIUSURA HORECA*%0AData: {data_it}%0A---%0A💰 Tot Incasso: €{tot_incasso:.2f}%0A💸 Tot Uscite: €{tot_uscite:.2f}%0A💵 *Netto Cassa: €{netto_contante:.2f}*"
                st.link_button("📲 NOTIFICA WHATSAPP", f"https://wa.me/393929334563?text={msg}")
                time.sleep(1)
                st.rerun()

    st.write("---")
    st.subheader("📊 Ultime 5 Chiusure")
    sheet = get_sheet("Chiusure")
    if sheet:
        all_v = sheet.get_all_values()
        if len(all_v) > 1:
            df = pd.DataFrame(all_v[1:], columns=all_v[0])
            # Verifichiamo quali colonne mostrare per sicurezza
            disp_cols = [c for c in ['Data', 'Responsabile', 'Totale Netto'] if c in df.columns]
            st.table(df[disp_cols].tail(5).iloc[::-1])

# =================================================================
# 3. REGISTRO HACCP
# =================================================================
elif menu == "🌡️ Registro HACCP":
    st.subheader("🌡️ Rilevazione Temperature")
    with st.container(border=True):
        frigo = st.selectbox("Elemento", ["Frigo Bevande", "Frigo Carne", "Frigo Pesce", "Cella Negativa", "Banco Bar"])
        temp = st.number_input("Temperatura Rilevata (°C)", value=4.0, step=0.5)
        firma = st.text_input("Firma Operatore")
    
    if st.button("REGISTRA ✅", type="primary"):
        sheet = get_sheet("Foglio1")
        if sheet:
            data_it = datetime.now().strftime("%d/%m/%Y %H:%M")
            sheet.append_row([data_it, frigo, str(temp), "OK", firma])
            st.success("Temperatura salvata!")
            time.sleep(1)
            st.rerun()

    st.write("---")
    st.subheader("📋 Log Recente")
    sheet = get_sheet("Foglio1")
    if sheet:
        all_v = sheet.get_all_values()
        if len(all_v) > 1:
            st.table(pd.DataFrame(all_v[1:], columns=all_v[0]).tail(5).iloc[::-1])

# =================================================================
# 4. MARGINI VINI
# =================================================================
elif menu == "🍷 Margini Vini":
    st.subheader("Calcolatrice Margine SuPeR")
    with st.container(border=True):
        acq = st.number_input("Acquisto (No IVA)", 0.0, value=10.0)
        ven = st.number_input("Vendita (Con IVA)", 0.0, value=30.0)
    
    netto = ven/1.22
    utile = netto - acq
    st.divider()
    c1, c2 = st.columns(2)
    c1.metric("Utile Netto", f"€ {utile:.2f}")
    c2.metric("Margine Reale", f"{(utile/netto)*100:.1f}%")

# =================================================================
# AREA TITOLARE E HUB
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
st.markdown(f"""
    <div style="text-align: center; color: #888; font-size: 14px; margin-top: 20px;">
        Powered by <a href="https://www.superstart.it" target="_blank" style="color: {ROSSO_BRAND}; text-decoration: none; font-weight: bold;">SuPeR</a> & Streamlit
    </div>
""", unsafe_allow_html=True)
