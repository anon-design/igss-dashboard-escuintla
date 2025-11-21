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

def main():
    """
    Función principal que orquesta la aplicación Streamlit.
    """
    # --- 1. Carga de Datos ---
    # Carga todos los dataframes necesarios utilizando una función cacheada.
    with st.spinner("Cargando datos..."):
        datos = load_all_data()
        if datos['data'].empty:
            st.error("⚠️ No se pudieron cargar los datos. Verifica la configuración y el archivo de datos.")
            st.stop()
    
    df_completo = datos['data']

    # --- 2. Renderizar Sidebar y Obtener Filtros ---
    # La lógica de la barra lateral está encapsulada en su propio módulo.
    filtros = render_sidebar(df_completo)

    # --- 3. Aplicar Filtros a los Datos ---
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

    # --- 4. Enrutador de Páginas ---
    # Un diccionario mapea la selección del usuario a la función de renderizado correspondiente.
    # A cada función se le pasan los dataframes que necesita.
    page_router = {
        "inicio": lambda: render_main_page(df_filtrado, df_completo, stats),
        "adultos": lambda: morbilidad_adultos.render(df_filtrado, datos['eno'], datos['cronicas'], datos['capitulos'], datos['diagnosticos']),
        "pediatrica": lambda: morbilidad_pediatrica.render(df_filtrado, datos['eno'], datos['cronicas'], datos['capitulos'], datos['diagnosticos']),
        "capitulos": lambda: capitulos.render(df_filtrado, datos['capitulos']),
        "eno": lambda: eno.render(df_filtrado, datos['eno']),
        "cronicas": lambda: cronicas.render(df_filtrado, datos['cronicas']),
        "geografico": lambda: geografico.render(df_filtrado)
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

