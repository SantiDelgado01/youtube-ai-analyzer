import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from pysentimiento import create_analyzer
import matplotlib.pyplot as plt
import io

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Audience Intelligence Pro", page_icon="📊", layout="centered")

# 2. CSS PARA DISEÑO PREMIUM (SIN LOGO, MÁXIMA LIMPIEZA)
st.markdown("""
    <style>
    /* Fondo con degradado profundo */
    .stApp {
        background: radial-gradient(circle at top, #1e2630 0%, #0e1117 100%);
    }
    [data-testid="stSidebar"] { display: none; }
    
    /* Títulos con tipografía moderna */
    h1 {
        color: white !important;
        text-align: center;
        font-weight: 800 !important;
        padding-top: 20px;
        letter-spacing: -1px;
    }
    p {
        text-align: center;
        color: #808495 !important;
    }

    /* Inputs estilizados */
    .stTextInput>div>div>input {
        background-color: rgba(255, 255, 255, 0.05) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
    }
    
    /* Botón de acción principal */
    .stButton>button {
        width: 100%;
        border-radius: 12px !important;
        height: 3.8em;
        background: linear-gradient(90deg, #FF4B4B 0%, #D83B3B 100%) !important;
        color: white !important;
        font-weight: bold !important;
        border: none !important;
        box-shadow: 0px 4px 15px rgba(255, 75, 75, 0.2);
    }

    /* Tarjetas de Métricas */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        padding: 20px !important;
        border-radius: 16px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. CARGA DE MODELOS
@st.cache_resource
def load_analyzers():
    return create_analyzer(task="sentiment", lang="es"), create_analyzer(task="hate_speech", lang="es")

sentiment_proc, hate_proc = load_analyzers()

# 4. EXCEL CON PESTAÑAS Y COLORES
def to_excel_advanced(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='TODOS')
        df[df['Sentimiento'] == 'POS'].to_excel(writer, index=False, sheet_name='POSITIVOS')
        df[df['Sentimiento'] == 'NEG'].to_excel(writer, index=False, sheet_name='NEGATIVOS')
        df[df['Sentimiento'] == 'NEU'].to_excel(writer, index=False, sheet_name='NEUTRALES')

        workbook = writer.book
        ws = writer.sheets['TODOS']
        fmt_pos = workbook.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100'})
        fmt_neg = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
        fmt_neu = workbook.add_format({'bg_color': '#F2F2F2', 'font_color': '#333333'})

        ws.conditional_format('C2:C5000', {'type': 'cell', 'criteria': '==', 'value': '"POS"', 'format': fmt_pos})
        ws.conditional_format('C2:C5000', {'type': 'cell', 'criteria': '==', 'value': '"NEG"', 'format': fmt_neg})
        ws.conditional_format('C2:C5000', {'type': 'cell', 'criteria': '==', 'value': '"NEU"', 'format': fmt_neu})
    return output.getvalue()

# 5. INTERFAZ LIMPIA
st.markdown("<h1>Audience Intelligence Pro</h1>", unsafe_allow_html=True)
st.markdown("<p>Análisis estratégico de comunidad mediante Inteligencia Artificial</p>", unsafe_allow_html=True)

st.write("") # Espaciador

with st.container():
    api_key_sec = st.secrets.get("YOUTUBE_API_KEY", "")
    api_key = st.text_input("🔑 Google Cloud API Key", value=api_key_sec, type="password")
    video_url = st.text_input("🔗 YouTube Video URL", placeholder="https://www.youtube.com/watch?v=...")
    max_com = st.select_slider("⚡ Volumen de datos", options=[50, 100, 250, 500], value=100)
    
    st.write("")
    analizar = st.button("ANALIZAR AHORA")

st.divider()

# 6. PROCESAMIENTO
if analizar:
    if not api_key or not video_url:
        st.error("Datos incompletos.")
    else:
        try:
            video_id = video_url.split("v=")[-1].split("&")[0]
            yt = build("youtube", "v3", developerKey=api_key)
            
            with st.spinner("Procesando sentimientos..."):
                res = yt.commentThreads().list(part="snippet", videoId=video_id, maxResults=max_com).execute()
                data = [{"Usuario": i['snippet']['topLevelComment']['snippet']['authorDisplayName'], 
                         "Comentario": i['snippet']['topLevelComment']['snippet']['textDisplay'], 
                         "Sentimiento": sentiment_proc.predict(i['snippet']['topLevelComment']['snippet']['textDisplay']).output} 
                        for i in res['items']]
                df = pd.DataFrame(data)

                # DASHBOARD
                c1, c2, c3 = st.columns(3)
                c1.metric("Positivos", len(df[df['Sentimiento']=='POS']), "✅")
                c2.metric("Neutrales", len(df[df['Sentimiento']=='NEU']), "⚪")
                c3.metric("Negativos", len(df[df['Sentimiento']=='NEG']), "❌")

                st.write("")
                xlsx = to_excel_advanced(df)
                st.download_button("📥 DESCARGAR REPORTE ESTRATÉGICO", xlsx, f"Analisis_{video_id}.xlsx", "application/vnd.ms-excel")
                
                with st.expander("Ver tabla de datos bruta"):
                    st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"Error: {e}")



