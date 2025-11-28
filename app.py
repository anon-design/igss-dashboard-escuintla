"""
Dashboard Epidemiológico IGSS Escuintla
Aplicación principal con navegación por módulos y una arquitectura modular.
"""

import streamlit as st
import sys
from pathlib import Path

from config import PAGE_CONFIG, CUSTOM_CSS
from utils.data_loader import load_all_data, load_procedencia_data
from utils.filters import apply_filters_jerarquicos, get_summary_stats, apply_filters_procedencia
from utils.auth import check_password, render_logout_button

# --- Importar Módulos de UI ---
from ui.sidebar import render_sidebar, render_summary_stats
from ui.main_page import render_main_page

# --- Importar Módulos de Páginas de Análisis ---
from modules import morbilidad_adultos, morbilidad_pediatrica, capitulos, eno, cronicas, geografico
from modules import procedencia_general
from modules.procedencia import (
    morbilidad_adultos as proc_adultos,
    morbilidad_pediatrica as proc_pediatrica,
    capitulos as proc_capitulos,
    eno as proc_eno,
    cronicas as proc_cronicas
)
from modules.procedencia_v2 import (
    sankey_flujos as proc_sankey,
    analisis_cruzado as proc_cruzado
)

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

    # --- 0. AUTENTICACIÓN ---
    # Verificar login antes de mostrar el dashboard
    if not check_password():
        st.stop()  # Detener ejecución si no está autenticado

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

    # Botón de cerrar sesión en el sidebar
    render_logout_button()

    # --- 3. Cargar datos de procedencia (lazy loading) ---
    # Solo se carga cuando se accede a la página de procedencia
    df_procedencia = None
    df_procedencia_todas_unidades = None
    if filtros["selected_page"].startswith("procedencia"):
        df_procedencia_raw = load_procedencia_data()

        todas_las_unidades = df_procedencia_raw['Unidad'].unique().tolist()

        # Datos filtrados con todas las unidades para evitar perder subconjuntos
        df_procedencia = apply_filters_procedencia(
            df_procedencia_raw,
            unidades=todas_las_unidades,
            anios=filtros["filtro_año"],
            departamentos=None,
            municipios=None,
            sexos=filtros["filtro_sexo"],
            edades=filtros["filtro_edad"]
        )

        # Alias explícito para módulos avanzados (reutiliza el mismo dataset completo)
        df_procedencia_todas_unidades = df_procedencia

    # --- 4. Enrutador de Páginas ---
    # Un diccionario mapea la selección del usuario a la función de renderizado correspondiente.
    # A cada función se le pasan los dataframes que necesita.
    page_router = {
        # Módulos originales (datos de atención)
        "inicio": lambda: render_main_page(df_filtrado, df_completo, stats),
        "adultos": lambda: morbilidad_adultos.render(df_filtrado, datos['eno'], datos['cronicas'], datos['diagnosticos']),
        "pediatrica": lambda: morbilidad_pediatrica.render(df_filtrado, datos['eno'], datos['cronicas'], datos['diagnosticos']),
        "capitulos": lambda: capitulos.render(df_filtrado, datos['capitulos']),
        "eno": lambda: eno.render(df_filtrado, datos['eno']),
        "cronicas": lambda: cronicas.render(df_filtrado, datos['cronicas']),
        "geografico": lambda: geografico.render(df_filtrado, datos['eno'], datos['cronicas'], datos['diagnosticos']),
        "separator": lambda: st.info("Seleccione un módulo de análisis"),
        # Módulos de PROCEDENCIA (datos geográficos)
        "procedencia_general": lambda: procedencia_general.render(df_procedencia),
        "procedencia_adultos": lambda: proc_adultos.render(df_procedencia, datos['eno'], datos['cronicas'], datos['diagnosticos']),
        "procedencia_pediatrica": lambda: proc_pediatrica.render(df_procedencia, datos['eno'], datos['cronicas'], datos['diagnosticos']),
        "procedencia_capitulos": lambda: proc_capitulos.render(df_procedencia, datos['capitulos']),
        "procedencia_eno": lambda: proc_eno.render(df_procedencia, datos['eno']),
        "procedencia_cronicas": lambda: proc_cronicas.render(df_procedencia, datos['cronicas']),
        # Módulos de PROCEDENCIA V2 (análisis avanzado)
        # Estos módulos usan df_procedencia_todas_unidades para ver flujos entre unidades
        "separator2": lambda: st.info("Seleccione un módulo de análisis avanzado"),
        "procedencia_sankey": lambda: proc_sankey.render(df_procedencia_todas_unidades),
        "procedencia_cruzado": lambda: proc_cruzado.render(df_procedencia_todas_unidades)
    }
    
    # Ejecutar la función de renderizado de la página seleccionada.
    selected_page_func = page_router.get(filtros["selected_page"])
    if selected_page_func:
        selected_page_func()
    else:
        st.error("Página no encontrada.")

    # --- 5. Footer ---
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
