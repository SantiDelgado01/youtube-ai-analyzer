import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from pysentimiento import create_analyzer
import io

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Audience Intelligence Pro", page_icon="💎", layout="centered")

# 2. CSS PARA CENTRAR TODO Y MEJORAR EL BOTÓN (Mantenido igual)
st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at top, #1e2630 0%, #0e1117 100%); }
    
    .main .block-container { max-width: 800px; padding-top: 2rem; }
    h1, h2, h3, p { text-align: center !important; color: white !important; }
    
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

    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 15px;
        text-align: center;
    }
    
    .stTextInput, .stSelectSlider { text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# 3. CARGA DE IA
@st.cache_resource
def load_ia():
    return create_analyzer(task="sentiment", lang="es")

analyzer = load_ia()

# 4. FUNCIÓN PARA GENERAR EXCEL EN MEMORIA
def to_excel(df, leads, pos, neg):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Data Completa')
        leads.to_excel(writer, index=False, sheet_name='Leads de Venta')
        pos.to_excel(writer, index=False, sheet_name='Top Positivos')
        neg.to_excel(writer, index=False, sheet_name='Top Negativos')
    return output.getvalue()

# 5. INTERFAZ CENTRADA
st.title("💎 Audience Intelligence")
st.write("Analiza el sentimiento y detecta oportunidades de venta en el centro de tu comunidad.")

with st.container():
    api_key = st.text_input("🔑 Google API Key", type="password", help="Pega tu clave de Google Cloud")
    video_url = st.text_input("🔗 Enlace del Video", placeholder="https://www.youtube.com/watch?v=...")
    max_com = st.select_slider("⚡ Cantidad de comentarios a analizar", options=[50, 100, 250, 500], value=100)
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

            # --- MÉTRICAS ---
            st.header("📊 Métricas de Salud")
            total = len(df)
            pos_n = len(df[df['Sentimiento']=='POS'])
            neu_n = len(df[df['Sentimiento']=='NEU'])
            neg_n = len(df[df['Sentimiento']=='NEG'])
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Positivos", f"{(pos_n/total)*100:.1f}%")
            c2.metric("Neutros", f"{(neu_n/total)*100:.1f}%")
            c3.metric("Negativos", f"{(neg_n/total)*100:.1f}%")

            st.write("**Balance de Sentimiento (Visual)**")
            st.progress(pos_n / total if total > 0 else 0)

            # --- LEADS ---
            st.header("💰 Leads Detectados")
            leads_df = df[df['Es_Precio'] == True][['Usuario', 'Comentario']]
            if not leads_df.empty:
                st.dataframe(leads_df, use_container_width=True, hide_index=True)
            else:
                st.info("No se detectaron intenciones de compra directas.")

            # --- TOP 10 ---
            st.header("🔝 Top Comentarios")
            tab1, tab2 = st.tabs(["✅ Positivos", "❌ Negativos"])
            
            top_pos = df[df['Sentimiento']=='POS'].sort_values(by="Confianza", ascending=False).head(10)
            top_neg = df[df['Sentimiento']=='NEG'].sort_values(by="Confianza", ascending=False).head(10)

            with tab1:
                st.table(top_pos[['Usuario', 'Comentario']])
            with tab2:
                st.table(top_neg[['Usuario', 'Comentario']])

            # --- EXPORTAR A EXCEL ---
            st.write("---")
            excel_data = to_excel(df, leads_df, top_pos, top_neg)
            
            st.download_button(
                label="📥 DESCARGAR REPORTE EN EXCEL (.xlsx)",
                data=excel_data,
                file_name=f"Auditoria_{video_id}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        except Exception as e:
            st.error(f"Hubo un error al conectar con YouTube: {e}")


