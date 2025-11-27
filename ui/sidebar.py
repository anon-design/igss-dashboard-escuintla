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
    # Se refactoriza el menú para usar secciones y callbacks, mejorando la UI.

    # Opciones del menú divididas en diccionarios para cada sección.
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

    # Mapa completo para buscar el valor corto a partir de la etiqueta
    page_mapping = {**main_options, **procedencia_options, **avanzado_options}

    # Inicializar el estado de la sesión si no existe
    if 'selected_page_key' not in st.session_state:
        st.session_state.selected_page_key = "🏠 Inicio"

    # Callback para actualizar la página seleccionada
    def set_page():
        # 'radio_selection' es la clave temporal que Streamlit usa internamente para el widget
        st.session_state.selected_page_key = st.session_state.radio_selection

    # --- Renderizado del menú por secciones ---
    st.sidebar.markdown("##### Análisis General")
    st.sidebar.radio(
        "Módulos Principales",
        options=main_options.keys(),
        key="radio_selection",  # Clave única para el estado del widget
        on_change=set_page,
        label_visibility="collapsed",
        # El índice se establece buscando la clave actual en las opciones de esta sección
        index=list(main_options.keys()).index(st.session_state.selected_page_key)
        if st.session_state.selected_page_key in main_options else None,
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("##### Análisis de Procedencia")
    st.sidebar.radio(
        "Módulos de Procedencia",
        options=procedencia_options.keys(),
        key="radio_selection",
        on_change=set_page,
        label_visibility="collapsed",
        index=list(procedencia_options.keys()).index(st.session_state.selected_page_key)
        if st.session_state.selected_page_key in procedencia_options else None,
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("##### Análisis Avanzado")
    st.sidebar.radio(
        "Módulos Avanzados",
        options=avanzado_options.keys(),
        key="radio_selection",
        on_change=set_page,
        label_visibility="collapsed",
        index=list(avanzado_options.keys()).index(st.session_state.selected_page_key)
        if st.session_state.selected_page_key in avanzado_options else None,
    )
    
    st.sidebar.markdown("---")

    # El valor a retornar se obtiene del mapa usando la clave guardada en el estado
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
