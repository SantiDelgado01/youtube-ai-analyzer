import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from pysentimiento import create_analyzer
import matplotlib.pyplot as plt
import io

# Configuración de página: 'centered' es la clave para que no se vea como la captura
st.set_page_config(page_title="AI Audience Dashboard", page_icon="📈", layout="centered")

# Forzamos el diseño con CSS inyectado
st.markdown("""
    <style>
    /* Ocultar la barra lateral por completo si existiera */
    [data-testid="stSidebar"] { display: none; }
    
    /* Fondo oscuro y fuentes claras */
    .stApp { background-color: #0e1117; }
    
    /* Estilo del botón principal */
    .stButton>button {
        width: 100%;
        border-radius: 20px;
        background: linear-gradient(45deg, #FF0000, #CC0000);
        color: white;
        height: 3em;
        font-weight: bold;
        border: none;
    }
    
    /* Centrar textos */
    h1, h3, p { text-align: center; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def load_analyzers():
    return create_analyzer(task="sentiment", lang="es"), create_analyzer(task="hate_speech", lang="es")

sentiment_proc, hate_proc = load_analyzers()

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

# --- INTERFAZ ---
st.title("📈 AI Audience Sentiment")
st.write("Introduce los datos para analizar la salud del video")

# Inputs en el cuerpo principal (NO en el sidebar)
api_key_sec = st.secrets.get("YOUTUBE_API_KEY", "")
api_key = st.text_input("YouTube API Key", value=api_key_sec, type="password")
video_url = st.text_input("URL del Video de YouTube")
max_com = st.slider("Cantidad de comentarios", 20, 200, 100)

if st.button("🚀 ANALIZAR VIDEO"):
    if not api_key or not video_url:
        st.error("Faltan datos")
    else:
        try:
            video_id = video_url.split("v=")[-1].split("&")[0]
            yt = build("youtube", "v3", developerKey=api_key)
            
            with st.spinner("Procesando..."):
                res = yt.commentThreads().list(part="snippet", videoId=video_id, maxResults=max_com).execute()
                data = []
                for item in res['items']:
                    txt = item['snippet']['topLevelComment']['snippet']['textDisplay']
                    s = sentiment_proc.predict(txt).output
                    data.append({"Usuario": item['snippet']['topLevelComment']['snippet']['authorDisplayName'], 
                                 "Comentario": txt, "Sentimiento": s})
                
                df = pd.DataFrame(data)
                
                # Métricas
                c1, c2, c3 = st.columns(3)
                c1.metric("Positivos", len(df[df['Sentimiento']=='POS']))
                c2.metric("Neutrales", len(df[df['Sentimiento']=='NEU']))
                c3.metric("Negativos", len(df[df['Sentimiento']=='NEG']))

                # Descarga
                st.write("---")
                xlsx = to_excel_advanced(df)
                st.download_button("📥 Descargar Excel por Pestañas", data=xlsx, 
                                   file_name="analisis.xlsx", mime="application/vnd.ms-excel")
                st.dataframe(df)
        except Exception as e:
            st.error(f"Error: {e}")



