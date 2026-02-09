import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from pysentimiento import create_analyzer
import seaborn as sns
import matplotlib.pyplot as plt
import io

# 1. CONFIGURACIÓN VISUAL
st.set_page_config(page_title="AI Audience Insights", page_icon="📈", layout="centered")

# CSS para forzar el look moderno y ocultar menús innecesarios
st.markdown("""
    <style>
    /* Fondo y texto */
    .stApp { background-color: #0e1117; }
    h1, h2, h3, p { color: white !important; text-align: center; }
    
    /* Estilo del contenedor de entrada */
    .stTextInput>div>div>input {
        background-color: #1e2129 !important;
        color: white !important;
        border: 1px solid #3e424b !important;
        border-radius: 10px !important;
    }
    
    /* Botón principal estilo 'YouTube Premium' */
    .stButton>button {
        width: 100%;
        border-radius: 25px !important;
        height: 3.5em;
        background: linear-gradient(90deg, #FF0000 0%, #CC0000 100%) !important;
        color: white !important;
        font-weight: bold !important;
        border: none !important;
        margin-top: 20px;
    }
    
    /* Métricas */
    [data-testid="stMetric"] {
        background-color: #1e2129;
        border: 1px solid #31333f;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def load_analyzers():
    return create_analyzer(task="sentiment", lang="es"), create_analyzer(task="hate_speech", lang="es")

sentiment_proc, hate_proc = load_analyzers()

# --- FUNCIÓN EXCEL AVANZADA (Pestañas y Colores) ---
def to_excel_advanced(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='TODOS')
        df[df['Sentimiento'] == 'POS'].to_excel(writer, index=False, sheet_name='POSITIVOS')
        df[df['Sentimiento'] == 'NEG'].to_excel(writer, index=False, sheet_name='NEGATIVOS')
        df[df['Sentimiento'] == 'NEU'].to_excel(writer, index=False, sheet_name='NEUTRALES')

        workbook  = writer.book
        ws = writer.sheets['TODOS']
        
        # Formatos profesionales
        fmt_pos = workbook.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100'})
        fmt_neg = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
        fmt_neu = workbook.add_format({'bg_color': '#F2F2F2', 'font_color': '#333333'})
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#1a1a1a', 'font_color': 'white'})

        for col_num, value in enumerate(df.columns.values):
            ws.write(0, col_num, value, header_fmt)
            ws.set_column(col_num, col_num, 35)

        ws.conditional_format('C2:C5000', {'type': 'cell', 'criteria': '==', 'value': '"POS"', 'format': fmt_pos})
        ws.conditional_format('C2:C5000', {'type': 'cell', 'criteria': '==', 'value': '"NEG"', 'format': fmt_neg})
        ws.conditional_format('C2:C5000', {'type': 'cell', 'criteria': '==', 'value': '"NEU"', 'format': fmt_neu})

    return output.getvalue()

# --- INTERFAZ CENTRAL ---
st.image("https://cdn-icons-png.flaticon.com/512/1384/1384060.png", width=80) # Logo central
st.title("AI Audience Insights")
st.markdown("Analiza la percepción de tu audiencia con Inteligencia Artificial")

# Espaciador
st.write("")

# Formulario Central
with st.container():
    api_key_sec = st.secrets.get("YOUTUBE_API_KEY", "")
    api_key = st.text_input("🔑 YouTube API Key", value=api_key_sec, type="password")
    video_url = st.text_input("🔗 Enlace del Video", placeholder="Pega el link aquí...")
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        max_com = st.select_slider("Muestra de comentarios", options=[50, 100, 250, 500], value=100)
    with col_s2:
        st.write("") # Espacio estético
        st.write("Selecciona el volumen de datos a procesar")

    analizar = st.button("ANALIZAR AUDIENCIA")

st.write("---")

# --- PROCESAMIENTO Y RESULTADOS ---
if analizar:
    if not api_key or not video_url:
        st.error("Debes completar la API Key y la URL.")
    else:
        try:
            video_id = video_url.split("v=")[-1].split("&")[0]
            yt = build("youtube", "v3", developerKey=api_key)
            
            with st.spinner("🧠 Nuestra IA está analizando cada comentario..."):
                res = yt.commentThreads().list(part="snippet", videoId=video_id, maxResults=max_com).execute()
                
                data = []
                for item in res['items']:
                    txt = item['snippet']['topLevelComment']['snippet']['textDisplay']
                    user = item['snippet']['topLevelComment']['snippet']['authorDisplayName']
                    s = sentiment_proc.predict(txt).output
                    h = "Tóxico" if len(hate_proc.predict(txt).output) > 0 else "Limpio"
                    data.append({"Usuario": user, "Comentario": txt, "Sentimiento": s, "Seguridad": h})
                
                df = pd.DataFrame(data)

                # DASHBOARD DE RESULTADOS (Sección moderna)
                st.markdown("### 📊 Resultado del Análisis")
                m1, m2, m3 = st.columns(3)
                m1.metric("Positivos", len(df[df['Sentimiento']=='POS']))
                m2.metric("Neutrales", len(df[df['Sentimiento']=='NEU']))
                m3.metric("Negativos", len(df[df['Sentimiento']=='NEG']))

                # Gráfico circular moderno
                st.write("")
                fig, ax = plt.subplots(figsize=(6, 4), facecolor='#0e1117')
                colors = ['#2ecc71', '#95a5a6', '#e74c3c']
                df['Sentimiento'].value_counts().plot(kind='pie', autopct='%1.1f%%', colors=colors, ax=ax, textprops={'color':"w", 'weight':'bold'})
                plt.ylabel("")
                st.pyplot(fig)

                # Botón de descarga destacado
                st.write("---")
                st.subheader("📦 Tu reporte está listo")
                xlsx = to_excel_advanced(df)
                st.download_button(
                    label="📥 DESCARGAR REPORTE EXCEL (CON PESTAÑAS)",
                    data=xlsx,
                    file_name=f"Analisis_IA_{video_id}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
                st.write("#### 📝 Vista previa de comentarios")
                st.dataframe(df.head(10), use_container_width=True)

        except Exception as e:
            st.error(f"Error: {e}")


