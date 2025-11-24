import streamlit as st
import google.generativeai as genai

st.title("🛠️ Diagnóstico de Modelos Disponibles")

# 1. Configuración API
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    st.success("✅ API Key detectada correctamente.")
except:
    st.error("❌ No se encuentra la API Key.")
    st.stop()

# 2. Listar modelos
st.write("Preguntando a Google qué modelos están activos para ti...")

try:
    found_models = []
    # Recorremos todos los modelos que ofrece Google
    for m in genai.list_models():
        # Filtramos solo los que sirven para generar texto (chat)
        if 'generateContent' in m.supported_generation_methods:
            found_models.append(m.name)
            st.code(m.name) # Muestra el nombre exacto en pantalla
    
    if not found_models:
        st.warning("No se encontraron modelos compatibles con 'generateContent'.")
    else:
        st.success(f"Se han encontrado {len(found_models)} modelos disponibles.")

except Exception as e:
    st.error(f"Error al listar modelos: {e}")
