import streamlit as st
import google.generativeai as genai

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Asistente Técnico SolarDan",
    page_icon="logo.png",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- ESTILOS VISUALES (Ocultar menús molestos) ---
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- TUS DATOS ---
ENLACE_CALENDARIO = "https://calendly.com/solardangrancanaria" 

# --- CONEXIÓN CON GOOGLE GEMINI ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("⚠️ Error: No se encuentra la API Key de Google.")
    st.stop()

# ==========================================
# 🟢 BARRA LATERAL (SIDEBAR) - ACTUALIZADA
# ==========================================
with st.sidebar:
    st.header("SolarDan Asistencia")
    
    # --- SECCIÓN DESTACADA DE CITA ---
    st.markdown("### 🛠️ ¿Necesitas visita?")
    st.info("Si la avería es compleja o prefieres que lo revise un técnico presencialmente.")
    
    # Este es el botón directo a tu calendario
    st.link_button("📅 RESERVAR CITA AHORA", ENLACE_CALENDARIO, type="primary")
    
    st.markdown("---")
    
    # --- DATOS DE CONTACTO ---
    st.markdown("**Contacto Directo:**")
    st.markdown("📧 info@solardan.com")
    # st.markdown("📞 928 XX XX XX") # Descomenta y pon tu número si quieres
    
    st.markdown("---")
    
    # BOTÓN PARA REINICIAR EL CHAT
    if st.button("🗑️ Borrar conversación"):
        st.session_state.messages = []
        st.rerun()
        
# ==========================================
# 🟢 ÁREA PRINCIPAL (CHAT)
# ==========================================

# --- LOGO Y TÍTULO CENTRADOS ---
col1, col2, col3 = st.columns([1, 2, 1]) 
with col2:
    try:
        st.image("logo.png", use_container_width=True) 
    except:
        pass 

st.markdown("<h1 style='text-align: center;'>Asistente Técnico SolarDan</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Tu experto en energía solar. Diagnóstico preliminar y citas.</p>", unsafe_allow_html=True)

# --- LÓGICA DE IA (CEREBRO) ---
instrucciones_sistema = f"""
Eres el asistente técnico virtual de la empresa "SolarDan".
Objetivo: Ayudar a clientes con dudas técnicas de placas solares.

REGLAS:
1. Tono: Profesional, técnico pero cercano.
2. SEGURIDAD: Si hay riesgo (humo, chispas), manda APAGAR todo y contactar técnico.
3. LIMITACIÓN: Si no sabes la solución o es avería física, deriva al calendario: {ENLACE_CALENDARIO}
4. No respondas de temas ajenos a la energía solar.
"""

# Configuración del modelo (usamos el que confirmamos que funciona)
try:
    model = genai.GenerativeModel('gemini-2.5-flash', system_instruction=instrucciones_sistema)
except:
    st.error("Error cargando el modelo de IA. Revisa la configuración.")

# Inicializar historial
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mensaje de bienvenida automático (opcional, si te gusta que salude primero)
if len(st.session_state.messages) == 0:
    intro = "¡Hola! Soy la IA de SolarDan. ¿En qué puedo ayudarte hoy con tu instalación?"
    st.session_state.messages.append({"role": "model", "content": intro})

# Mostrar historial en pantalla
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Capturar entrada del usuario
if prompt := st.chat_input("Escribe aquí tu consulta..."):
    # 1. Mostrar mensaje usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Generar respuesta IA
    try:
        chat = model.start_chat(history=[{"role": m["role"], "parts": [m["content"]]} for m in st.session_state.messages if m["role"] != "model" or m["content"] != intro])
        
        response = chat.send_message(prompt)
        text_response = response.text
        
        with st.chat_message("assistant"):
            st.markdown(text_response)
        
        st.session_state.messages.append({"role": "model", "content": text_response})

    except Exception as e:
        st.error("Lo siento, estoy teniendo problemas de conexión. Por favor, usa el botón del menú lateral para contactar con un técnico.")

# --- PIE DE PÁGINA (DISCLAIMER) ---
st.markdown("---")
st.caption("⚠️ **Aviso:** Este es un asistente basado en Inteligencia Artificial. Aunque está entrenado para ayudar, puede cometer errores. Para averías críticas, consulta siempre con nuestro equipo humano.")
