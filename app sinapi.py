import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from pysentimiento import create_analyzer
import io

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Audience Intelligence Pro", page_icon="💎", layout="centered")

# 2. CSS PARA CENTRAR TODO Y MEJORAR EL BOTÓN
st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at top, #1e2630 0%, #0e1117 100%); }
    
    /* Centrar títulos y textos */
    .main .block-container { max-width: 800px; padding-top: 2rem; }
    h1, h2, h3, p { text-align: center !important; color: white !important; }
    
    /* Botón Centrado y Legible */
    div.stButton > button {
        display: block;
        margin: 0 auto !important;
        width: 100% !important;
        background-color: #0072ff !important;
        color: #ffffff !important;
        font-size: 22px !important;
        font-weight: 900 !important;
        height: 3.5em !important;
        border-radius: 15px !important;
        border: 2px solid #ffffff !important;
        text-transform: uppercase;
    }

    /* Estilo de métricas centradas */
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 15px;
        text-align: center;
    }
    
    /* Centrar inputs */
    .stTextInput, .stSelectSlider { text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# 3. CARGA DE IA
@st.cache_resource
def load_ia():
    return create_analyzer(task="sentiment", lang="es")

analyzer = load_ia()

# 4. INTERFAZ CENTRADA
st.title("💎 Audience Intelligence")
st.write("Analiza el sentimiento y detecta oportunidades de venta en el centro de tu comunidad.")

# Contenedor central de inputs
with st.container():
    api_key = st.text_input("🔑 Google API Key", type="password", help="Pega tu clave de Google Cloud")
    video_url = st.text_input("🔗 Enlace del Video", placeholder="https://www.youtube.com/watch?v=...")
    max_com = st.select_slider("⚡ Cantidad de comentarios a auditar", options=[50, 100, 250, 500], value=100)
    st.write("")
    btn = st.button("INICIAR ANÁLISIS")

st.divider()

if btn:
    if not api_key or not video_url:
        st.error("⚠️ Por favor, rellena todos los campos para continuar.")
    else:
        try:
            video_id = video_url.split("v=")[-1].split("&")[0]
            yt = build("youtube", "v3", developerKey=api_key)
            
            with st.status("🧠 Procesando datos de audiencia...", expanded=True) as status:
                res = yt.commentThreads().list(part="snippet", videoId=video_id, maxResults=max_com).execute()
                
                data = []
                kw_precio = ["precio", "cuanto", "costo", "valor", "comprar", "venden", "info", "interesado"]
                
                for item in res['items']:
                    txt = item['snippet']['topLevelComment']['snippet']['textDisplay']
                    user = item['snippet']['topLevelComment']['snippet']['authorDisplayName']
                    pred = analyzer.predict(txt)
                    data.append({
                        "Usuario": user,
                        "Comentario": txt,
                        "Sentimiento": pred.output,
                        "Confianza": pred.probas[pred.output],
                        "Es_Precio": any(k in txt.lower() for k in kw_precio)
                    })
                
                df = pd.DataFrame(data)
                status.update(label="✅ Análisis finalizado con éxito", state="complete")

            # --- RESULTADOS CENTRADOS ---
            st.header("📊 Métricas de Salud")
            
            total = len(df)
            pos_n = len(df[df['Sentimiento']=='POS'])
            neu_n = len(df[df['Sentimiento']=='NEU'])
            neg_n = len(df[df['Sentimiento']=='NEG'])
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Positivos", f"{(pos_n/total)*100:.1f}%")
            c2.metric("Neutros", f"{(neu_n/total)*100:.1f}%")
            c3.metric("Negativos", f"{(neg_n/total)*100:.1f}%")

            # Barra de sentimiento (Visualización rápida)
            st.write("**Balance de Sentimiento (Visual)**")
            st.progress(pos_n / total)

            # --- LEADS DE VENTA ---
            st.header("💰 Leads Detectados (Precio/Info)")
            leads_df = df[df['Es_Precio'] == True][['Usuario', 'Comentario']]
            if not leads_df.empty:
                st.dataframe(leads_df, use_container_width=True, hide_index=True)
            else:
                st.info("No se detectaron intenciones de compra directas.")

            # --- TOP 10 ---
            st.header("🔝 Top 10 Comentarios Críticos")
            
            tab1, tab2 = st.tabs(["✅ Los más Positivos", "❌ Los más Negativos"])
            
            with tab1:
                top_pos = df[df['Sentimiento']=='POS'].sort_values(by="Confianza", ascending=False).head(10)
                st.table(top_pos[['Usuario', 'Comentario']])
            
            with tab2:
                top_neg = df[df['Sentimiento']=='NEG'].sort_values(by="Confianza", ascending=False).head(10)
                st.table(top_neg[['Usuario', 'Comentario']])

            # Exportar
            st.write("---")
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 DESCARGAR REPORTE COMPLETO",
                data=csv,
                file_name=f"Analisis_{video_id}.csv",
                mime="text/csv"
            )

        except Exception as e:
            st.error(f"Hubo un error al conectar con YouTube: {e}")


