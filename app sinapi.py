import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from pysentimiento import create_analyzer
import matplotlib.pyplot as plt
import io

# 1. CONFIGURACIÓN DE PÁGINA PROFESIONAL
st.set_page_config(page_title="Audience AI Pro", page_icon="📊", layout="centered")

# 2. CSS AVANZADO (DISEÑO PREMIUM)
st.markdown("""
    <style>
    /* Fondo con degradado profesional */
    .stApp {
        background: radial-gradient(circle at top, #1e2630 0%, #0e1117 100%);
    }
    
    /* Ocultar sidebar y menús para limpieza total */
    [data-testid="stSidebar"] { display: none; }
    
    /* Contenedor principal de inputs */
    .stTextInput>div>div>input, .stSlider>div {
        background-color: rgba(255, 255, 255, 0.05) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
    }

    /* Títulos con sombra y glow */
    h1 {
        color: white !important;
        text-shadow: 0px 0px 15px rgba(255, 255, 255, 0.2);
        font-family: 'Inter', sans-serif;
    }

    /* Botón Moderno con Efecto Hover */
    .stButton>button {
        width: 100%;
        border-radius: 15px !important;
        height: 3.5em;
        background: linear-gradient(90deg, #ff4b4b 0%, #ff1f1f 100%) !important;
        color: white !important;
        font-weight: bold !important;
        border: none !important;
        transition: all 0.3s ease-in-out;
        box-shadow: 0px 4px 15px rgba(255, 75, 75, 0.3);
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0px 6px 20px rgba(255, 75, 75, 0.5);
    }

    /* Tarjetas de Métricas (Glassmorphism) */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        padding: 20px !important;
        border-radius: 20px !important;
        backdrop-filter: blur(10px);
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def load_analyzers():
    return create_analyzer(task="sentiment", lang="es"), create_analyzer(task="hate_speech", lang="es")

sentiment_proc, hate_proc = load_analyzers()

# --- FUNCIÓN EXCEL (Colores y Pestañas) ---
def to_excel_advanced(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='TODOS')
        df[df['Sentimiento'] == 'POS'].to_excel(writer, index=False, sheet_name='POSITIVOS')
        df[df['Sentimiento'] == 'NEG'].to_excel(writer, index=False, sheet_name='NEGATIVOS')
        df[df['Sentimiento'] == 'NEU'].to_excel(writer, index=False, sheet_name='NEUTRALES')

        workbook = writer.book
        ws = writer.sheets['TODOS']
        
        # Estilos de celdas
        fmt_pos = workbook.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100'})
        fmt_neg = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
        fmt_neu = workbook.add_format({'bg_color': '#F2F2F2', 'font_color': '#333333'})

        ws.conditional_format('C2:C5000', {'type': 'cell', 'criteria': '==', 'value': '"POS"', 'format': fmt_pos})
        ws.conditional_format('C2:C5000', {'type': 'cell', 'criteria': '==', 'value': '"NEG"', 'format': fmt_neg})
        ws.conditional_format('C2:C5000', {'type': 'cell', 'criteria': '==', 'value': '"NEU"', 'format': fmt_neu})
    return output.getvalue()

# --- INTERFAZ CENTRALIZADA ---
st.markdown("<h1 style='text-align: center;'>💎 Audience Intelligence</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; opacity: 0.7;'>Analítica avanzada con IA para Creadores y Marcas</p>", unsafe_allow_html=True)

st.write("") # Espaciador

# Sección de entradas
with st.container():
    key_secret = st.secrets.get("YOUTUBE_API_KEY", "")
    api_key = st.text_input("🔑 Google API Key", value=key_secret, type="password")
    video_url = st.text_input("🔗 URL del Video", placeholder="https://www.youtube.com/watch?v=...")
    max_com = st.select_slider("⚡ Precisión del Análisis (Comentarios)", options=[50, 100, 250, 500], value=100)
    
    st.write("")
    btn_analizar = st.button("INICIAR AUDITORÍA IA")

st.divider()

# --- LÓGICA DE PROCESAMIENTO ---
if btn_analizar:
    if not api_key or not video_url:
        st.error("⚠️ Por favor completa los campos requeridos.")
    else:
        try:
            video_id = video_url.split("v=")[-1].split("&")[0]
            yt = build("youtube", "v3", developerKey=api_key)
            
            with st.status("🔍 Escaneando audiencia...", expanded=True) as status:
                res = yt.commentThreads().list(part="snippet", videoId=video_id, maxResults=max_com).execute()
                data = []
                for item in res['items']:
                    txt = item['snippet']['topLevelComment']['snippet']['textDisplay']
                    s = sentiment_proc.predict(txt).output
                    data.append({
                        "Usuario": item['snippet']['topLevelComment']['snippet']['authorDisplayName'], 
                        "Comentario": txt, 
                        "Sentimiento": s
                    })
                df = pd.DataFrame(data)
                status.update(label="✅ Análisis Completado", state="complete", expanded=False)

            # Dashboard de Resultados
            st.markdown("### 📊 Salud de la Comunidad")
            m1, m2, m3 = st.columns(3)
            m1.metric("Positivos ✅", len(df[df['Sentimiento']=='POS']))
            m2.metric("Neutrales ⚪", len(df[df['Sentimiento']=='NEU']))
            m3.metric("Negativos ❌", len(df[df['Sentimiento']=='NEG']))

            # Descarga Premium
            st.write("")
            xlsx_data = to_excel_advanced(df)
            st.download_button(
                label="📥 DESCARGAR REPORTE PROFESIONAL (EXCEL)",
                data=xlsx_data,
                file_name=f"Informe_IA_{video_id}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            with st.expander("Ver desglose de datos"):
                st.dataframe(df, use_container_width=True)

        except Exception as e:
            st.error(f"Error de conexión: {e}")



