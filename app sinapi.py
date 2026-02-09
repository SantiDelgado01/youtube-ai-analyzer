import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from pysentimiento import create_analyzer
import seaborn as sns
import matplotlib.pyplot as plt
import io

# 1. CONFIGURACIÓN ESTÉTICA
st.set_page_config(page_title="AI Audience Insights", page_icon="📈", layout="wide")

# CSS personalizado para mejorar el look
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #FF0000; color: white; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0px 2px 10px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def load_analyzers():
    return create_analyzer(task="sentiment", lang="es"), create_analyzer(task="hate_speech", lang="es")

sentiment_proc, hate_proc = load_analyzers()

# 2. FUNCIÓN DE EXCEL CON PESTAÑAS Y COLORES
def to_excel_advanced(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Definir dataframes por sentimiento
        pos_df = df[df['Sentimiento'] == 'POS']
        neg_df = df[df['Sentimiento'] == 'NEG']
        neu_df = df[df['Sentimiento'] == 'NEU']

        # Crear las pestañas
        df.to_excel(writer, index=False, sheet_name='TODOS')
        pos_df.to_excel(writer, index=False, sheet_name='POSITIVOS')
        neg_df.to_excel(writer, index=False, sheet_name='NEGATIVOS')
        neu_df.to_excel(writer, index=False, sheet_name='NEUTRALES')

        workbook  = writer.book
        
        # Formatos de colores
        fmt_pos = workbook.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100'}) # Verde
        fmt_neg = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'}) # Rojo
        fmt_neu = workbook.add_format({'bg_color': '#F2F2F2', 'font_color': '#333333'}) # Gris

        # Aplicar formato condicional en la hoja "TODOS"
        ws = writer.sheets['TODOS']
        header_format = workbook.add_format({'bold': True, 'bg_color': '#333333', 'font_color': 'white'})
        
        for col_num, value in enumerate(df.columns.values):
            ws.write(0, col_num, value, header_format)
            ws.set_column(col_num, col_num, 30)

        # La columna C es la de 'Sentimiento' (índice 2)
        ws.conditional_format('C2:C5000', {'type': 'cell', 'criteria': '==', 'value': '"POS"', 'format': fmt_pos})
        ws.conditional_format('C2:C5000', {'type': 'cell', 'criteria': '==', 'value': '"NEG"', 'format': fmt_neg})
        ws.conditional_format('C2:C5000', {'type': 'cell', 'criteria': '==', 'value': '"NEU"', 'format': fmt_neu})

    return output.getvalue()

# 3. CUERPO DE LA APP
st.title("📈 AI Audience Sentiment Dashboard")
st.subheader("Análisis estratégico de comunidades en YouTube")

with st.sidebar:
    st.header("⚙️ Panel de Control")
    key_from_secret = st.secrets.get("YOUTUBE_API_KEY", "")
    api_key = st.text_input("YouTube API Key", value=key_from_secret, type="password")
    video_url = st.text_input("Enlace del Video")
    max_com = st.slider("Volumen de muestra", 20, 500, 100)
    st.divider()
    st.markdown("### ¿Cómo monetizar?")
    st.write("Usa el botón de descarga para entregar reportes PDF/Excel a tus clientes.")

if st.button("🔍 ANALIZAR AHORA"):
    if not api_key or not video_url:
        st.warning("⚠️ Completa los datos en la barra lateral.")
    else:
        try:
            video_id = video_url.split("v=")[-1].split("&")[0]
            yt = build("youtube", "v3", developerKey=api_key)
            
            with st.spinner("🧠 Procesando sentimientos con Inteligencia Artificial..."):
                res = yt.commentThreads().list(part="snippet", videoId=video_id, maxResults=max_com).execute()
                
                data = []
                for item in res['items']:
                    txt = item['snippet']['topLevelComment']['snippet']['textDisplay']
                    user = item['snippet']['topLevelComment']['snippet']['authorDisplayName']
                    s = sentiment_proc.predict(txt).output
                    h = "Tóxico" if len(hate_proc.predict(txt).output) > 0 else "Limpio"
                    data.append({"Usuario": user, "Comentario": txt, "Sentimiento": s, "Seguridad": h})
                
                df = pd.DataFrame(data)

                # MÉTRICAS RÁPIDAS
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Total", len(df))
                m2.metric("Positivos ✅", len(df[df['Sentimiento']=='POS']))
                m3.metric("Negativos ❌", len(df[df['Sentimiento']=='NEG']))
                m4.metric("Tóxicos ⚠️", len(df[df['Seguridad']=='Tóxico']))

                st.divider()

                # GRÁFICOS
                c1, c2 = st.columns(2)
                with c1:
                    st.write("### Clima de Opinión")
                    fig, ax = plt.subplots()
                    df['Sentimiento'].value_counts().plot(kind='pie', autopct='%1.1f%%', colors=['#636EFA','#EF553B','#00CC96'], ax=ax)
                    st.pyplot(fig)
                
                with c2:
                    st.write("### Top Comentarios")
                    st.dataframe(df[['Usuario', 'Comentario', 'Sentimiento']].head(10))

                st.divider()

                # DESCARGA
                xlsx = to_excel_advanced(df)
                st.download_button(
                    label="📥 DESCARGAR REPORTE ESTRATÉGICO (EXCEL)",
                    data=xlsx,
                    file_name=f"Reporte_IA_{video_id}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

        except Exception as e:
            st.error(f"Error: {e}")

