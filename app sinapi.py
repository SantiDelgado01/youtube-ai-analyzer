import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from pysentimiento import create_analyzer
import io

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Audience Intelligence Pro", page_icon="💰", layout="centered")

# 2. CSS DE ALTO NIVEL (MEJORADO PARA LECTURA)
st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at top, #1e2630 0%, #0e1117 100%); }
    [data-testid="stSidebar"] { display: none; }
    
    h1 { color: white !important; text-shadow: 0px 0px 15px rgba(255, 255, 255, 0.2); text-align: center; font-weight: 800; }
    p { color: #808495 !important; text-align: center; }

    .stTextInput>div>div>input {
        background-color: rgba(255, 255, 255, 0.05) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
    }

    /* BOTÓN OPTIMIZADO PARA MÁXIMA LEGIBILIDAD */
    .stButton>button {
        width: 100%; 
        border-radius: 15px !important; 
        height: 4em;
        background: linear-gradient(90deg, #00c6ff 0%, #0072ff 100%) !important;
        color: #ffffff !important; /* Blanco puro */
        font-size: 18px !important; /* Más grande */
        font-weight: 700 !important; 
        text-transform: uppercase; /* Mayúsculas para impacto */
        letter-spacing: 1.5px !important; /* Espaciado profesional */
        border: none !important;
        box-shadow: 0px 4px 15px rgba(0, 114, 255, 0.4); 
        transition: 0.3s;
    }
    .stButton>button:hover { 
        transform: translateY(-2px); 
        box-shadow: 0px 8px 25px rgba(0, 114, 255, 0.6); 
        color: #ffffff !important;
    }

    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        padding: 15px !important; border-radius: 15px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. CARGA DE IA
@st.cache_resource
def load_analyzers():
    return create_analyzer(task="sentiment", lang="es")

sentiment_proc = load_analyzers()

# 4. LÓGICA DE EXCEL PROFESIONAL
def to_excel_pro(df, leads, dudas):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Análisis Completo')
        leads.to_excel(writer, index=False, sheet_name='LEADS DE VENTA')
        dudas.to_excel(writer, index=False, sheet_name='DUDAS DE AUDIENCIA')
        
        workbook = writer.book
        fmt_gold = workbook.add_format({'bg_color': '#FFD700', 'font_color': '#000000', 'bold': True})
        ws_leads = writer.sheets['LEADS DE VENTA']
        ws_leads.set_column('A:C', 30)
        ws_leads.conditional_format('A1:C1', {'type': 'no_blanks', 'format': fmt_gold})
        
    return output.getvalue()

# 5. INTERFAZ
st.markdown("<h1>💎 Audience Intelligence</h1>", unsafe_allow_html=True)
st.markdown("<p>Encuentra leads y optimiza contenido con IA</p>", unsafe_allow_html=True)

with st.container():
    key_secret = st.secrets.get("YOUTUBE_API_KEY", "")
    api_key = st.text_input("🔑 Google Cloud API Key", value=key_secret, type="password")
    video_url = st.text_input("🔗 Enlace del Video", placeholder="https://www.youtube.com/watch?v=...")
    max_com = st.select_slider("⚡ Profundidad del Análisis", options=[50, 100, 250, 500], value=100)
    
    st.write("")
    # El botón ahora será súper legible
    btn = st.button("INICIAR AUDITORÍA ESTRATÉGICA")

st.divider()

# 6. PROCESAMIENTO
if btn:
    if not api_key or not video_url:
        st.error("Datos incompletos.")
    else:
        try:
            video_id = video_url.split("v=")[-1].split("&")[0]
            yt = build("youtube", "v3", developerKey=api_key)
            
            with st.status("🧠 Procesando datos...", expanded=True) as status:
                res = yt.commentThreads().list(part="snippet", videoId=video_id, maxResults=max_com).execute()
                
                data = []
                kw_dinero = ["precio", "cuanto", "comprar", "info", "costo", "venden", "adquirir", "link", "interesado"]
                kw_duda = ["como", "por que", "puedes hacer", "tutorial", "duda", "ayuda", "explicar"]

                for item in res['items']:
                    txt = item['snippet']['topLevelComment']['snippet']['textDisplay']
                    user = item['snippet']['topLevelComment']['snippet']['authorDisplayName']
                    s = sentiment_proc.predict(txt).output
                    
                    data.append({
                        "Usuario": user,
                        "Comentario": txt,
                        "Sentimiento": s,
                        "Es_Lead": any(k in txt.lower() for k in kw_dinero),
                        "Es_Duda": any(k in txt.lower() for k in kw_duda)
                    })
                
                df = pd.DataFrame(data)
                status.update(label="✅ Análisis Listo", state="complete")

            # DASHBOARD
            st.markdown("### 📊 Indicadores de Negocio")
            c1, c2, c3 = st.columns(3)
            
            leads_df = df[df['Es_Lead'] == True][['Usuario', 'Comentario']]
            dudas_df = df[df['Es_Duda'] == True][['Usuario', 'Comentario']]

            c1.metric("Leads 💰", len(leads_df))
            c2.metric("Positivos 📈", len(df[df['Sentimiento']=='POS']))
            c3.metric("Dudas ❓", len(dudas_df))

            st.write("")
            xlsx = to_excel_pro(df, leads_df, dudas_df)
            st.download_button(
                label="📥 DESCARGAR REPORTE PARA EL CLIENTE",
                data=xlsx,
                file

