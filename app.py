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

# --- TUS DATOS Y PRECIOS ---
ENLACE_CALENDARIO = "https://calendly.com/solardangrancanaria" 
MENSAJE_BIENVENIDA = "¡Hola! Soy la IA de SolarDan. Puedo analizar averías o ayudarte a generar un presupuesto. ¿Qué necesitas?"

# Precios y Medidas
PRECIO_PANEL_450 = 67.0
POTENCIA_PANEL_450 = 450 
AREA_NECESARIA_POR_PANEL = 4.0 

PRECIO_INVERSOR_4KW = 400.0
PRECIO_INVERSOR_6KW = 820.0
PRECIO_INVERSOR_10KW = 1150.0

PRECIO_SOPORTES_CABLES_POR_PANEL = 60.0
PRECIO_MANO_OBRA_BASE = 300.0
PRECIO_MANO_OBRA_POR_PANEL = 50.0 

# --- CLASE PARA GENERAR EL PDF (DISEÑO MEJORADO) ---
class PresupuestoPDF(FPDF):
    def header(self):
        # 1. LOGO (Izquierda)
        # Usamos coordenadas X=10, Y=10 y un ancho de 35mm
        if os.path.exists("logo_pdf.png"):
            self.image("logo_pdf.png", 10, 10, 35)
        elif os.path.exists("logo.png"):
            self.image("logo.png", 10, 10, 35)
            
        # 2. TÍTULO (Derecha y más abajo)
        self.set_font('helvetica', 'B', 16)
        # Movemos el cursor a X=50, Y=18 para que no pise el logo y baje un poco
        self.set_xy(50, 18) 
        # 'R' alinea el texto a la derecha de la página
        self.cell(0, 10, 'Estudio de Viabilidad Solar', border=0, ln=1, align='R')
        
        # 3. SUBTÍTULO O FECHA (Opcional, debajo del título)
        self.set_font('helvetica', 'I', 10)
        self.set_x(50) # Volvemos a posicionarnos a la derecha del logo
        self.cell(0, 5, 'Informe Técnico Preliminar - SolarDan', border=0, ln=1, align='R')

        # 4. LÍNEA SEPARADORA (Decoración)
        self.set_draw_color(255, 140, 0) # Naranja oscuro (RGB)
        self.set_line_width(0.5)
        self.line(10, 38, 200, 38) # Línea horizontal de lado a lado (Y=38)

        # 5. ESPACIO DE SEGURIDAD
        self.ln(25) # Bajamos 25 unidades para que el contenido empiece limpio

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(128, 128, 128) # Gris
        self.cell(0, 10, f'Documento generado por IA - SolarDan - Página {self.page_no()}', 0, 0, 'C')

# --- CONEXIÓN IA ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("⚠️ Error: Falta API Key.")
    st.stop()

