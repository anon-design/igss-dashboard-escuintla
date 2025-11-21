"""
Módulo para renderizar la barra lateral (sidebar) de la aplicación.
"""
import streamlit as st
from utils.filters import get_unidades_especificas, get_total_general
from utils.colors import format_large_number

def render_sidebar(df):
    """
    Renderiza la barra lateral y sus filtros.

    Args:
        df (pd.DataFrame or None): El DataFrame principal. Si es None, los filtros se deshabilitan.

    Returns:
        dict: Un diccionario con todos los valores de los filtros seleccionados.
    """
    st.sidebar.markdown(
        "<h2 style='text-align: center; color: #0066A8;'>IGSS Escuintla Logo</h2>",
        unsafe_allow_html=True
    )

    st.sidebar.title("📊 Dashboard Epidemiológico")
    st.sidebar.markdown("---")

    # --- 1. Menú de Navegación ---
    menu_options = {
        "🏠 Inicio": "inicio",
        "👨 Morbilidad Adultos": "adultos",
        "👶 Morbilidad Pediátrica": "pediatrica",
        "📚 Análisis por Capítulos CIE-10": "capitulos",
        "⚠️ Enfermedades de Notificación Obligatoria": "eno",
        "💊 Enfermedades Crónicas": "cronicas",
        "🗺️ Análisis Geográfico": "geografico"
    }

    selected_page = st.sidebar.radio(
        "Selecciona un módulo:",
        list(menu_options.keys()),
        index=0
    )
    st.sidebar.markdown("---")

    # --- 2. Filtros Globales ---
    st.sidebar.subheader("🔍 Filtros Generales")

    # Si no hay datos, deshabilita los filtros
    if df is None:
        unidades_especificas_disponibles, años_disponibles, sexos_disponibles, edades_disponibles = [], [], [], []
        total_general = 0
        is_disabled = True
        st.sidebar.warning("Cargue un archivo CSV para habilitar los filtros.")
    else:
        unidades_especificas_disponibles = get_unidades_especificas(df)
        años_disponibles = sorted(df['Año'].unique().tolist())
        sexos_disponibles = sorted(df['Sexo'].unique().tolist())
        edades_disponibles = sorted(df['Edad'].unique().tolist())
        total_general = get_total_general(df)
        is_disabled = False

    st.sidebar.info(f"""
    **Total General Escuintla**
    {format_large_number(total_general)} casos
    """)

    # Filtros
    filtro_unidad = st.sidebar.multiselect(
        "Filtrar por Unidad Específica:",
        options=unidades_especificas_disponibles,
        default=[],
        help="Selecciona unidades específicas para ver desglose. Vacío = muestra General completo",
        disabled=is_disabled
    )

    filtro_año = st.sidebar.multiselect(
        "Año:",
        options=años_disponibles,
        default=años_disponibles,
        disabled=is_disabled
    )

    filtro_sexo = st.sidebar.multiselect(
        "Sexo:",
        options=sexos_disponibles,
        default=sexos_disponibles,
        disabled=is_disabled
    )

    with st.sidebar.expander("Filtro Avanzado: Edad"):
        filtro_edad = st.multiselect(
            "Rangos de edad:",
            options=edades_disponibles,
            default=edades_disponibles,
            disabled=is_disabled
        )

    st.sidebar.markdown("---")
    
    # --- 3. Carga de Archivos ---
    with st.sidebar.expander("⬆️ Cargar Nuevos Datos"):
        uploaded_file = st.file_uploader(
            "Cargar archivo CSV de morbilidad",
            type=['csv']
        )
        st.markdown(
            """
            <small>El archivo debe contener las columnas: `CIE10`, `Unidad`, `Año`, `Sexo`, `Edad`, `Casos`.</small>
            """, 
            unsafe_allow_html=True
        )

    # --- 4. Retornar valores ---
    return {
        "selected_page": menu_options[selected_page],
        "filtro_unidad": filtro_unidad,
        "filtro_año": filtro_año,
        "filtro_sexo": filtro_sexo,
        "filtro_edad": filtro_edad,
        "total_general": total_general,
        "uploaded_file": uploaded_file
    }

def render_summary_stats(stats, total_general, filtro_unidad):
    """
    Renderiza las estadísticas de resumen en la barra lateral.
    """
    st.sidebar.markdown("---")
    st.sidebar.subheader("📈 Datos Mostrados")

    if filtro_unidad:
        st.sidebar.metric("Casos Filtrados", format_large_number(stats['total_casos']))
        pct_del_total = (stats['total_casos'] / total_general * 100) if total_general > 0 else 0
        st.sidebar.caption(f"{pct_del_total:.1f}% del total general")
    else:
        st.sidebar.metric("Total General", format_large_number(stats['total_casos']))

    st.sidebar.metric("Diagnósticos Únicos", format_large_number(stats['total_diagnosticos']))
    st.sidebar.metric("Años Cubiertos", stats['años_cubiertos'])
