import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from pysentimiento import create_analyzer
import io

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Audience Intelligence Pro", page_icon="💰", layout="centered")

# 2. CSS DE ALTO NIVEL (BOTÓN CORREGIDO Y LEGIBLE)
st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at top, #1e2630 0%, #0e1117 100%); }
    [data-testid="stSidebar"] { display: none; }
    
    h1 { color: white !important; text-shadow: 0px 0px 15px rgba(255, 255, 255, 0.2); text-align: center; font-weight: 800; }
    p { color: #808495 !important; text-align: center; }

    /* ESTILO DE INPUTS */
    .stTextInput>div>div>input {
        background-color: rgba(255, 255, 255, 0.05) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
    }

    /* BOTÓN DE ACCIÓN PRINCIPAL: TEXTO BLANCO Y GRANDE */
    div.stButton > button:first-child {
        width: 100%; 
        border-radius: 15px !important; 
        height: 4em;
        background: linear-gradient(90deg, #00c6ff 0%, #0072ff 100%) !important;
        color: #ffffff !important; /* Blanco puro garantizado */
        font-size: 20px !important; /* Más grande aún */
        font-weight: 800 !important; 
        text-transform: uppercase;
        letter-spacing: 1.5px !important;
        border: none !important;
        box-shadow: 0px 4px 15px rgba(0, 114, 255, 0.4); 
    }

    div.stButton > button:hover { 
        transform: translateY(-2px); 
        box-shadow: 0px 8px 25px rgba(0, 114, 255, 0.6); 
        color: #ffffff !important;
    }

    /* ESTILO DE MÉTRICAS */
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
        # Formato dorado para los encabezados de leads
        fmt_gold = workbook.add_format({'bg_color': '#FFD700', 'font_color': '#000000', 'bold': True})
        ws_leads = writer.sheets['LEADS DE VENTA']
        ws_leads.set_column('A:C', 30)
        ws_leads.conditional_format('A1:C1', {'type': 'no_blanks', 'format': fmt_gold})
        
    return output.getvalue()

# 5. INTERFAZ
st.markdown("<h1>💎 Audience Intelligence</h1>", unsafe_allow_html=True)
st.markdown("<p>Extrae leads de ventas y salud de comunidad automáticamente</p>", unsafe_allow_html=True)

with st.container():
    api_key_sec = st.secrets.get("YOUTUBE_API_KEY", "")
    api_key = st.text_input("🔑 Google Cloud API Key", value=api_key_sec, type="password")
    video_url = st.text_input("🔗 Enlace del Video", placeholder="Pega el link de YouTube aquí...")
    max_com = st.select_slider("⚡ Cantidad de comentarios a auditar", options=[50, 100, 250, 500], value=100)
    
    st.write("")
    # Botón principal
    btn = st.button("INICIAR AUDITORÍA ESTRATÉGICA")

st.divider()

# 6. PROCESAMIENTO Y RESULTADOS
if btn:
    if not api_key or not video_url:
        st.error("Por favor rellena la API Key y el Link del video.")
    else:
        try:
            video_id = video_url.split("v=")[-1].split("&")[0]
            yt = build("youtube", "v3", developerKey=api_key)
            
            with st.status("🧠 La IA está trabajando...", expanded=True) as status:
                res = yt.commentThreads().list(part="snippet", videoId=video_id, maxResults=max_com).execute()
                
                data = []
                # Diccionario de palabras de negocio
                kw_dinero = ["precio", "cuanto", "comprar", "info", "costo", "venden", "adquirir", "link", "interesado", "comprarlo"]
                kw_duda = ["como", "por que", "puedes hacer", "tutorial", "duda", "ayuda", "explicar", "pasos"]

                for item in res['items']:
                    txt = item['snippet']['topLevelComment']['snippet']['textDisplay']
                    user = item['snippet']['topLevelComment']['snippet']['authorDisplayName']
                    
                    # Predicción de sentimiento
                    s = sentiment_proc.predict(txt).output
                    
                    data.append({
                        "Usuario": user,
                        "Comentario": txt,
                        "Sentimiento": s,
                        "Es_Lead": any(k in txt.lower() for k in kw_dinero),
                        "Es_Duda": any(k in txt.lower() for k in kw_duda)
                    })
                
                df = pd.DataFrame(data)
                status.update(label="✅ Análisis de Negocio Completado", state="complete")

            # --- SECCIÓN DE MÉTRICAS ---
            st.markdown("### 📊 Indicadores de Oportunidad")
            c1, c2, c3 = st.columns(3)
            
            leads_df = df[df['Es_Lead'] == True][['Usuario', 'Comentario']]
            dudas_df = df[df['Es_Duda'] == True][['Usuario', 'Comentario']]

            c1.metric("Leads de Venta 💰", len(leads_df))
            c2.metric("Positivos 📈", len(df[df['Sentimiento']=='POS']))
            c3.metric("Dudas Críticas ❓", len(dudas_df))

            # --- TABLAS DE RESULTADOS ---
            st.write("")
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.subheader("🔥 Clientes Potenciales")
                if not leads_df.empty:
                    st.dataframe(leads_df, use_container_width=True, hide_index=True)
                else:
                    st.info("No hay intenciones de compra directas.")

            with col_b:
                st.subheader("💡 Ideas para Contenido")
                if not dudas_df.empty:
                    st.dataframe(dudas_df, use_container_width=True, hide_index=True)
                else:
                    st.info("No se detectaron dudas críticas.")

            # --- BOTÓN DE DESCARGA (CORREGIDO) ---
            st.write("---")
            xlsx_data = to_excel_pro(df, leads_df, dudas_df)
            st.download_button(
                label="📥 DESCARGAR INFORME PARA EL CLIENTE (EXCEL)",
                data=xlsx_data,
                file_name=f"Informe_Business_{video_id}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        except Exception as e:
            st.error(f"Hubo un problema con la API o el Enlace: {e}")