# ==========================================
# 🟢 BARRA LATERAL (ORGANIZADA)
# ==========================================
with st.sidebar:
    st.header("SolarDan Herramientas")
    
    # --- SECCIÓN 1: GENERADOR PDF ---
    with st.expander("📝 SOLICITAR INFORME PDF", expanded=False):
        st.write("Rellena para obtener estudio instantáneo.")
        
        form_nombre = st.text_input("Nombre Completo")
        form_direccion = st.text_input("Dirección")
        form_latitud = st.number_input("Latitud", format="%.4f", value=28.1000)
        form_area = st.number_input("Metros de azotea (m²)", min_value=10, value=50)
        foto_azotea = st.file_uploader("Foto azotea", type=["jpg", "png", "jpeg"])
        
        if st.button("📄 GENERAR INFORME"):
            if not form_nombre or not foto_azotea:
                st.error("Faltan datos (Nombre o Foto).")
            else:
                # CÁLCULOS
                inclinacion_optima = form_latitud
                num_paneles = int(form_area / AREA_NECESARIA_POR_PANEL)
                potencia_total_w = num_paneles * POTENCIA_PANEL_450
                potencia_total_kw = potencia_total_w / 1000
                
                modelo_inversor = ""
                precio_inversor = 0.0
                
                if potencia_total_kw > 10.5:
                    st.warning("Más de 10kW requiere estudio manual.")
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
                    st.error("Espacio insuficiente.")
                    st.stop()

                produccion_anual = potencia_total_kw * 5.2 * 365 * 0.8
                coste_paneles = num_paneles * PRECIO_PANEL_450
                coste_material_var = num_paneles * PRECIO_SOPORTES_CABLES_POR_PANEL
                coste_mano_obra = PRECIO_MANO_OBRA_BASE + (num_paneles * PRECIO_MANO_OBRA_POR_PANEL)
                total_presupuesto = coste_paneles + precio_inversor + coste_material_var + coste_mano_obra

                # PDF
                try:
                    pdf = PresupuestoPDF()
                    pdf.add_page()
                    pdf.set_font("helvetica", size=12)
                    
                    def clean_text(text):
                        return text.encode('latin-1', 'replace').decode('latin-1')

                    pdf.cell(0, 10, f"Cliente: {clean_text(form_nombre)}", ln=True)
                    pdf.cell(0, 10, f"Direccion: {clean_text(form_direccion)}", ln=True)
                    pdf.cell(0, 10, f"Fecha: {datetime.now().strftime('%d/%m/%Y')}", ln=True)
                    pdf.ln(10)
                    
                    pdf.set_font("helvetica", 'B', 12)
                    pdf.set_fill_color(240, 240, 240) # Fondo gris clarito para títulos
                    pdf.cell(0, 10, "  1. ANALISIS TECNICO", ln=True, fill=True)
                    pdf.set_font("helvetica", size=12)
                    pdf.ln(2)
                    pdf.cell(0, 8, f"   - Ubicacion: {form_latitud}", ln=True)
                    pdf.cell(0, 8, f"   - Potencia Estimada: {potencia_total_kw:.2f} kWp", ln=True)
                    pdf.cell(0, 8, f"   - Paneles: {num_paneles} x {POTENCIA_PANEL_450}W", ln=True)
                    pdf.cell(0, 8, f"   - Produccion: {int(produccion_anual)} kWh/anual", ln=True)
                    pdf.ln(5)
                    
                    pdf.set_font("helvetica", 'B', 12)
                    pdf.cell(0, 10, "  2. ESTADO DE CUBIERTA", ln=True, fill=True)
                    pdf.ln(5)
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                        tmp_file.write(foto_azotea.getvalue())
                        tmp_path = tmp_file.name
                        # Centramos la imagen
                        pdf.image(tmp_path, x=55, w=100) 
                    pdf.ln(5)

                    pdf.add_page()
                    pdf.set_font("helvetica", 'B', 12)
                    pdf.cell(0, 10, "  3. ESTIMACION ECONOMICA", ln=True, fill=True)
                    pdf.set_font("helvetica", size=11)
                    pdf.ln(5)
                    col_w = 140
                    # Altura de celda un poco mayor (12)
                    pdf.cell(col_w, 12, f"  Paneles Solares: {coste_paneles} EUR", border=1, ln=True)
                    pdf.cell(col_w, 12, f"  {modelo_inversor}: {precio_inversor} EUR", border=1, ln=True)
                    pdf.cell(col_w, 12, f"  Estructuras y Cableado: {coste_material_var} EUR", border=1, ln=True)
                    pdf.cell(col_w, 12, f"  Mano de Obra y Legalizacion: {coste_mano_obra} EUR", border=1, ln=True)
                    
                    pdf.set_font("helvetica", 'B', 12)
                    pdf.set_fill_color(255, 250, 205) # Fondo amarillo pálido para el total
                    pdf.cell(col_w, 15, f"  TOTAL: {total_presupuesto} EUR", border=1, ln=True, fill=True)
                    
                    pdf_bytes = bytes(pdf.output()) 
                    st.success("✅ ¡Informe generado!")
                    st.download_button("📥 DESCARGAR PDF", pdf_bytes, f"Estudio_{form_nombre.replace(' ','_')}.pdf", "application/pdf")
                except Exception as e:
                    st.error(f"Error PDF: {e}")

    st.markdown("---")
    
    # --- SECCIÓN 2: CONTACTO Y CITAS ---
    st.header("Asistencia Técnica")
    st.info("¿Avería compleja? Agenda una visita con nuestros expertos.")
    st.link_button("📅 RESERVAR CITA AHORA", ENLACE_CALENDARIO, type="primary")
    
    st.markdown("---")
    st.write("**Contacto Directo:**")
    st.write("📧 info@solardan.com")
    
    st.markdown("---")
    if st.button("🗑️ Borrar conversación"):
        st.session_state.messages = []
        st.session_state["uploader_key"] += 1
        st.rerun()
    
    st.caption("© 2025 SolarDan.")

# ==========================================
# 🟢 ÁREA PRINCIPAL
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

# --- LÓGICA IA ---
instrucciones_sistema = f"""
Eres el asistente técnico de "SolarDan".
1. Si el usuario pide presupuesto, dile: "¡Claro! Ve al menú lateral izquierdo, sección 'SOLICITAR INFORME PDF' para tu estudio."
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

# --- INPUT FOTOS ---
with st.expander("📸 Adjuntar imagen a la consulta", expanded=False):
    uploaded_file = st.file_uploader(
        "Sube tu foto para la IA:", 
        type=["jpg", "png", "jpeg"], 
        key=f"uploader_{st.session_state['uploader_key']}" 
    )
    if uploaded_file:
        st.image(uploaded_file, width=150)

# --- INPUT TEXTO ---
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
        
        if uploaded_file:
            st.session_state["uploader_key"] += 1
            st.rerun()

    except Exception as e:
        st.error(f"Error: {e}")
