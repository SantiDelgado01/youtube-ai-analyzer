import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from pysentimiento import create_analyzer
import io

# 1. CONFIGURACIÓN
st.set_page_config(page_title="AI Audience Dashboard", page_icon="📈")

# 2. CSS "BLINDADO" (FUERZA BRUTA PARA LEGIBILIDAD)
st.markdown("""
    <style>
    /* Fondo General */
    .stApp { background-color: #0e1117; }
    
    /* EL BOTÓN: ROJO CON TEXTO BLANCO CLARÍSIMO */
    div.stButton > button {
        width: 100% !important;
        background-color: #FF0000 !important; /* Rojo puro */
        color: #FFFFFF !important; /* BLANCO PURO */
        font-size: 24px !important; /* Tamaño gigante */
        font-weight: 900 !important; /* Máximo grosor */
        height: 3em !important;
        border-radius: 10px !important;
        border: 2px solid #ffffff !important;
        text-transform: uppercase !important;
    }
    
    /* Asegurar que el texto no cambie de color al tocarlo */
    div.stButton > button:hover, div.stButton > button:active, div.stButton > button:focus {
        color: #FFFFFF !important;
        background-color: #CC0000 !important;
        border: 2px solid #ffffff !important;
    }

    /* Forzar color de etiquetas de entrada */
    label { color: white !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. CARGA DE MODELO
@st.cache_resource
def load_ia():
    return create_analyzer(task="sentiment", lang="es")

analyzer = load_ia()

# 4. INTERFAZ LIMPIA
st.title("📊 AI Audience Sentiment")
st.write("Analiza comentarios y detecta oportunidades de venta.")

with st.form("my_form"):
    api_key = st.text_input("YouTube API Key", type="password")
    video_url = st.text_input("URL del Video de YouTube")
    count = st.slider("Cantidad de comentarios", 50, 500, 100)
    
    # El botón dentro de un formulario es más estable
    submit = st.form_submit_button("ANALIZAR VIDEO AHORA")

# 5. LÓGICA
if submit:
    if not api_key or not video_url:
        st.warning("Por favor, completa los campos.")
    else:
        try:
            video_id = video_url.split("v=")[-1].split("&")[0]
            youtube = build("youtube", "v3", developerKey=api_key)
            
            with st.spinner("Procesando inteligencia..."):
                request = youtube.commentThreads().list(
                    part="snippet", videoId=video_id, maxResults=count
                )
                response = request.execute()
                
                results = []
                for item in response['items']:
                    text = item['snippet']['topLevelComment']['snippet']['textDisplay']
                    sent = analyzer.predict(text).output
                    results.append({"Comentario": text, "Sentimiento": sent})
                
                df = pd.DataFrame(results)
                
                # Visualización
                st.success("¡Análisis completado!")
                st.subheader("Resumen de Audiencia")
                st.write(df.head())
                
                # Botón de descarga
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("Descargar Reporte CSV", csv, "reporte.csv", "text/csv")
                
        except Exception as e:
            st.error(f"Error: {e}")

