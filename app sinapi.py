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
    div.stButton >
