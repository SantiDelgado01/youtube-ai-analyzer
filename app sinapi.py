import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from pysentimiento import create_analyzer
import seaborn as sns
import matplotlib.pyplot as plt
import io

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="AI Audience Analyzer Pro", page_icon="🤖", layout="wide")

# 2. CARGA DE MODELOS (Cache para que sea rápido)
@st.cache_resource
def load_analyzers():
    sentiment_analyzer = create_analyzer(task="sentiment", lang="es")
    hate_analyzer = create_analyzer(task="hate_speech", lang="es")
    return sentiment_analyzer, hate_analyzer

sentiment_proc, hate_proc = load_analyzers()

# 3. FUNCIÓN PARA EL EXCEL PROFESIONAL
def to_excel_professional(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Análisis de Audiencia')
        
        workbook  = writer.book
        worksheet = writer.sheets['Análisis de Audiencia']

        # Formatos
        header_fmt = workbook.add_format({
            'bold': True, 
            'bg_color': '#1f77b4', 
            'font_color': 'white', 
            'border': 1
        })
        
        # Formato condicional para sentimientos (Opcional)
        # Aplicar formato a encabezados y ancho de columnas
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_fmt)
            column_len = max(df[value].astype(str).map(len).max(), len(value)) + 2
            worksheet.set_column(col_num, col_num, min(column_len, 50)) # Máximo 50 de ancho

    return output.getvalue()

# 4. INTERFAZ LATERAL (Configuración)
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1384/1384060.png", width=50)
    st.title("Configuración")
    
    # Intenta obtener la API Key de los Secrets, si no, usa el campo de texto
    api_key_default = st.secrets.get("YOUTUBE_API_KEY", "")
    api_key = st.text_input("YouTube API Key", value=api_key_default, type="password")
    
    video_url = st.text_input("URL del Video de YouTube")
    max_results = st.slider("Cantidad de comentarios", 50, 2000, 100)
    
    st.info("💡 Consejo: Usa el reporte de Excel para presentar resultados a tus clientes.")

# 5. LÓGICA DE EXTRACCIÓN Y ANÁLISIS
st.title("🤖 AI Audience Analyzer Pro")
st.markdown("### Transforma comentarios en decisiones estratégicas")

if st.button("🚀 Iniciar Análisis Profundo"):
    if not api_key or not video_url:
        st.error("❌ Por favor, ingresa la API Key y la URL del video.")
    else:
        try:
            # Extraer ID del video
            video_id = video_url.split("v=")[-1].split("&")[0]
            
            youtube = build("youtube", "v3", developerKey=api_key)
            
            with st.spinner("⏳ Extrayendo comentarios y analizando con IA..."):
                # Llamada a YouTube API
                request = youtube.commentThreads().list(
                    part="snippet",
                    videoId=video_id,
                    maxResults=max_results,
                    textFormat="plainText"
                )
                response = request.execute()

                comments = []
                for item in response['items']:
                    comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
                    author = item['snippet']['topLevelComment']['snippet']['authorDisplayName']
                    
                    # Análisis de Sentimiento
                    sent = sentiment_proc.predict(comment)
                    # Análisis de Odio/Toxicidad
                    hate = hate_proc.predict(comment)
                    
                    comments.append({
                        "Autor": author,
                        "Comentario": comment,
                        "Sentimiento": sent.output,
                        "Toxicidad": "Tóxico" if len(hate.output) > 0 else "Limpio"
                    })

                df = pd.DataFrame(comments)

                # 6. VISUALIZACIÓN DE RESULTADOS
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("📊 Distribución de Sentimientos")
                    fig, ax = plt.subplots()
                    sns.countplot(data=df, x='Sentimiento', palette='viridis', ax=ax)
                    st.pyplot(fig)

                with col2:
                    st.subheader("🛡️ Brand Safety (Toxicidad)")
                    tox_counts = df['Toxicidad'].value_counts()
                    fig2, ax2 = plt.subplots()
                    plt.pie(tox_counts, labels=tox_counts.index, autopct='%1.1f%%', colors=['#2ecc71', '#e74c3c'])
                    st.pyplot(fig2)

                st.divider()

                # 7. DESCARGA DE REPORTE
                excel_data = to_excel_professional(df)
                st.download_button(
                    label="📥 Descargar Reporte para Cliente (Excel)",
                    data=excel_data,
                    file_name=f"Analisis_Audiencia_{video_id}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

                st.subheader("📝 Vista previa de los datos")
                st.dataframe(df, use_container_width=True)

        except Exception as e:
            st.error(f"⚠️ Ocurrió un error: {e}")

else:
    st.write("Esperando datos... ingresa la URL y presiona el botón.")
