import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from pysentimiento import create_analyzer
import io

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Audience Intelligence Pro", page_icon="💰", layout="centered")

# 2. CSS DE ALTO IMPACTO Y LEGIBILIDAD TOTAL
st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at top, #1e2630 0%, #0e1117 100%); }
    [data-testid="stSidebar"] { display: none; }
    
    h1 { color: white !important; text-align: center; font-weight: 800; }
    p { color: #808495 !important; text-align: center; }

    /* ESTILO DE INPUTS */
    .stTextInput>div>div>input {
        background-color: rgba(255, 255, 255, 0.05) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }

    /* EL BOTÓN: FONDO OSCURO, TEXTO BLANCO RADIANTE */
    /* Usamos selectores más específicos para obligar a Streamlit a obedecer */
    div.stButton > button {
        width: 100% !important;
        background-color: #0072ff !important; /* Azul sólido muy vivo */
        color: #ffffff !important; /* BLANCO PURO */
        font-size: 22px !important; /* Muy grande */
        font-weight: 900 !important; /* Ultra negrita */
        height: 3.5em !important;
        border-radius: 12px !important;
        border: 2px solid #ffffff !important; /* Borde blanco para resaltar */
        text-transform: uppercase !important;
        opacity: 1 !important;
        visibility: visible !important;
    }

    /* Asegurar que el texto siga siendo blanco al pasar el mouse */
    div.stButton > button:hover {
        background-color: #00c6ff !important;
        color: #ffffff !important;
        border: 2px solid #ffffff !important;
    }
    
    /* Forzar el color del texto dentro del botón por si acaso */
    div.stButton > button p {
        color: #ffffff !important;
        font-weight: 900 !important;
    }

    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 15px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. CARGA DE IA
@st.cache_resource
def load_analyzers():
    return create_analyzer(task="sentiment", lang="es")

sentiment_proc = load_analyzers()

# 4. LÓGICA DE EXCEL
def to_excel_pro(df, leads, dudas):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Análisis Completo')
        leads.to_excel(writer, index=False, sheet_name='LEADS DE VENTA')
        dudas.to_excel(writer, index=False, sheet_name='DUDAS DE AUDIENCIA')
    return output.getvalue()

# 5. INTERFAZ
st.markdown("<h1>💎 Audience Intelligence</h1>", unsafe_allow_html=True)
st.markdown("<p>Escaneo de leads y salud de marca</p>", unsafe_allow_html=True)

with st.container():
    api_key = st.text_input("🔑 Google API Key", type="password")
    video_url = st.text_input("🔗 Link del Video")
    max_com = st.select_slider("⚡ Comentarios", options=[50, 100, 250, 500], value=100)
    
    st.write("")
    # Este es el botón que DEBE leerse ahora
    btn = st.button("ANALIZAR AHORA")

if btn:
    if not api_key or not video_url:
        st.error("Completa los campos.")
    else:
        try:
            video_id = video_url.split("v=")[-1].split("&")[0]
            yt = build("youtube", "v3", developerKey=api_key)
            
            with st.status("Analizando...", expanded=True) as status:
                res = yt.commentThreads().list(part="snippet", videoId=video_id, maxResults=max_com).execute()
                data = []
                kw_dinero = ["precio", "cuanto", "comprar", "info", "costo", "interesado"]
                kw_duda = ["como", "por que", "ayuda", "explicar"]

                for item in res['items']:
                    txt = item['snippet']['topLevelComment']['snippet']['textDisplay']
                    user = item['snippet']['topLevelComment']['snippet']['authorDisplayName']
                    s = sentiment_proc.predict(txt).output
                    data.append({
                        "Usuario": user, "Comentario": txt, "Sentimiento": s,
                        "Es_Lead": any(k in txt.lower() for k in kw_dinero),
                        "Es_Duda": any(k in txt.lower() for k in kw_duda)
                    })
                df = pd.DataFrame(data)
                status.update(label="Completado", state="complete")

            # Dashboard rápido
            leads_df = df[df['Es_Lead'] == True][['Usuario', 'Comentario']]
            dudas_df = df[df['Es_Duda'] == True][['Usuario', 'Comentario']]

            c1, c2 = st.columns(2)
            c1.metric("Leads 💰", len(leads_df))
            c2.metric("Dudas ❓", len(dudas_df))

            st.write("---")
            xlsx_data = to_excel_pro(df, leads_df, dudas_df)
            st.download_button(
                label="📥 DESCARGAR REPORTE",
                data=xlsx_data,
                file_name="Reporte.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as e:
            st.error(f"Error: {e}")


