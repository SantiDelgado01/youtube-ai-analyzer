import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from pysentimiento import create_analyzer
import io

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Audience Pro Business", page_icon="📊", layout="wide")

# 2. CSS DE ALTA VISIBILIDAD
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    h1, h2, h3 { color: white !important; }
    
    /* BOTÓN ANALIZAR - MÁXIMA LEGIBILIDAD */
    div.stButton > button {
        width: 100% !important;
        background-color: #0072ff !important;
        color: #ffffff !important;
        font-size: 20px !important;
        font-weight: 800 !important;
        height: 3.5em !important;
        border-radius: 10px !important;
        border: 2px solid #ffffff !important;
    }
    
    /* TARJETAS DE MÉTRICAS */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        padding: 20px !important;
        border-radius: 15px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. CARGA DE IA
@st.cache_resource
def load_ia():
    return create_analyzer(task="sentiment", lang="es")

analyzer = load_ia()

# 4. INTERFAZ
st.title("💎 Auditoría de Audiencia y Ventas")
st.markdown("### Extrae insights, porcentajes y leads en segundos")

with st.sidebar:
    st.header("Configuración")
    api_key = st.text_input("YouTube API Key", type="password")
    video_url = st.text_input("URL del Video")
    max_com = st.select_slider("Cantidad de comentarios", options=[50, 100, 200, 500], value=100)

btn = st.button("GENERAR INFORME ESTRATÉGICO")

if btn:
    if not api_key or not video_url:
        st.error("Faltan datos de acceso.")
    else:
        try:
            video_id = video_url.split("v=")[-1].split("&")[0]
            yt = build("youtube", "v3", developerKey=api_key)
            
            with st.status("Analizando sentimientos y buscando dinero...", expanded=True) as status:
                res = yt.commentThreads().list(part="snippet", videoId=video_id, maxResults=max_com).execute()
                
                data = []
                kw_precio = ["precio", "cuanto", "costo", "valor", "comprar", "venden", "info", "información"]
                
                for item in res['items']:
                    txt = item['snippet']['topLevelComment']['snippet']['textDisplay']
                    user = item['snippet']['topLevelComment']['snippet']['authorDisplayName']
                    # Análisis de sentimiento
                    pred = analyzer.predict(txt)
                    sent = pred.output # POS, NEU, NEG
                    prob = pred.probas[sent] # Confianza de la IA para ordenar el Top 10
                    
                    data.append({
                        "Usuario": user,
                        "Comentario": txt,
                        "Sentimiento": sent,
                        "Confianza": prob,
                        "Es_Precio": any(k in txt.lower() for k in kw_precio)
                    })
                
                df = pd.DataFrame(data)
                status.update(label="✅ Análisis Completo", state="complete")

            # --- SECCIÓN 1: PORCENTAJES ---
            st.subheader("📈 Salud de la Comunidad")
            c1, c2, c3, c4 = st.columns(4)
            
            total = len(df)
            pos_p = (len(df[df['Sentimiento']=='POS']) / total) * 100
            neu_p = (len(df[df['Sentimiento']=='NEU']) / total) * 100
            neg_p = (len(df[df['Sentimiento']=='NEG']) / total) * 100
            
            c1.metric("Positivos", f"{pos_p:.1f}%")
            c2.metric("Neutros", f"{neu_p:.1f}%")
            c3.metric("Negativos", f"{neg_p:.1f}%")
            c4.metric("Interés de Compra", len(df[df['Es_Precio']==True]), "Leads")

            # --- SECCIÓN 2: PRECIO ---
            st.divider()
            st.subheader("💰 Consultas de Precio / Leads")
            leads_df = df[df['Es_Precio'] == True][['Usuario', 'Comentario']]
            if not leads_df.empty:
                st.table(leads_df)
            else:
                st.info("No se detectaron preguntas de precio.")

            # --- SECCIÓN 3: TOP 10 ---
            st.divider()
            col_pos, col_neg = st.columns(2)
            
            with col_pos:
                st.subheader("✅ Top 10 Comentarios Positivos")
                top_pos = df[df['Sentimiento']=='POS'].sort_values(by="Confianza", ascending=False).head(10)
                st.dataframe(top_pos[['Usuario', 'Comentario']], hide_index=True)

            with col_neg:
                st.subheader("❌ Top 10 Comentarios Negativos")
                top_neg = df[df['Sentimiento']=='NEG'].sort_values(by="Confianza", ascending=False).head(10)
                st.dataframe(top_neg[['Usuario', 'Comentario']], hide_index=True)

        except Exception as e:
            st.error(f"Error técnico: {e}")

