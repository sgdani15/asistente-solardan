import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
import tempfile
import os
from datetime import datetime

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
        .stImage { max-width: 300px; }
        /* Estilo para el botón de generar PDF */
        .stButton button {
            width: 100%;
        }
    </style>
""", unsafe_allow_html=True)

# --- INICIALIZACIÓN DE MEMORIA ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploader_key" not in st.session_state:
    st.session_state["uploader_key"] = 0

# --- TUS DATOS Y PRECIOS (CONFIGURACIÓN) ---
ENLACE_CALENDARIO = "https://calendly.com/solardangrancanaria" 
MENSAJE_BIENVENIDA = "¡Hola! Soy la IA de SolarDan. Puedo analizar averías o ayudarte a generar un presupuesto. ¿Qué necesitas?"

# Precios y Medidas (Configurable)
PRECIO_PANEL_450 = 67.0
POTENCIA_PANEL_450 = 450 # Watts
AREA_NECESARIA_POR_PANEL = 4.0 # m2 (Conservador para evitar sombras)

PRECIO_INVERSOR_4KW = 400.0
PRECIO_INVERSOR_6KW = 820.0
PRECIO_INVERSOR_10KW = 1150.0

# Estimación de Estructura, Cableado y Mano de obra
# He puesto unos precios estimados lógicos, puedes cambiarlos aquí:
PRECIO_SOPORTES_CABLES_POR_PANEL = 60.0 # Estructura aluminio + cableado
PRECIO_MANO_OBRA_BASE = 300.0 # Desplazamiento y legalización básica
PRECIO_MANO_OBRA_POR_PANEL = 50.0 # Montaje físico

# --- CLASE PARA GENERAR EL PDF ---
class PresupuestoPDF(FPDF):
    def header(self):
        # Intentamos poner el logo si existe
        if os.path.exists("logo.png"):
            self.image("logo.png", 10, 8, 33)
        self.set_font('helvetica', 'B', 15)
        self.cell(80) # Mover a la derecha
        self.cell(30, 10, 'Estudio de Viabilidad Solar', 0, 0, 'C')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Generado por SolarDan IA - Página {self.page_no()}', 0, 0, 'C')

# --- CONEXIÓN IA ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("⚠️ Error: Falta API Key.")
    st.stop()

# ==========================================
# 🟢 BARRA LATERAL (HERRAMIENTAS)
# ==========================================
with st.sidebar:
    st.header("SolarDan Herramientas")
    
    # --- PESTAÑA 1: CALCULADORA Y PDF ---
    with st.expander("📝 SOLICITAR INFORME PDF", expanded=True):
        st.write("Rellena los datos para obtener tu pre-estudio instantáneo.")
        
        form_nombre = st.text_input("Nombre Completo")
        form_direccion = st.text_input("Dirección de la vivienda")
        form_latitud = st.number_input("Latitud (Ej: 28.123)", format="%.4f", value=28.1000)
        form_area = st.number_input("Metros útiles de azotea (m²)", min_value=10, value=50)
        
        foto_azotea = st.file_uploader("Foto de la azotea (Obligatorio para informe)", type=["jpg", "png", "jpeg"])
        
        if st.button("📄 GENERAR INFORME PDF"):
            if not form_nombre or not foto_azotea:
                st.error("Por favor, pon tu nombre y sube una foto.")
            else:
                # --- LÓGICA MATEMÁTICA ---
                # 1. Calculamos inclinación óptima (Simple: Latitud del lugar)
                inclinacion_optima = form_latitud
                
                # 2. Número de paneles (Area util / 4m2)
                num_paneles = int(form_area / AREA_NECESARIA_POR_PANEL)
                
                # 3. Potencia Total
                potencia_total_w = num_paneles * POTENCIA_PANEL_450
                potencia_total_kw = potencia_total_w / 1000
                
                # 4. Selección de Inversor
                modelo_inversor = ""
                precio_inversor = 0.0
                
                if potencia_total_kw > 10.5:
                    st.warning("⚠️ La instalación supera los 10kW. Requiere estudio manual. Contacta con nosotros.")
                    st.stop()
                elif potencia_total_kw > 6.0:
                    modelo_inversor = "Inversor Híbrido 10kW"
                    precio_inversor = PRECIO_INVERSOR_10KW
                elif potencia_total_kw > 4.0:
                    modelo_inversor = "Inversor Híbrido 6kW"
                    precio_inversor = PRECIO_INVERSOR_6KW
                else:
                    modelo_inversor = "Inversor 4kW"
                    precio_inversor = PRECIO_INVERSOR_4KW
                
                if num_paneles < 4:
                    st.error("El espacio es muy pequeño para una instalación viable mínima.")
                    st.stop()

                # 5. Cálculos de Producción (5.2 HSP x 365 x 0.8 PR)
                produccion_anual = potencia_total_kw * 5.2 * 365 * 0.8
                
                # 6. Presupuesto
                coste_paneles = num_paneles * PRECIO_PANEL_450
                coste_material_var = num_paneles * PRECIO_SOPORTES_CABLES_POR_PANEL
                coste_mano_obra = PRECIO_MANO_OBRA_BASE + (num_paneles * PRECIO_MANO_OBRA_POR_PANEL)
                total_presupuesto = coste_paneles + precio_inversor + coste_material_var + coste_mano_obra

                # --- GENERACIÓN DEL PDF ---
                pdf = PresupuestoPDF()
                pdf.add_page()
                pdf.set_font("helvetica", size=12)
                
                # Datos Cliente
                pdf.cell(0, 10, f"Cliente: {form_nombre}", ln=True)
                pdf.cell(0, 10, f"Dirección: {form_direccion}", ln=True)
                pdf.cell(0, 10, f"Fecha: {datetime.now().strftime('%d/%m/%Y')}", ln=True)
                pdf.ln(10)
                
                # Datos Técnicos
                pdf.set_font("helvetica", 'B', 12)
                pdf.cell(0, 10, "1. ANÁLISIS TÉCNICO", ln=True)
                pdf.set_font("helvetica", size=12)
                pdf.cell(0, 10, f"- Ubicación (Latitud): {form_latitud}", ln=True)
                pdf.cell(0, 10, f"- Inclinación Óptima Recomendada: {inclinacion_optima:.1f} grados", ln=True)
                pdf.cell(0, 10, f"- Área disponible: {form_area} m2", ln=True)
                pdf.cell(0, 10, f"- Potencia Instalable Estimada: {potencia_total_kw:.2f} kWp", ln=True)
                pdf.cell(0, 10, f"- Paneles: {num_paneles} unidades de {POTENCIA_PANEL_450}W", ln=True)
                pdf.cell(0, 10, f"- Producción Anual Estimada: {int(produccion_anual)} kWh/año", ln=True)
                pdf.ln(5)
                
                # Foto
                pdf.set_font("helvetica", 'B', 12)
                pdf.cell(0, 10, "2. ESTADO DE CUBIERTA", ln=True)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                    tmp_file.write(foto_azotea.getvalue())
                    tmp_path = tmp_file.name
                    pdf.image(tmp_path, x=10, w=100) # Imagen insertada
                pdf.ln(5)

                # Desglose Económico
                pdf.add_page()
                pdf.set_font("helvetica", 'B', 12)
                pdf.cell(0, 10, "3. ESTIMACIÓN ECONÓMICA (PRE-PRESUPUESTO)", ln=True)
                pdf.set_font("helvetica", size=11)
                
                # Tabla simple
                col_w = 140
                pdf.cell(col_w, 10, f"Paneles Solares ({num_paneles} x {PRECIO_PANEL_450} eur): {coste_paneles} EUR", border=1, ln=True)
                pdf.cell(col_w, 10, f"{modelo_inversor}: {precio_inversor} EUR", border=1, ln=True)
                pdf.cell(col_w, 10, f"Estructuras, Cableado y Protecciones: {coste_material_var} EUR", border=1, ln=True)
                pdf.cell(col_w, 10, f"Mano de Obra, Legalización y Montaje: {coste_mano_obra} EUR", border=1, ln=True)
                
                pdf.set_font("helvetica", 'B', 12)
                pdf.cell(col_w, 15, f"TOTAL ESTIMADO: {total_presupuesto} EUR", border=1, ln=True)
                
                pdf.ln(10)
                pdf.set_font("helvetica", 'I', 10)
                pdf.multi_cell(0, 5, "NOTA: Este documento es una estimación preliminar basada en datos remotos. El precio final puede variar tras la visita técnica presencial. Los precios no incluyen IGIC/IVA.")
                
                # Generar bytes del PDF
                pdf_bytes = pdf.output(dest='S').encode('latin-1')
                
                # Botón de descarga
                st.success("✅ ¡Informe generado con éxito!")
                st.download_button(
                    label="📥 DESCARGAR INFORME PDF",
                    data=pdf_bytes,
                    file_name=f"Estudio_SolarDan_{form_nombre.replace(' ','_')}.pdf",
                    mime="application/pdf"
                )

    st.markdown("---")
    
    # --- BOTONES DE ACCIÓN RÁPIDA ---
    st.link_button("📅 RESERVAR CITA TÉCNICA", ENLACE_CALENDARIO, type="primary")
    
    if st.button("🗑️ Borrar conversación"):
        st.session_state.messages = []
        st.session_state["uploader_key"] += 1
        st.rerun()
    
    st.caption("© 2025 SolarDan.")


# ==========================================
# 🟢 ÁREA PRINCIPAL (CHAT CON IA)
# ==========================================

# --- CABECERA ---
col1, col2, col3 = st.columns([1, 2, 1]) 
with col2:
    try:
        st.image("logo.png", use_container_width=True) 
    except:
        pass 

st.markdown("<h1 style='text-align: center;'>Asistente Técnico SolarDan</h1>", unsafe_allow_html=True)
st.caption("Asistente IA + Calculadora de Presupuestos")

# --- LÓGICA DE IA ---
instrucciones_sistema = f"""
Eres el asistente técnico de "SolarDan".
1. Si el usuario pide presupuesto, dile: "¡Claro! Por favor, ve al menú lateral izquierdo y rellena el formulario 'SOLICITAR INFORME PDF' para obtener un estudio detallado al instante."
2. Si tiene dudas técnicas, respóndelas.
3. Si hay peligro, manda apagar todo.
4. Si la avería es grave, cita: {ENLACE_CALENDARIO}
"""

# Historial
if len(st.session_state.messages) == 0:
    st.session_state.messages.append({"role": "model", "content": MENSAJE_BIENVENIDA})

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if isinstance(message["content"], list):
             for part in message["content"]:
                 if isinstance(part, str): st.markdown(part)
        else:
            st.markdown(message["content"])

# --- INPUT DE FOTOS (ENCIMA DEL CHAT) ---
with st.expander("📸 Adjuntar imagen a la consulta", expanded=False):
    uploaded_file = st.file_uploader(
        "Sube tu foto para la IA:", 
        type=["jpg", "png", "jpeg"], 
        key=f"uploader_{st.session_state['uploader_key']}" 
    )
    if uploaded_file:
        st.image(uploaded_file, width=150)

# --- INPUT DE TEXTO ---
if prompt := st.chat_input("Escribe tu consulta..."):
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

    try:
        with st.spinner("SolarDan IA pensando..."):
            if uploaded_file:
                response = model.generate_content(content_to_send)
            else:
                chat = model.start_chat(history=[
                    {"role": m["role"], "parts": [m["content"]]} 
                    for m in st.session_state.messages[:-1] 
                    if isinstance(m["content"], str) and m["content"] != MENSAJE_BIENVENIDA
                ])
                response = chat.send_message(prompt)

        text_response = response.text
        with st.chat_message("assistant"):
            st.markdown(text_response)
        st.session_state.messages.append({"role": "model", "content": text_response})
        
        if uploaded_file:
            st.session_state["uploader_key"] += 1
            st.rerun()

    except Exception as e:
        st.error(f"Error: {e}")
