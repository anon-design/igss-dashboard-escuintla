"""
Dashboard Epidemiológico IGSS Escuintla
Aplicación principal con navegación por módulos y una arquitectura modular.
"""

import streamlit as st
import sys
from pathlib import Path

# --- Configuración de Path y Estilos ---
# Asegura que los módulos del proyecto se puedan importar correctamente.
sys.path.append(str(Path(__file__).parent))

from config import PAGE_CONFIG, CUSTOM_CSS
from utils.data_loader import load_all_data
from utils.filters import apply_filters_jerarquicos, get_summary_stats

# --- Importar Módulos de UI ---
from ui.sidebar import render_sidebar, render_summary_stats
from ui.main_page import render_main_page

# --- Importar Módulos de Páginas de Análisis ---
from modules import morbilidad_adultos, morbilidad_pediatrica, capitulos, eno, cronicas, geografico

# --- Configuración de la Página ---
st.set_page_config(**PAGE_CONFIG)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Helper para cargar y almacenar datos en session_state
def load_and_store_data(uploaded_file):
    with st.spinner("Cargando datos..."):
        # Limpiar caché de Streamlit para asegurar que se procese el nuevo archivo
        st.cache_data.clear() 
        loaded_data = load_all_data(uploaded_file)
        if loaded_data['data'].empty:
            st.error("⚠️ No se pudieron cargar o procesar los datos. Verifica el formato del archivo.")
            st.stop()
        st.session_state['datos'] = loaded_data
        st.session_state['uploaded_file_hash'] = hash(uploaded_file.getvalue()) if uploaded_file else 'default'


def main():
    """
    Función principal que orquesta la aplicación Streamlit.
    """
    # --- 1. Manejo de Carga de Datos y Session State ---
    # Inicializar st.session_state['datos'] si no existe.
    if 'datos' not in st.session_state:
        st.session_state['datos'] = None
    if 'uploaded_file_hash' not in st.session_state:
        st.session_state['uploaded_file_hash'] = 'default'

    # Renderizar sidebar inicialmente para obtener uploaded_file
    # Pasamos un DataFrame vacío si aún no hay datos cargados para que el sidebar no falle.
    filtros = render_sidebar(st.session_state['datos']['data'] if st.session_state['datos'] else None)
    
    current_uploaded_file_hash = hash(filtros["uploaded_file"].getvalue()) if filtros["uploaded_file"] else 'default'

    # Si se cargó un nuevo archivo, o si el hash del archivo ha cambiado, recargar y almacenar datos.
    if current_uploaded_file_hash != st.session_state['uploaded_file_hash']:
        load_and_store_data(filtros["uploaded_file"])
        # Necesitamos re-ejecutar toda la aplicación para que los cambios se reflejen
        st.rerun()
        
    # Si no hay datos cargados (ni por defecto ni subidos), cargar por defecto.
    if st.session_state['datos'] is None:
        load_and_store_data(None)
        # Una vez cargados los datos por defecto, re-ejecutar.
        st.rerun()

    # Desempaquetar los datos de la sesión para su uso.
    datos = st.session_state['datos']
    df_completo = datos['data']

    # --- 2. Aplicar Filtros a los Datos ---
    # Se aplica el filtrado jerárquico basado en la selección del usuario.
    df_filtrado = apply_filters_jerarquicos(
        df=df_completo,
        unidades_seleccionadas=filtros["filtro_unidad"],
        años=filtros["filtro_año"],
        sexos=filtros["filtro_sexo"],
        edades=filtros["filtro_edad"]
    )
    
    # Obtener estadísticas de los datos filtrados y mostrarlas en la sidebar.
    stats = get_summary_stats(df_filtrado)
    render_summary_stats(stats, filtros["total_general"], filtros["filtro_unidad"])

    # --- 3. Enrutador de Páginas ---
    # Un diccionario mapea la selección del usuario a la función de renderizado correspondiente.
    # A cada función se le pasan los dataframes que necesita.
    page_router = {
        "inicio": lambda: render_main_page(df_filtrado, df_completo, stats),
        "adultos": lambda: morbilidad_adultos.render(df_filtrado, datos['eno'], datos['cronicas'], datos['diagnosticos']),
        "pediatrica": lambda: morbilidad_pediatrica.render(df_filtrado, datos['eno'], datos['cronicas'], datos['diagnosticos']),
        "capitulos": lambda: capitulos.render(df_filtrado, datos['capitulos']),
        "eno": lambda: eno.render(df_filtrado, datos['eno']),
        "cronicas": lambda: cronicas.render(df_filtrado, datos['cronicas']),
        "geografico": lambda: geografico.render(df_filtrado, datos['eno'], datos['cronicas'])
    }
    
    # Ejecutar la función de renderizado de la página seleccionada.
    selected_page_func = page_router.get(filtros["selected_page"])
    if selected_page_func:
        selected_page_func()
    else:
        st.error("Página no encontrada.")

    # --- 4. Footer ---
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #888; font-size: 14px;'>
            <p>Dashboard Epidemiológico IGSS Escuintla | Datos: 2018-2025</p>
            <p>Desarrollado con Streamlit + Plotly + Pandas</p>
        </div>
        """, 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()

