import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
import re
import seaborn as sns
import matplotlib.pyplot as plt
from pysentimiento import create_analyzer
import io

# =================================================================
# 0. CONFIGURACIÓN DE LA PÁGINA Y MODELOS
# =================================================================
st.set_page_config(page_title="Santiago Delgado | AI Analyzer", layout="wide")

@st.cache_resource
def cargar_modelos():
    # Cargamos sentimiento y odio (Hate Speech) para el Brand Safety score
    sentiment = create_analyzer(task="sentiment", lang="es")
    hate = create_analyzer(task="hate_speech", lang="es")
    return sentiment, hate

sentiment_analyzer, hate_analyzer = cargar_modelos()

# =================================================================
# 1. FUNCIONES DE APOYO (LÓGICA)
# =================================================================

def extraer_video_id(url):
    regex = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(regex, url)
    return match.group(1) if match else None

def preprocesar_texto(texto):
    texto = re.sub(r'http\S+|www\S+|https\S+', '', texto, flags=re.MULTILINE)
    texto = texto.lower().replace('&quot;', ' ').replace('&#39;', ' ')
    texto = re.sub(r'<.*?>', '', texto)
    return texto.strip()

def obtener_comentarios(api_key, video_id, max_comentarios):
    youtube = build('youtube', 'v3', developerKey=api_key)
    comentarios = []
    next_page_token = None
    
    while len(comentarios) < max_comentarios:
        try:
            request = youtube.commentThreads().list(
                part="snippet", videoId=video_id, maxResults=100, pageToken=next_page_token
            )
            response = request.execute()
            
            for item in response.get('items', []):
                comment = item['snippet']['topLevelComment']['snippet']
                comentarios.append({
                    'autor': comment['authorDisplayName'],
                    'texto_original': comment['textDisplay'],
                    'texto_procesado': preprocesar_texto(comment['textDisplay'])
                })
                if len(comentarios) >= max_comentarios: break
            
            next_page_token = response.get('nextPageToken')
            if not next_page_token: break
        except Exception as e:
            st.error(f"Error de API: {e}")
            break
    return pd.DataFrame(comentarios)

# =================================================================
# 2. INTERFAZ DE USUARIO (STREAMLIT)
# =================================================================

st.title("🤖 AI Audience Analyzer Pro")
st.markdown("Analiza el sentimiento y la seguridad de marca de tus videos de YouTube.")

with st.sidebar:
    st.header("⚙️ Configuración")
    api_key = st.text_input("YouTube API Key", value="", type="password")
    limite = st.slider("Límite de comentarios", 100, 5000, 1000)
    st.divider()
    st.info("Desarrollado por Santiago Delgado")

url_input = st.text_input("Pega la URL de YouTube aquí (Video o Short):", placeholder="https://www.youtube.com/watch?v=...")

if st.button("🚀 Iniciar Análisis"):
    video_id = extraer_video_id(url_input)
    
    if video_id and api_key:
        # FASE 1: EXTRACCIÓN
        with st.status("📥 Extrayendo comentarios...", expanded=True) as status:
            df = obtener_comentarios(api_key, video_id, limite)
            if df.empty:
                st.error("No se encontraron comentarios o el ID es inválido.")
                st.stop()
            status.update(label=f"✅ {len(df)} comentarios obtenidos.", state="complete")
        
        # FASE 2: ANÁLISIS IA (SENTIMIENTO + ODIO)
        st.subheader("🧠 Procesando con BERT (Español)")
        bar_progreso = st.progress(0)
        sentimientos = []
        toxicidad = []
        
        for i, texto in enumerate(df['texto_procesado']):
            # Sentimiento
            res_sent = sentiment_analyzer.predict(texto)
            map_sent = {"POS": "POSITIVO", "NEG": "NEGATIVO", "NEU": "NEUTRO"}
            sentimientos.append(map_sent.get(res_sent.output, "NEUTRO"))
            
            # Odio / Agresividad
            res_hate = hate_analyzer.predict(texto)
            toxicidad.append("ALERTA" if res_hate.output != [] else "SEGURO")
            
            bar_progreso.progress((i + 1) / len(df))
        
        df['sentimiento'] = sentimientos
        df['seguridad_marca'] = toxicidad
        
        # FASE 3: VISUALIZACIÓN DE RESULTADOS
        st.divider()
        col1, col2, col3 = st.columns(3)
        
        conteo = df['sentimiento'].value_counts(normalize=True) * 100
        total_toxicos = (df['seguridad_marca'] == "ALERTA").sum()

        with col1:
            st.metric("Total Analizado", f"{len(df)}")
            st.metric("Nivel de Toxicidad", f"{total_toxicos}", delta="Críticos", delta_color="inverse")
        
        with col2:
            st.write("**Distribución de Sentimiento**")
            st.write(f"🟢 Positivos: {conteo.get('POSITIVO', 0):.1f}%")
            st.write(f"🔴 Negativos: {conteo.get('NEGATIVO', 0):.1f}%")
            st.write(f"🟡 Neutros: {conteo.get('NEUTRO', 0):.1f}%")

        with col3:
            fig, ax = plt.subplots(figsize=(4, 3))
            sns.countplot(data=df, x='sentimiento', palette={'POSITIVO': '#2ecc71', 'NEUTRO': '#95a5a6', 'NEGATIVO': '#e74c3c'}, ax=ax)
            plt.xticks(fontsize=8)
            plt.yticks(fontsize=8)
            st.pyplot(fig)

        # FASE 4: EXPORTACIÓN
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Analisis')
        
        st.download_button(
            label="📥 Descargar Reporte en Excel",
            data=buffer.getvalue(),
            file_name=f"Analisis_IA_{video_id}.xlsx",
            mime="application/vnd.ms-excel"
        )

        # FASE 5: TABLAS DETALLADAS
        st.divider()
        t1, t2 = st.tabs(["⭐ Mejores Comentarios", "🚩 Alertas de Marca"])
        with t1:
            st.table(df[df['sentimiento'] == 'POSITIVO'][['autor', 'texto_original']].head(10))
        with t2:
            st.table(df[df['seguridad_marca'] == 'ALERTA'][['autor', 'texto_original']].head(10))
                
    else:

        st.warning("⚠️ Por favor ingresa una URL válida y tu API Key.")
