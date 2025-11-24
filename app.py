import streamlit as st
import google.generativeai as genai

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Asistente Técnico SolarDan",
    page_icon="logo.png",
    layout="centered",
    initial_sidebar_state="expanded" # Abre la barra lateral por defecto
)

# --- ESTILOS CSS PERSONALIZADOS (Opcional pero recomendado) ---
# Esto oculta el menú de hamburguesa de arriba a la derecha y el pie de página de "Made with Streamlit"
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- CONFIGURACIÓN ---
ENLACE_CALENDARIO = "https://calendly.com/solardangrancanaria" 
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("⚠️ Falta configurar la API Key.")
    st.stop()

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    # Si quieres poner el logo también en pequeño aquí, descomenta la siguiente línea:
    # st.image("logo.png", width=100) 
    st.header("Sobre SolarDan")
    st.markdown("Somos expertos en energía fotovoltaica en Gran Canaria.")
    
    st.markdown("---")
    st.markdown("### 📞 Contacto")
    st.markdown("¿Prefieres hablar con un humano?")
    # Puedes poner tu teléfono real aquí abajo
    st.markdown("📧 info@solardan.com") 
    
    st.markdown("---")
    if st.button("🗑️ Borrar conversación"):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    st.caption("© 2025 SolarDan. Todos los derechos reservados.")

# --- DISEÑO CENTRAL (TU LOGO) ---
col1, col2, col3 = st.columns([1, 2, 1]) 
with col2:
    try:
        st.image("logo.png", use_container_width=True) 
    except:
        pass 

st.markdown("<h1 style='text-align: center;'>Asistente Técnico SolarDan</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Tu experto en energía solar. Diagnóstico preliminar y citas.</p>", unsafe_allow_html=True)

# --- IA Y LÓGICA ---
instrucciones_sistema = f"""
Eres el asistente técnico virtual de la empresa "SolarDan".
Objetivo: Ayudar a clientes con dudas técnicas de placas solares.

REGLAS:
1. Tono: Profesional y amable.
2. SEGURIDAD: Si hay riesgo (humo, chispas), manda APAGAR todo y contactar técnico.
3. LIMITACIÓN: Si no sabes la solución o es avería física, deriva al calendario: {ENLACE_CALENDARIO}
4. No respondas de temas ajenos a la energía solar.
"""

try:
    model = genai.GenerativeModel('gemini-2.5-flash', system_instruction=instrucciones_sistema)
except:
    st.error("Error cargando modelo IA.")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Mensaje de bienvenida si el chat está vacío
if len(st.session_state.messages) == 0:
    with st.chat_message("assistant"):
        st.markdown("¡Hola! Soy la IA de SolarDan. ¿En qué puedo ayudarte hoy con tu instalación?")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Escribe tu duda aquí..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        chat = model.start_chat(history=[{"role": m["role"], "parts": [m["content"]]} for m in st.session_state.messages[:-1]])
        response = chat.send_message(prompt)
        
        with st.chat_message("assistant"):
            st.markdown(response.text)
        st.session_state.messages.append({"role": "model", "content": response.text})

    except Exception as e:
        st.error("Error de conexión temporal.")

# --- DISCLAIMER FINAL (Aviso Legal) ---
st.markdown("---")
st.caption("⚠️ **Nota:** Este es un asistente basado en Inteligencia Artificial. Aunque está entrenado para ayudar, puede cometer errores. Para averías críticas, consulta siempre con nuestro equipo humano.")
