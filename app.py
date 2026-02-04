# --- INIZIALIZZAZIONE MEMORIA PER TEMPERATURE ---
if 'registro_haccp' not in st.session_state:
    st.session_state.registro_haccp = []

# --- NEL MENU HACCP ---
elif menu == "🌡️ Registro HACCP":
    st.subheader("Controllo Temperature Frigoriferi")
    
    with st.container(border=True):
        frigo = st.selectbox("Seleziona Elemento", ["Frigo Bevande", "Frigo Carne", "Cella Negativa", "Banco Bar"])
        temp = st.number_input("Temperatura Rilevata (°C)", value=4.0, step=0.5)
        operatore = st.text_input("Firma Operatore")
    
    if st.button("REGISTRA TEMPERATURA ✅"):
        # Creiamo il record
        nuovo_dato = {
            "Ora": datetime.now().strftime("%H:%M:%S"),
            "Elemento": frigo,
            "Temp": f"{temp} °C",
            "Firma": operatore,
            "Stato": "✅ OK" if temp <= 5 else "🚨 ALLARME"
        }
        # Lo salviamo nella memoria temporanea
        st.session_state.registro_haccp.append(nuovo_dato)
        st.success("Dato aggiunto al pannello!")

    # --- IL PANNELLINO DELLE REGISTRAZIONI ---
    if st.session_state.registro_haccp:
        st.write("### 📊 Registrazioni di oggi:")
        df = pd.DataFrame(st.session_state.registro_haccp)
        st.table(df) # Mostra una bella tabella pulita
        
        if st.button("🗑️ Svuota Registro"):
            st.session_state.registro_haccp = []
            st.rerun()
