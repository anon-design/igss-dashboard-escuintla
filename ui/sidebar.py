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
    # Refactorización con keys únicas y gestión de estado para corregir error.
    main_options = {
        "🏠 Inicio": "inicio",
        "👨 Morbilidad Adultos": "adultos",
        "👶 Morbilidad Pediátrica": "pediatrica",
        "📚 Capítulos CIE-10": "capitulos",
        "⚠️ Notificación Obligatoria": "eno",
        "💊 Enfermedades Crónicas": "cronicas",
        "🗺️ Análisis Geográfico": "geografico",
    }
    procedencia_options = {
        "🌍 Procedencia: General": "procedencia_general",
        "👨🌍 Procedencia: Adultos": "procedencia_adultos",
        "👶🌍 Procedencia: Pediátrica": "procedencia_pediatrica",
        "📚🌍 Procedencia: Capítulos": "procedencia_capitulos",
        "⚠️🌍 Procedencia: ENO": "procedencia_eno",
        "💊🌍 Procedencia: Crónicas": "procedencia_cronicas",
    }
    avanzado_options = {
        "🔀 Flujos Sankey": "procedencia_sankey",
        "📊 Análisis Cruzado": "procedencia_cruzado"
    }
    page_mapping = {**main_options, **procedencia_options, **avanzado_options}

    if 'selected_page_key' not in st.session_state:
        st.session_state.selected_page_key = "🏠 Inicio"

    # Se captura la selección activa ANTES de renderizar los widgets
    active_selection = st.session_state.selected_page_key

    # --- Renderizado del menú por secciones con keys únicas ---
    st.sidebar.markdown("##### Análisis General")
    r1 = st.sidebar.radio(
        "Módulos Principales", main_options.keys(), label_visibility="collapsed",
        key="radio_main",
        index=list(main_options.keys()).index(active_selection) if active_selection in main_options else None
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("##### Análisis de Procedencia")
    r2 = st.sidebar.radio(
        "Módulos de Procedencia", procedencia_options.keys(), label_visibility="collapsed",
        key="radio_procedencia",
        index=list(procedencia_options.keys()).index(active_selection) if active_selection in procedencia_options else None
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("##### Análisis Avanzado")
    r3 = st.sidebar.radio(
        "Módulos Avanzados", avanzado_options.keys(), label_visibility="collapsed",
        key="radio_avanzado",
        index=list(avanzado_options.keys()).index(active_selection) if active_selection in avanzado_options else None
    )
    
    # --- Lógica para detectar el cambio y forzar el rerun ---
    # Comprobar si la selección de algún radio ha cambiado respecto al estado guardado
    new_selection = None
    if r1 != active_selection and r1 in main_options:
        new_selection = r1
    elif r2 != active_selection and r2 in procedencia_options:
        new_selection = r2
    elif r3 != active_selection and r3 in avanzado_options:
        new_selection = r3

    # Si hay una nueva selección, actualizar el estado y re-ejecutar el script
    if new_selection:
        st.session_state.selected_page_key = new_selection
        st.rerun()

    st.sidebar.markdown("---")
    
    selected_page_value = page_mapping.get(st.session_state.selected_page_key, "inicio")

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
            <small>
            <b>Formato del archivo CSV requerido:</b>
            <ul>
                <li><b>CIE10</b>: Código (ej. "I10")</li>
                <li><b>Unidad</b>: Nombre de la unidad (ej. "Hospital Escuintla")</li>
                <li><b>Año</b>: Año del registro (ej. "2023")</li>
                <li><b>Sexo</b>: Sexo del paciente (ej. "FEMENINO")</li>
                <li><b>Edad</b>: Rango de edad (ej. "31-35")</li>
                <li><b>Casos</b>: Número de casos (ej. "150")</li>
            </ul>
            </small>
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
