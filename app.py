import streamlit as st
import google.generativeai as genai

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Asistente Técnico SolarDan",
    page_icon="logo.png",
    layout="centered"
)

# 👇 AÑADE ESTO JUSTO AQUÍ DEBAJO 👇
try:
    st.image("logo.png", width=300) # Ajusta el número 300 para hacerlo más grande o pequeño
except:
    pass # Si no encuentra el logo, no hace nada y no da error
# 👆 FIN DEL AÑADIDO 👆

# --- CONFIGURACIÓN DE SOLARDAN ---
ENLACE_CALENDARIO = "https://calendly.com/solardangrancanaria"

# Título y subtítulo
st.title("☀️ Asistente Técnico SolarDan ☀️")
st.caption("Tu experto en energía solar. Diagnóstico preliminar y citas.")

# --- GESTIÓN DE LA CLAVE DE API ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except:
    st.error("⚠️ Falta configurar la API Key en Streamlit Cloud.")
    st.stop()

genai.configure(api_key=api_key)

# --- DEFINICIÓN DE LA PERSONALIDAD ---
instrucciones_sistema = f"""
Eres el asistente técnico virtual de la empresa "SolarDan", experta en instalaciones fotovoltaicas.
Tu objetivo es ayudar a clientes con dudas técnicas sobre sus placas solares e inversores.

REGLAS DE COMPORTAMIENTO:
1. Tono: Profesional, técnico pero accesible, y amable.
2. Seguridad ante todo: Si el usuario describe algo peligroso (humo, chispas, cables pelados, olor a quemado), indícale que apague el sistema inmediatamente y que contacte con un técnico urgente.
3. Diagnóstico: Intenta resolver dudas comunes (configuración de app, lecturas del inversor, limpieza de paneles).
4. LIMITACIÓN: Si la avería parece compleja, requiere herramientas, o no estás 100% seguro de la solución, NO inventes.
5. ACCIÓN COMERCIAL: En caso de dudas complejas o averías físicas, diles amablemente: 
   "Para este tipo de incidencia, es mejor que uno de nuestros técnicos de SolarDan lo revise presencialmente para asegurar tu instalación. Puedes reservar una cita directamente aquí: {ENLACE_CALENDARIO}"

No des respuestas sobre temas que no sean energía solar o electricidad.
"""

# --- CONFIGURACIÓN DEL MODELO ---
# Usamos el modelo que hemos confirmado que existe en tu lista
try:
    model = genai.GenerativeModel(
        'gemini-2.5-flash', 
        system_instruction=instrucciones_sistema
    )
except Exception as e:
    st.error(f"Error al configurar el modelo: {e}")

# --- HISTORIAL DEL CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar mensajes anteriores
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- INTERACCIÓN CON EL USUARIO ---
if prompt := st.chat_input("Describe tu problema o consulta sobre tus placas..."):
    # 1. Mostrar mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Generar respuesta
    try:
        # Preparamos el historial
        chat = model.start_chat(history=[
            {"role": m["role"], "parts": [m["content"]]} 
            for m in st.session_state.messages[:-1]
        ])
        
        response = chat.send_message(prompt)
        text_response = response.text

        # 3. Mostrar respuesta
        with st.chat_message("assistant"):
            st.markdown(text_response)
        
        # 4. Guardar respuesta
        st.session_state.messages.append({"role": "model", "content": text_response})

    except Exception as e:
        st.error(f"Lo siento, ha habido un error de conexión. Inténtalo de nuevo. Error: {e}")
