import streamlit as st
import google.generativeai as genai

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Asistente Técnico SolarDan",
    page_icon="☀️",
    layout="centered"
)

# --- CONFIGURACIÓN DE SOLARDAN ---
# Aquí definimos el enlace a tu calendario para cuando la IA no pueda resolverlo
ENLACE_CALENDARIO = "https://calendly.com/PON-AQUI-TU-ENLACE" 

# Título y subtítulo visible
st.title("☀️ Asistente Técnico SolarDan ☀️")
st.caption("Tu experto en energía solar. Diagnóstico preliminar y citas.")

# --- GESTIÓN DE LA CLAVE DE API (SECRETA) ---
# Intentamos obtener la clave desde los "secretos" de Streamlit
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except:
    # Esto es solo para que no de error visual si aún no está configurado,
    # pero el usuario final nunca verá esto si lo configuramos bien.
    st.error("⚠️ Falta configurar la API Key en Streamlit Cloud.")
    st.stop()

genai.configure(api_key=api_key)

# --- DEFINICIÓN DE LA PERSONALIDAD (PROMPT DEL SISTEMA) ---
# Aquí es donde le decimos a la IA quién es y cómo debe actuar.
instrucciones_sistema = f"""
Eres el asistente técnico virtual de la empresa "SolarDan", experta en instalaciones fotovoltaicas.
Tu objetivo es ayudar a clientes con dudas técnicas sobre sus placas solares e inversores.

REGLAS DE COMPORTAMIENTO:
1. Tono: Profesional, técnico pero accesible, y amable.
2. Seguridad ante todo: Si el usuario describe algo peligroso (humo, chispas, cables pelados, olor a quemado), indícale que apague el sistema inmediatamente y que contacte con un técnico urgente.
3. Diagnóstico: Intenta resolver dudas comunes (configuración de app, lecturas del inversor, limpieza de paneles).
4. LIMITACIÓN: Si la avería parece compleja, requiere herramientas, o no estás 100% seguro de la solución, NO inventes.
5. ACCIÓN COMERCIAL: En caso de dudas complejas o averías físicas, diles amablemente: 
   "Para este tipo de incidencia, es mejor que uno de nuestros técnicos de SolarDan lo revise presencialmente para asegurar tu instalación. Puedes reservar una cita directamente aquí: {https://calendly.com/solardangrancanaria}"

No des respuestas sobre temas que no sean energía solar o electricidad.
"""

# Configuración del modelo (usamos flash por ser rápido y eficiente)
model = genai.GenerativeModel(
    'gemini-1.5-flash',
    system_instruction=instrucciones_sistema
)

# --- HISTORIAL DEL CHAT ---
# Esto permite que el bot recuerde lo que se ha dicho en la conversación actual
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar mensajes anteriores en la pantalla
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- INTERACCIÓN CON EL USUARIO ---
if prompt := st.chat_input("Describe tu problema o consulta sobre tus placas..."):
    # 1. Guardar y mostrar mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Generar respuesta
    try:
        # Preparamos el historial para enviarlo a Gemini
        chat = model.start_chat(history=[
            {"role": m["role"], "parts": [m["content"]]} 
            for m in st.session_state.messages[:-1] # Todo menos el último que acabamos de añadir
        ])
        
        response = chat.send_message(prompt)
        text_response = response.text

        # 3. Mostrar respuesta del asistente
        with st.chat_message("assistant"):
            st.markdown(text_response)
        
        # 4. Guardar respuesta en historial
        st.session_state.messages.append({"role": "model", "content": text_response})

    except Exception as e:
        st.error(f"Lo siento, ha habido un error de conexión. Inténtalo de nuevo. Error: {e}")
