import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from pysentimiento import create_analyzer
import matplotlib.pyplot as plt
import io

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Audience Intelligence Pro", page_icon="📊", layout="centered")

# 2. CSS PARA DISEÑO PREMIUM (FONDO, BOTONES Y TARJETAS)
st.markdown("""
    <style>
    /* Fondo con degradado y ocultar sidebar */
    .stApp {
        background: radial-gradient(circle at top, #1e2630 0%, #0e1117 100%);
    }
    [data-testid="stSidebar"] { display: none; }
    
    /* Inputs y Sliders modernos */
    .stTextInput>div>div>input {
        background-color: rgba(255, 255, 255, 0.05) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
    }
    
    /* Títulos */
    h1 {
        color: white !important;
        text-shadow: 0px 0px 15px rgba(255, 255, 255, 0.2);
    }

    /* Botón con degradado rojo */
    .stButton>button {
        width: 100%;
        border-radius: 15px !important;
        height: 3.5em;
        background: linear-gradient(90deg, #ff4b4b 0%, #ff1f1f 100%) !important;
        color: white !important;
        font-weight: bold !important;
        border: none !important;
        transition: 0.3s;
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0px 5px 20px rgba(255, 75, 75, 0.4);
    }

    /* Tarjetas de resultados (Glassmorphism) */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        padding: 20px !important;
        border-radius: 20px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. CARGA DE MODELOS DE IA
@st.cache_resource
def load_analyzers():
    return create_analyzer(task="sentiment", lang="es"), create_analyzer(task="hate_speech", lang="es")

sentiment_proc, hate_proc = load_analyzers()

# 4. FUNCIÓN EXCEL AVANZADA (PESTAÑAS Y COLORES)
def to_excel_advanced(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Creamos las 4 pestañas
        df.to_excel(writer, index=False, sheet_name='TODOS')
        df[df['Sentimiento'] == 'POS'].to_excel(writer, index=False, sheet_name='POSITIVOS')
        df[df['Sentimiento'] == 'NEG'].to_excel(writer, index=False, sheet_name='NEGATIVOS')
        df[df['Sentimiento'] == 'NEU'].to_excel(writer, index=False, sheet_name='NEUTRALES')

        workbook = writer.book
        ws = writer.sheets['TODOS']
        
        # Formatos de color para el Excel
        fmt_pos = workbook.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100'}) # Verde
        fmt_neg = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'}) # Rojo
        fmt_neu = workbook.add_format({'bg_color': '#F2F2F2', 'font_color': '#333333'}) # Gris

        # Aplicar colores automáticos en la columna C (Sentimiento)
        ws.conditional_format('C2:C5000', {'type': 'cell', 'criteria': '==', 'value': '"POS"', 'format': fmt_pos})
        ws.conditional_format('C2:C5000', {'type': 'cell', 'criteria': '==', 'value': '"NEG"', 'format': fmt_neg})
        ws.conditional_format('C2:C5000', {'type': 'cell', 'criteria': '==', 'value': '"NEU"', 'format': fmt_neu})
        
    return output.getvalue()

# 5. INTERFAZ DE USUARIO (ENCABEZADO CON TU LOGO)
col_l1, col_l2, col_l3 = st.columns([1, 0.8, 1])
with col_l2:
    try:
        st.image("logo.png", use_container_width=True)
    except:
        st.write("📌 (Sube logo.png a GitHub)")

st.markdown("<h1 style='text-align: center;'>Audience Intelligence</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; opacity: 0.7;'>Auditoría de sentimiento y salud de comunidad con IA</p>", unsafe_allow_html=True)

st.write("---")

# 6. FORMULARIO DE DATOS
with st.container():
    api_key_sec = st.secrets.get("YOUTUBE_API_KEY", "")
    api_key = st.text_input("🔑 Google API Key", value=api_key_sec, type="password")
    video_url = st.text_input("🔗 URL del Video de YouTube", placeholder="Pega el enlace aquí...")
    max_com = st.select_slider("⚡ Cantidad de comentarios a procesar", options=[50, 100, 250, 500], value=100)
    
    st.write("")
    analizar = st.button("🚀 INICIAR ANÁLISIS")

# 7. PROCESAMIENTO Y RESULTADOS
if analizar:
    if not api_key or not video_url:
        st.error("Por favor, ingresa la API Key y la URL del video.")
    else:
        try:
            # Extraer ID del video
            video_id = video_url.split("v=")[-1].split("&")[0]
            yt = build("youtube", "v3", developerKey=api_key)
            
            with st.spinner("🧠 Nuestra IA está analizando los comentarios..."):
                res = yt.commentThreads().list(part="snippet", videoId=video_id, maxResults=max_com).execute()
                
                data = []
                for item in res['items']:
                    txt = item['snippet']['topLevelComment']['snippet']['textDisplay']
                    user = item['snippet']['topLevelComment']['snippet']['authorDisplayName']
                    s = sentiment_proc.predict(txt).output
                    data.append({"Usuario": user, "Comentario": txt, "Sentimiento": s})
                
                df = pd.DataFrame(data)

                # Visualización de Resultados
                st.write("### 📈 Dashboard de Sentimiento")
                m1, m2, m3 = st.columns(3)
                m1.metric("Positivos", len(df[df['Sentimiento']=='POS']), "✅")
                m2.metric("Neutrales", len(df[df['Sentimiento']=='NEU']), "⚪")
                m3.metric("Negativos", len(df[df['Sentimiento']=='NEG']), "❌")

                st.write("---")
                
                # Botón de Descarga
                xlsx = to_excel_advanced(df)
                st.download_button(
                    label="📥 DESCARGAR REPORTE EXCEL PROFESIONAL",
                    data=xlsx,
                    file_name=f"Reporte_IA_{video_id}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

                # Tabla de vista previa
                with st.expander("📝 Ver todos los comentarios analizados"):
                    st.dataframe(df, use_container_width=True)

        except Exception as e:
            st.error(f"Ocurrió un error: {e}")



