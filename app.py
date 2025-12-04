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
MENSAJE_BIENVENIDA = "¡Hola! Soy la IA de SolarDan. Puedo analizar averías (incluso con fotos) o ayudarte a generar un presupuesto. ¿Qué necesitas?"

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

# --- CLASE PARA GENERAR EL PDF ---
class PresupuestoPDF(FPDF):
    def header(self):
        # 1. LOGO
        if os.path.exists("logo_pdf.png"):
            self.image("logo_pdf.png", 10, 10, 35)
        elif os.path.exists("logo.png"):
            self.image("logo.png", 10, 10, 35)
            
        # 2. TÍTULO
        self.set_font('helvetica', 'B', 16)
        self.set_xy(50, 18) 
        self.cell(0, 10, 'Estudio de Viabilidad Solar', border=0, ln=1, align='R')
        
        # 3. SUBTÍTULO
        self.set_font('helvetica', 'I', 10)
        self.set_x(50) 
        self.cell(0, 5, 'Informe Técnico Preliminar - SolarDan', border=0, ln=1, align='R')

        # 4. LÍNEA
        self.set_draw_color(255, 140, 0) # Naranja
        self.set_line_width(0.5)
        self.line(10, 38, 200, 38)
        self.ln(25)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Documento generado por IA - SolarDan - Página {self.page_no()}', 0, 0, 'C')

# --- CONEXIÓN IA ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    # Modelo actualizado y potente
    model = genai.GenerativeModel('gemini-2.5-flash')
except:
    st.error("⚠️ Error: Problema con la API Key o el modelo.")
    st.stop()

# ==========================================
# 🟢 BARRA LATERAL (HERRAMIENTAS)
# ==========================================
with st.sidebar:
    st.header("SolarDan Herramientas")
    
    # --- SECCIÓN 1: GENERADOR PDF ---
    with st.expander("📝 SOLICITAR INFORME PDF", expanded=False):
        st.write("Datos para el estudio:")
        
        form_nombre = st.text_input("Nombre Completo")
        form_direccion = st.text_input("Dirección")
        
        form_potencia_actual = st.number_input("Potencia Contratada (kW)", min_value=1.0, value=4.6, step=0.1)
        form_orientacion_azotea = st.selectbox("Orientación de la azotea", 
                                               ["Sur (Ideal)", "Sureste", "Suroeste", "Este", "Oeste", "Norte"])

        form_latitud = st.number_input("Latitud", format="%.4f", value=28.1000)
        form_area = st.number_input("Metros de azotea (m²)", min_value=10, value=50)
        foto_azotea = st.file_uploader("Foto azotea", type=["jpg", "png", "jpeg"])
        
        if st.button("📄 GENERAR INFORME"):
            if not form_nombre or not foto_azotea:
                st.error("Faltan datos (Nombre o Foto).")
            else:
                # CÁLCULOS
                num_paneles = int(form_area / AREA_NECESARIA_POR_PANEL)
                potencia_total_w = num_paneles * POTENCIA_PANEL_450
                potencia_total_kw = potencia_total_w / 1000
                
                aviso_sobredimension = ""
                if potencia_total_kw > (form_potencia_actual * 1.5):
                    aviso_sobredimension = "NOTA: La capacidad de la cubierta es muy superior a su potencia contratada. Se recomienda ajustar la instalacion al consumo real."
                
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
                    
                    def clean_text(text):
                        return text.encode('latin-1', 'replace').decode('latin-1')

                    # Datos
                    pdf.set_font("helvetica", size=11)
                    pdf.cell(0, 6, f"Cliente: {clean_text(form_nombre)}", ln=True)
                    pdf.cell(0, 6, f"Direccion: {clean_text(form_direccion)}", ln=True)
                    pdf.cell(0, 6, f"Fecha: {datetime.now().strftime('%d/%m/%Y')}", ln=True)
                    pdf.ln(5)
                    
                    # 1. ANÁLISIS
                    pdf.set_font("helvetica", 'B', 12)
                    pdf.set_fill_color(240, 240, 240)
                    pdf.cell(0, 10, "  1. ANALISIS TECNICO Y SITUACION", ln=True, fill=True)
                    pdf.set_font("helvetica", size=11)
                    pdf.ln(2)
                    
                    pdf.cell(0, 7, f"   - Potencia Contratada Actual: {form_potencia_actual} kW", ln=True)
                    pdf.set_font("helvetica", 'B', 11)
                    pdf.cell(0, 7, f"   - Potencia Fotovoltaica Instalable: {potencia_total_kw:.2f} kWp", ln=True)
                    pdf.set_font("helvetica", size=11)
                    
                    if aviso_sobredimension:
                        pdf.set_text_color(220, 50, 50) 
                        pdf.set_font("helvetica", 'I', 9)
                        pdf.multi_cell(0, 5, f"     {clean_text(aviso_sobredimension)}")
                        pdf.set_text_color(0, 0, 0) 
                        pdf.set_font("helvetica", size=11)

                    pdf.ln(2)
                    pdf.cell(0, 7, f"   - Orientacion Cubierta Cliente: {clean_text(form_orientacion_azotea)}", ln=True)
                    pdf.cell(0, 7, f"   - Estrategia de Diseno: Estructuras orientadas al SUR MAGNETICO", ln=True)
                    pdf.cell(0, 7, f"   - Inclinacion Optima (Latitud): {form_latitud} grados", ln=True)
                    
                    pdf.ln(2)
                    pdf.cell(0, 7, f"   - Area disponible: {form_area} m2", ln=True)
                    pdf.cell(0, 7, f"   - Produccion Estimada: {int(produccion_anual)} kWh/anual", ln=True)
                    pdf.ln(5)
                    
                    # 2. FOTO
                    pdf.set_font("helvetica", 'B', 12)
                    pdf.cell(0, 10, "  2. ESTADO DE CUBIERTA", ln=True, fill=True)
                    pdf.ln(5)
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                        tmp_file.write(foto_azotea.getvalue())
                        tmp_path = tmp_file.name
                        pdf.image(tmp_path, x=55, w=100)
                    pdf.ln(5)

                    # 3. ECONÓMICO
                    pdf.add_page()
                    pdf.set_font("helvetica", 'B', 12)
                    pdf.cell(0, 10, "  3. ESTIMACION ECONOMICA", ln=True, fill=True)
                    pdf.set_font("helvetica", size=11)
                    pdf.ln(5)
                    col_w = 140
                    
                    pdf.cell(col_w, 12, f"  Paneles Solares ({num_paneles} uds x 450W): {coste_paneles} EUR", border=1, ln=True)
                    pdf.cell(col_w, 12, f"  {modelo_inversor}: {precio_inversor} EUR", border=1, ln=True)
                    pdf.cell(col_w, 12, f"  Estructuras y Cableado: {coste_material_var} EUR", border=1, ln=True)
                    pdf.cell(col_w, 12, f"  Mano de Obra y Legalizacion: {coste_mano_obra} EUR", border=1, ln=True)
                    
                    pdf.set_font("helvetica", 'B', 12)
                    pdf.set_fill_color(255, 250, 205)
                    pdf.cell(col_w, 15, f"  TOTAL ESTIMADO: {total_presupuesto} EUR", border=1, ln=True, fill=True)
                    
                    pdf.ln(5)
                    pdf.set_font("helvetica", 'I', 9)
                    pdf.multi_cell(0, 5, "NOTA: Estudio valido salvo error u omision. Precios sin impuestos (IGIC/IVA). La orientacion final de las placas se ajustara al Sur Magnetico para maximizar produccion.")

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

