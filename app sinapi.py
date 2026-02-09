import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from pysentimiento import create_analyzer
import seaborn as sns
import matplotlib.pyplot as plt
import io

# 1. CONFIGURACIÓN VISUAL AVANZADA
st.set_page_config(page_title="AI Audience Insights", page_icon="📈", layout="wide")

# CSS para centrar y modernizar
st.markdown("""
    <style>
    /* Fondo general */
    .main { background-color: #0e1117; }
    
    /* Estilo del contenedor central */
    .stTextInput, .stSlider {
        background-color: #1e2129;
        border-radius: 10px;
        padding: 5px;
    }
    
    /* Botón principal */
    .stButton>button {
        width: 100%;
        border-radius: 20px;
        height: 3.5em;
        background: linear-gradient(45deg, #FF0000, #ff4b4b);
        color: white;
        font-weight: bold;
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0px 5px 15px rgba(255, 0, 0, 0.4);
    }
    
    /* Métricas */
    [data-testid="stMetric"] {
        background-color: #1e2129;
        border: 1px solid #31333f;
        padding: 15px;
        border-radius: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def load_analyzers():
    return create_analyzer(task="sentiment", lang="es"), create_analyzer(task="hate_speech", lang="es")

sentiment_proc, hate_proc = load_analyzers()

# --- FUNCIÓN EXCEL (Pestañas y Colores) ---
def to_excel_advanced(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='TODOS')
        df[df['Sentimiento'] == 'POS'].to_excel(writer, index=False, sheet_name='POSITIVOS')
        df[df['Sentimiento'] == 'NEG'].to_excel(writer, index=False, sheet_name='NEGATIVOS')
        df[df['Sentimiento'] == 'NEU'].to_excel(writer, index=False, sheet_name='NEUTRALES')

        workbook  = writer.book
        ws = writer.sheets['TODOS']
        
        # Formatos
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

# --- INTERFAZ CENTRALIZADA ---
# Título centrado
st.markdown("<h1 style='text-align: center;'>📈 AI Audience Sentiment Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #808495;'>Analiza la salud de cualquier comunidad de YouTube en segundos</p>", unsafe_allow_html=True)

st.write("---")

# Contenedor central de inputs
col_a, col_b, col_c = st.columns([1, 2, 1])

with col_b:
    with st.container():
        st.markdown("### 🛠️ Configura tu Análisis")
        
        # API Key (buscando en secrets primero)
        secret_key = st.secrets.get("YOUTUBE_API_KEY", "")
        api_key = st.text_input("YouTube API Key", value=secret_key, type="password", help="Pega aquí tu clave de Google Cloud Console")
        
        # URL del video
        video_url = st.text_input("Enlace del Video de YouTube", placeholder="https://www.youtube.com/watch?v=...")
        
        # Cantidad de comentarios
        max_com = st.select_slider("Cantidad de comentarios a procesar", options=[50, 100, 200, 500], value=100)
        
        # Botón grande
        analizar = st.button("🚀 INICIAR ANÁLISIS ESTRATÉGICO")

st.write("---")

# --- PROCESAMIENTO ---
if analizar:
    if not api_key or not video_url:
        st.error("❗ Falta información: Ingresa la API Key y el enlace del video.")
    else:
        try:
            video_id = video_url.split("v=")[-1].split("&")[0]
            yt = build("youtube", "v3", developerKey=api_key)
            
            with st.spinner("🧠 Nuestra IA está leyendo los comentarios..."):
                res = yt.commentThreads().list(part="snippet", videoId=video_id, maxResults=max_com).execute()
                
                data = []
                for item in res['items']:
                    txt = item['snippet']['topLevelComment']['snippet']['textDisplay']
                    user = item['snippet']['topLevelComment']['snippet']['authorDisplayName']
                    s = sentiment_proc.predict(txt).output
                    h = "Tóxico" if len(hate_proc.predict(txt).output) > 0 else "Limpio"
                    data.append({"Usuario": user, "Comentario": txt, "Sentimiento": s, "Seguridad": h})
                
                df = pd.DataFrame(data)

                # DASHBOARD DE RESULTADOS
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Analizados", len(df))
                m2.metric("Positivos", len(df[df['Sentimiento']=='POS']), delta="Saludable")
                m3.metric("Negativos", len(df[df['Sentimiento']=='NEG']), delta="-Críticas", delta_color="inverse")
                m4.metric("Tóxicos", len(df[df['Seguridad']=='Tóxico']), delta="Alertas", delta_color="inverse")

                c1, c2 = st.columns([1, 1.5])
                with c1:
                    st.write("#### 📊 Distribución de Sentimiento")
                    # Usamos colores directos para que combine con el diseño
                    colors = ['#00CC96', '#EF553B', '#636EFA']
                    fig, ax = plt.subplots(facecolor='#0e1117')
                    df['Sentimiento'].value_counts().plot(kind='pie', autopct='%1.1f%%', colors=colors, ax=ax, textprops={'color':"w"})
                    st.pyplot(fig)
                
                with c2:
                    st.write("#### 📥 Entregables")
                    xlsx = to_excel_advanced(df)
                    st.download_button(
                        label="📦 DESCARGAR REPORTE PARA CLIENTE (EXCEL)",
                        data=xlsx,
                        file_name=f"Informe_IA_{video_id}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    st.info("El reporte incluye pestañas automáticas para Positivos, Negativos y Neutrales.")
                    
                    st.write("#### 📝 Vista Previa")
                    st.dataframe(df.head(10), use_container_width=True)

        except Exception as e:
            st.error(f"Se produjo un error técnico: {e}")


