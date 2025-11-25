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
        /* Un pequeño ajuste para que la imagen subida no se vea gigante en el chat */
        .stImage { max-width: 300px; }
    </style>
""", unsafe_allow_html=True)

# --- TUS DATOS Y CONSTANTES ---
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
# 🟢 BARRA LATERAL (SIDEBAR) - CON UPLOADER
# ==========================================
with st.sidebar:
    st.header("SolarDan Asistencia")
    
    # --- NUEVO: SUBIDA DE IMAGEN ---
    st.markdown("---")
    st.markdown("### 📸 ¿Tienes una foto?")
    st.info("Sube aquí una foto del inversor, el panel dañado o el error en pantalla antes de escribir tu mensaje.")
    # El "key='uploader'" es vital para poder resetearlo luego
    uploaded_file = st.file_uploader("Elege una imagen...", type=["jpg", "png", "jpeg"], key="uploader")
    
    if uploaded_file:
        st.success("✅ Imagen cargada. Ahora escribe tu pregunta en el chat.")
        # Mostramos una miniatura en la barra lateral
        st.image(uploaded_file, caption="Imagen lista para enviar", use_container_width=True)

    st.markdown("---")

    # --- SECCIÓN DESTACADA DE CITA ---
    st.markdown("### 🛠️ ¿Necesitas visita?")
    st.link_button("📅 RESERVAR CITA AHORA", ENLACE_CALENDARIO, type="primary")
    
    st.markdown("---")
    
    # BOTÓN PARA REINICIAR EL CHAT
    if st.button("🗑️ Borrar conversación"):
        st.session_state.messages = []
        # Truco para limpiar también el uploader de archivos al reiniciar
        st.session_state["uploader"] = None
        st.rerun()

# ==========================================
# 🟢 ÁREA PRINCIPAL (CHAT)
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

# --- LÓGICA DE IA (CEREBRO) ---
instrucciones_sistema = f"""
Eres el asistente técnico virtual de la empresa "SolarDan".
Objetivo: Ayudar a clientes con dudas técnicas de placas solares, analizando texto e imágenes si las aportan.

REGLAS:
1. Analiza la imagen si se proporciona. Describe lo que ves técnicamente (ej: "Veo un inversor Huawei marcando error 303").
2. SEGURIDAD: Si en la imagen o texto hay riesgo (humo, chispas, quemaduras), manda APAGAR todo y contactar técnico.
3. LIMITACIÓN: Si no sabes la solución o es avería física clara, deriva al calendario: {ENLACE_CALENDARIO}
4. No respondas de temas ajenos a la energía solar.
"""

# Configuración del modelo
try:
    # Usamos gemini-1.5-flash porque es el mejor para imágenes ahora mismo en la capa gratuita
    model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=instrucciones_sistema)
except:
    st.error("Error cargando el modelo de IA.")

# Inicializar historial
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mensaje de bienvenida automático
if len(st.session_state.messages) == 0:
    st.session_state.messages.append({"role": "model", "content": MENSAJE_BIENVENIDA})

# Mostrar historial en pantalla (solo texto para no saturar)
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        # Si el mensaje tiene "partes" (es multimodal), extraemos solo el texto para el historial
        if isinstance(message["content"], list):
             for part in message["content"]:
                 if isinstance(part, str):
                     st.markdown(part)
        else:
            st.markdown(message["content"])

# --- CAPTURAR ENTRADA DEL USUARIO Y PROCESAR ---
if prompt := st.chat_input("Escribe tu consulta aquí..."):
    
    # 1. PREPARAR EL CONTENIDO PARA LA IA
    # Empezamos con el texto que ha escrito el usuario
    content_to_send = [prompt]
    
    # Visualizamos el mensaje del usuario
    with st.chat_message("user"):
        st.markdown(prompt)
        # Si hay imagen cargada en la barra lateral, la añadimos al paquete y la mostramos
        if uploaded_file:
            # Convertimos la imagen para Gemini
            img = Image.open(uploaded_file)
            content_to_send.append(img)
            # La mostramos en el chat
            st.image(uploaded_file, caption="Imagen enviada")
            # Importante: Guardamos en el historial que este mensaje tenía imagen
            st.session_state.messages.append({"role": "user", "content": content_to_send})
        else:
            # Si solo es texto
            st.session_state.messages.append({"role": "user", "content": prompt})

    # 2. GENERAR RESPUESTA IA
    try:
        # NOTA IMPORTANTE SOBRE HISTORIAL CON IMÁGENES:
        # Mantener un historial de chat largo que incluye múltiples imágenes es complejo y propenso a errores en Streamlit.
        # Para asegurar la fiabilidad, cuando se envía una imagen, usamos una interacción única (generate_content) 
        # en lugar de continuar el chat histórico. La IA recordará las instrucciones del sistema, pero no los mensajes anteriores inmediatos.
        # Es el método más robusto para empezar.
        
        with st.spinner("Analizando..."):
            if uploaded_file:
                # Si hay imagen, usamos generate_content (interacción única)
                response = model.generate_content(content_to_send)
            else:
                 # Si es solo texto, intentamos mantener la sesión de chat (más complejo)
                # Filtramos el historial para texto solamente para evitar romper el chat object
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
        
        # Mostrar respuesta
        with st.chat_message("assistant"):
            st.markdown(text_response)
        
        # Guardar respuesta en historial
        st.session_state.messages.append({"role": "model", "content": text_response})
        
        # 3. LIMPIEZA POSTERIOR
        # Si había una imagen, hay que limpiar el uploader para que la siguiente pregunta no la vuelva a enviar por error.
        if uploaded_file:
            st.session_state["uploader"] = None
            st.rerun() # Recargamos para que desaparezca la miniatura de la barra lateral

    except Exception as e:
        st.error(f"Error de conexión o la imagen es demasiado compleja. Prueba solo con texto. Error: {e}")