# --- LÓGICA IA (CONFIGURACIÓN ESTRICTA DE SEGURIDAD) ---
instrucciones_sistema = f"""
Eres el asistente técnico de seguridad de "SolarDan".

PROTOCOLO DE ACTUACIÓN OBLIGATORIO:

1. **ANTE FUEGO, HUMO O QUEMADURAS (PRIORIDAD ABSOLUTA)**:
   - Tu tono debe ser DE ALARMA Y SERIEDAD. Prohibido usar entusiasmo ("¡Vaya!", "¡Sí!").
   - Escribe en negrita: "**⚠️ PELIGRO CRÍTICO DETECTADO**".
   - Ordena: "Aléjate inmediatamente de la instalación. Riesgo de electrocución e incendio."
   - Ordena: "Si es seguro hacerlo, desconecta la corriente general de la vivienda. Si el fuego está avanzado, llama al 112."
   - FINALIZA SIEMPRE CON: "Contacta urgentemente con nuestro servicio técnico prioritario: {ENLACE_CALENDARIO}"

2. **ANTE OTRAS AVERÍAS O DUDAS**:
   - Si la imagen muestra roturas físicas, cables pelados o errores complejos, NO des instrucciones de reparación casera.
   - Di: "Esto requiere intervención técnica profesional para evitar daños mayores." y facilita el enlace del calendario.
   - Solo da consejos técnicos si es algo de limpieza o configuración básica de software.

3. **SOLICITUD DE PRESUPUESTOS**:
   - Si piden precio, redirige al formulario del menú lateral ("SOLICITAR INFORME PDF").

No hables de nada que no sea solar. Sé conciso y profesional.
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
                # Interacción única para imágenes con el protocolo estricto
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
