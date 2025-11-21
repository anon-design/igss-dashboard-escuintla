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
        df (pd.DataFrame): El DataFrame principal con todos los datos.

    Returns:
        dict: Un diccionario con todos los valores de los filtros seleccionados.
    """
    st.sidebar.image("https://via.placeholder.com/250x80/0066A8/FFFFFF?text=IGSS+Escuintla",
                     use_column_width=True)

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

    # Obtener listas únicas para filtros
    unidades_especificas_disponibles = get_unidades_especificas(df)
    años_disponibles = sorted(df['Año'].unique().tolist())
    sexos_disponibles = sorted(df['Sexo'].unique().tolist())
    edades_disponibles = sorted(df['Edad'].unique().tolist())

    # Total General (siempre visible)
    total_general = get_total_general(df)
    st.sidebar.info(f"""
    **Total General Escuintla**
    {format_large_number(total_general)} casos
    """)

    # Filtros
    filtro_unidad = st.sidebar.multiselect(
        "Filtrar por Unidad Específica:",
        options=unidades_especificas_disponibles,
        default=[],
        help="Selecciona unidades específicas para ver desglose. Vacío = muestra General completo"
    )

    filtro_año = st.sidebar.multiselect(
        "Año:",
        options=años_disponibles,
        default=años_disponibles,
    )

    filtro_sexo = st.sidebar.multiselect(
        "Sexo:",
        options=sexos_disponibles,
        default=sexos_disponibles,
    )

    with st.sidebar.expander("Filtro Avanzado: Edad"):
        filtro_edad = st.multiselect(
            "Rangos de edad:",
            options=edades_disponibles,
            default=edades_disponibles,
        )

    # --- 3. Retornar valores ---
    return {
        "selected_page": menu_options[selected_page],
        "filtro_unidad": filtro_unidad,
        "filtro_año": filtro_año,
        "filtro_sexo": filtro_sexo,
        "filtro_edad": filtro_edad,
        "total_general": total_general
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
