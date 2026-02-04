import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="SuPeR HORECA Manager", page_icon="🏢", layout="centered")

st.markdown("""
<style>
    header {visibility: hidden !important;}
    .main { background-color: #f8f9fa; }
    .stApp { color: #1a1a1a; }
    .report-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        border-left: 10px solid #b00000;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

st.title("🏢 SuPeR - HORECA Edition")
st.write("Gestione operativa e controllo qualità")

# NAVIGAZIONE
menu = st.selectbox("COSA DEVI REGISTRARE?", ["📝 Chiusura Serata", "🌡️ Registro HACCP", "📊 Calcolo Food Cost"])

st.divider()

# --- 1. CHIUSURA SERATA ---
if menu == "📝 Chiusura Serata":
    st.subheader("Riepilogo fine turno")
    
    with st.container(border=True):
        operatore = st.text_input("Nome Responsabile")
        col1, col2 = st.columns(2)
        with col1:
            cassa = st.number_input("Chiusura Contanti (€)", min_value=0.0)
        with col2:
            pos = st.number_input("Chiusura POS (€)", min_value=0.0)
        
        note = st.text_area("Note (problemi, forniture mancanti, guasti)")

    if st.button("GENERA REPORT 📄"):
        totale = cassa + pos
        riepilogo = f"""
        *REPORT CHIUSURA* 🏢
        Data: {datetime.now().strftime('%d/%m/%Y')}
        Responsabile: {operatore}
        ---
        💰 Contanti: €{cassa}
        💳 POS: €{pos}
        *TOTALE: €{totale}*
        ---
        📝 Note: {note}
        """
        st.info("Copia il testo qui sotto e invialo al titolare:")
        st.code(riepilogo)
        
        # Tasto WhatsApp precompilato
        wa_link = f"https://wa.me/393929334563?text={riepilogo.replace(' ', '%20')}"
        st.link_button("📲 INVIA VIA WHATSAPP", wa_link)

# --- 2. HACCP TEMPERATURE ---
elif menu == "🌡️ Registro HACCP":
    st.subheader("Controllo Temperature Frigoriferi")
    
    frigo = st.selectbox("Seleziona Elemento", ["Frigo Bevande", "Frigo Carne", "Cella Negativa", "Banco Bar"])
    temp = st.number_input("Temperatura Rilevata (°C)", value=4.0, step=0.5)
    
    if st.button("REGISTRA TEMPERATURA ✅"):
        if (frigo == "Cella Negativa" and temp > -18) or (frigo != "Cella Negativa" and temp > 5):
            st.error(f"🚨 ALLARME: La temperatura di {frigo} è troppo alta ({temp}°C)!")
            st.warning("Azione correttiva: Verificare chiusura o chiamare manutenzione.")
        else:
            st.success(f"Temperatura {temp}°C registrata correttamente per {frigo}.")

# --- 3. FOOD COST ---
elif menu == "📊 Calcolo Food Cost":
    st.subheader("Calcolatore Margine Rapido")
    
    with st.container(border=True):
        costo_materie = st.number_input("Costo Materie Prime (€)", min_value=0.1, value=5.0)
        prezzo_vendita = st.number_input("Prezzo nel Menù (IVA inc.) (€)", min_value=0.1, value=15.0)
    
    prezzo_netto = prezzo_vendita / 1.10 # Ipotizzando IVA 10%
    margine_euro = prezzo_netto - costo_materie
    margine_perc = (margine_euro / prezzo_netto) * 100
    
    st.write(f"### Margine Reale: €{margine_euro:.2f}")
    
    if margine_perc < 65:
        st.error(f"Food Cost critico: {100-margine_perc:.1f}%. Stai guadagnando poco!")
    else:
        st.success(f"Margine ottimo: {margine_perc:.1f}%")

st.divider()
st.markdown("Powered by **SuPeR** | HORECA Edition")
