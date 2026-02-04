import streamlit as st
import pandas as pd
from datetime import datetime
import time

# =================================================================
# 1. CONFIGURAZIONE PAGINA
# =================================================================
st.set_page_config(page_title="SuPeR HORECA Manager", page_icon="🏢", layout="centered")

# --- STILE ANTI DARK MODE ---
st.markdown("""
<style>
    header {visibility: hidden !important;}
    .stApp { background-color: #ffffff !important; color: #1a1a1a !important; }
    html, body, [class*="css"], p, h1, h2, h3, label { color: #1a1a1a !important; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3.5em; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# =================================================================
# 2. INIZIALIZZAZIONE MEMORIA TEMPORANEA (Session State)
# =================================================================
if 'registro_haccp' not in st.session_state:
    st.session_state.registro_haccp = []

# =================================================================
# 3. INTERFACCIA E NAVIGAZIONE
# =================================================================
st.title("🏢 SuPeR - HORECA Edition")
st.write("Strumenti operativi per il controllo aziendale")

menu = st.selectbox("COSA DEVI FARE?", [
    "🌡️ Registro Temperature HACCP", 
    "🍷 Calcolo Margini Listino Vini",
    "📝 Report Chiusura Serata"
])

st.divider()

# =================================================================
# 4. TOOL 1: HACCP (Versione con Tabella)
# =================================================================
if menu == "🌡️ Registro Temperature HACCP":
    st.subheader("Controllo Quotidiano Frigoriferi")
    
    with st.container(border=True):
        frigo = st.selectbox("Elemento", ["Frigo Bevande", "Frigo Carne", "Frigo Pesce", "Cella Negativa", "Banco Bar"])
        temp = st.number_input("Temperatura Rilevata (°C)", value=4.0, step=0.5)
        firma = st.text_input("Firma Operatore")
    
    if st.button("REGISTRA NEL GIORNALE ✅", type="primary"):
        if not firma:
            st.warning("Inserisci la firma per registrare!")
        else:
            stato = "✅ OK"
            if (frigo == "Cella Negativa" and temp > -18) or (frigo != "Cella Negativa" and temp > 5):
                stato = "🚨 ALLARME"
            
            nuovo_dato = {
                "Data/Ora": datetime.now().strftime("%d/%m %H:%M"),
                "Elemento": frigo,
                "Temp": f"{temp} °C",
                "Stato": stato,
                "Firma": firma
            }
            st.session_state.registro_haccp.append(nuovo_dato)
            st.success("Temperatura registrata!")

    # Visualizzazione Tabella
    if st.session_state.registro_haccp:
        st.write("### 📊 Log odierno:")
        df = pd.DataFrame(st.session_state.registro_haccp)
        st.table(df)
        st.caption("Nota: Questi dati sono temporanei. Per il registro legale serve il modulo Google Sheets.")

# =================================================================
# 5. TOOL 2: LISTINO VINI (Calcolo Margini)
# =================================================================
elif menu == "🍷 Calcolo Margini Listino Vini":
    st.subheader("Analisi Redditività Bottiglia")
    
    with st.container(border=True):
        nome_vino = st.text_input("Nome del vino / Etichetta")
        prezzo_acquisto = st.number_input("Prezzo d'acquisto (bottiglia singola ESCLUSA IVA) (€)", min_value=0.0, value=10.0)
        prezzo_vendita = st.number_input("Prezzo di vendita al cliente (IVA INCLUSA) (€)", min_value=0.0, value=30.0)
    
    # CALCOLI (Onestà Intellettuale: scorporiamo l'IVA al 22% per il vino)
    prezzo_vendita_netto = prezzo_vendita / 1.22
    guadagno_euro = prezzo_vendita_netto - prezzo_acquisto
    margine_percentuale = (guadagno_euro / prezzo_vendita_netto) * 100
    ricarico_moltiplicatore = prezzo_vendita / (prezzo_acquisto * 1.22) if prezzo_acquisto > 0 else 0

    if st.button("ANALIZZA MARGINE 📊"):
        st.divider()
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Guadagno Netto", f"€ {guadagno_euro:.2f}")
        with col2:
            st.metric("Margine Reale", f"{margine_percentuale:.1f}%")
        
        # Feedback dell'Esorcista
        if margine_percentuale < 60:
            st.error(f"⚠️ ATTENZIONE: Il margine su '{nome_vino}' è basso. Stai ricaricando solo {ricarico_moltiplicatore:.1f} volte il prezzo ivato.")
        else:
            st.success(f"✅ OTTIMO: Il margine su '{nome_vino}' è in linea con i parametri SuPeR.")

# =================================================================
# 6. TOOL 3: CHIUSURA SERATA
# =================================================================
elif menu == "📝 Report Chiusura Serata":
    st.subheader("Riepilogo fine turno")
    with st.container(border=True):
        col_c1, col_c2 = st.columns(2)
        with col_c1: cassa = st.number_input("Incasso Contanti (€)", min_value=0.0)
        with col_c2: pos = st.number_input("Incasso POS (€)", min_value=0.0)
        note = st.text_area("Eventuali ammanchi o note tecniche")
    
    if st.button("GENERA REPORT PER WHATSAPP 📲"):
        tot = cassa + pos
        testo = f"*REPORT CHIUSURA* %0AData: {datetime.now().strftime('%d/%m/%Y')} %0A--- %0A💰 Contanti: €{cassa} %0A💳 POS: €{pos} %0A*TOTALE: €{tot}* %0A--- %0ANote: {note}"
        st.link_button("INVIA AL TITOLARE", f"https://wa.me/393929334563?text={testo}")

# --- FOOTER ---
st.divider()
st.markdown("<div style='text-align: center; color: #888;'>Powered by <b>SuPeR</b> | HORECA Edition</div>", unsafe_allow_html=True)
