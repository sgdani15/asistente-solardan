import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Asistente Técnico SolarDan",
    page_icon="logo.png",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- ESTILOS VISUALES ---
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        /* Ajuste para imágenes en el chat */
        .stImage { max-width: 300px; }
    </style>
""", unsafe_allow_html=True)

# --- TUS DATOS ---
ENLACE_CALENDARIO = "https://calendly.com/solardangrancanaria" 
MENSAJE_BIENVENIDA = "¡Hola! Soy la IA de SolarDan. Puedo analizar texto e imágenes. ¿En qué te ayudo?"

# --- CONEXIÓN CON GOOGLE GEMINI ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("⚠️ Error: No se encuentra la API Key de Google.")
    st.stop()

# ==========================================
# 🟢 BARRA LATERAL (SOLO CONTACTO)
# ==========================================
with st.sidebar:
    st.header("SolarDan Asistencia")
    
    # --- SECCIÓN DESTACADA DE CITA ---
    st.markdown("### 🛠️ ¿Necesitas visita?")
    st.info("Si la avería es compleja o prefieres que lo revise un técnico presencialmente.")
    st.link_button("📅 RESERVAR CITA AHORA", ENLACE_CALENDARIO, type="primary")
    
    st.markdown("---")
    
    # --- DATOS DE CONTACTO ---
    st.markdown("**Contacto Directo:**")
    st.markdown("📧 info@solardan.com")
    
    st.markdown("---")
    
    # BOTÓN PARA REINICIAR EL CHAT
    if st.button("🗑️ Borrar conversación"):
        st.session_state.messages = []
        st.session_state["uploader_key"] += 1 # Truco para reiniciar el uploader
        st.rerun()
    
    st.markdown("---")
    st.caption("© 2025 SolarDan. Todos los derechos reservados.")

# ==========================================
# 🟢 ÁREA PRINCIPAL
# ==========================================

# --- LOGO Y TÍTULO ---
col1, col2, col3 = st.columns([1, 2, 1]) 
with col2:
    try:
        st.image("logo.png", use_container_width=True) 
    except:
        pass 

st.markdown("<h1 style='text-align: center;'>Asistente Técnico SolarDan</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Tu experto en energía solar. Diagnóstico preliminar y citas.</p>", unsafe_allow_html=True)

# --- LÓGICA DE IA ---
instrucciones_sistema = f"""
Eres el asistente técnico virtual de la empresa "SolarDan".
Objetivo: Ayudar a clientes con dudas técnicas de placas solares, analizando texto e imágenes si las aportan.

REGLAS:
1. Analiza la imagen si se proporciona. Describe lo que ves técnicamente.
2. SEGURIDAD: Si en la imagen o texto hay riesgo (humo, chispas), manda APAGAR todo y contactar técnico.
3. LIMITACIÓN: Si no sabes la solución o es avería física clara, deriva al calendario: {ENLACE_CALENDARIO}
4. No respondas de temas ajenos a la energía solar.
"""

# Configuración del modelo
try:
    model = genai.GenerativeModel('gemini-2.5-flash', system_instruction=instrucciones_sistema)
except:
    st.error("Error cargando el modelo de IA.")

# Inicializar historial
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state["uploader_key"] = 0 # Clave para controlar el reset del uploader

# Mensaje de bienvenida
if len(st.session_state.messages) == 0:
    st.session_state.messages.append({"role": "model", "content": MENSAJE_BIENVENIDA})

# Mostrar historial
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if isinstance(message["content"], list):
             for part in message["content"]:
                 if isinstance(part, str):
                     st.markdown(part)
        else:
            st.markdown(message["content"])

# ==========================================
# 📸 SUBIDA DE IMAGEN (Justo encima del chat)
# ==========================================
# Usamos un expander para que no ocupe mucho sitio si no se usa
with st.expander("📸 Adjuntar imagen al mensaje", expanded=False):
    uploaded_file = st.file_uploader(
        "Sube tu foto y luego escribe abajo:", 
        type=["jpg", "png", "jpeg"], 
        key=f"uploader_{st.session_state['uploader_key']}" # Truco dinámico para resetear
    )
    if uploaded_file:
        st.success("Imagen cargada. Escribe tu mensaje abajo para enviarla.")
        st.image(uploaded_file, width=150)

# ==========================================
# 💬 ENTRADA DE TEXTO
# ==========================================
if prompt := st.chat_input("Escribe tu consulta aquí..."):
    
    content_to_send = [prompt]
    
    with st.chat_message("user"):
        st.markdown(prompt)
        if uploaded_file:
            img = Image.open(uploaded_file)
            content_to_send.append(img)
            st.image(uploaded_file, caption="Imagen enviada", width=200)
            st.session_state.messages.append({"role": "user", "content": content_to_send})
        else:
            st.session_state.messages.append({"role": "user", "content": prompt})

    # Generar respuesta
    try:
        with st.spinner("Analizando..."):
            if uploaded_file:
                # Interacción única para imágenes
                response = model.generate_content(content_to_send)
            else:
                # Historial de chat para texto
                text_history = []
                for m in st.session_state.messages[:-1]:
                    content = m["content"]
                    if isinstance(content, list):
                         for part in content:
                             if isinstance(part, str): text_history.append({"role": m["role"], "parts": [part]})
                    elif content != MENSAJE_BIENVENIDA:
                        text_history.append({"role": m["role"], "parts": [content]})

                chat = model.start_chat(history=text_history)
                response = chat.send_message(prompt)

        text_response = response.text
        
        with st.chat_message("assistant"):
            st.markdown(text_response)
        
        st.session_state.messages.append({"role": "model", "content": text_response})
        
        # Limpiar uploader tras enviar forzando cambio de key
        if uploaded_file:
            st.session_state["uploader_key"] += 1
            st.rerun()

    except Exception as e:
        st.error(f"Error de conexión. Inténtalo de nuevo. Error: {e}")
