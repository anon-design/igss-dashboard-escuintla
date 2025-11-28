"""
Módulo para renderizar la barra lateral (sidebar) de la aplicación.
"""
from pathlib import Path
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
    logo_candidates = [
        Path("static/logo.png"),
        Path("static/logo.jpg"),
        Path("static/logo.jpeg")
    ]
    logo_path = next((p for p in logo_candidates if p.exists()), None)

    if logo_path:
        st.sidebar.image(str(logo_path), use_column_width=True)
    else:
        st.sidebar.markdown(
            "<h2 style='text-align: center; color: #0066A8;'>IGSS Escuintla</h2>",
            unsafe_allow_html=True
        )

    st.sidebar.title("📊 Dashboard Epidemiológico")
    st.sidebar.markdown("---")

    # --- 1. Navegación con 2 niveles (sección + módulo) ---
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

    nav_sections = {
        "📈 Análisis General": main_options,
        "🧭 Procedencia": procedencia_options,
        "🧪 Análisis Avanzado": avanzado_options,
    }

    if 'selected_page_key' not in st.session_state:
        st.session_state.selected_page_key = "inicio"

    # Determinar la sección actual según la página seleccionada
    def find_section(page_key):
        for section_label, options in nav_sections.items():
            if page_key in options.values():
                return section_label
        return "📈 Análisis General"

    current_section = find_section(st.session_state.selected_page_key)
    section_labels = list(nav_sections.keys())
    section_index = section_labels.index(current_section)

    st.sidebar.caption("Navega por área y luego elige el módulo.")
    section_choice = st.sidebar.radio(
        "Áreas",
        section_labels,
        index=section_index,
        key="nav_section"
    )

    # Módulos de la sección elegida
    section_options = nav_sections[section_choice]
    module_labels = list(section_options.keys())
    module_values = list(section_options.values())
    module_index = module_values.index(st.session_state.selected_page_key) if st.session_state.selected_page_key in module_values else 0

    st.sidebar.markdown("---")
    module_choice_label = st.sidebar.radio(
        "Módulos",
        module_labels,
        index=module_index,
        key="nav_module"
    )
    selected_page_value = section_options[module_choice_label]
    st.session_state.selected_page_key = selected_page_value

    st.sidebar.markdown("---")
    
    # Control global de etiquetas en gráficas
    show_chart_labels = st.sidebar.checkbox(
        "Mostrar etiquetas numéricas en gráficas",
        value=st.session_state.get("show_chart_labels", True),
        key="show_chart_labels"
    )

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
        "selected_page": selected_page_value,
        "filtro_unidad": filtro_unidad,
        "filtro_año": filtro_año,
        "filtro_sexo": filtro_sexo,
        "filtro_edad": filtro_edad,
        "total_general": total_general,
        "uploaded_file": uploaded_file,
        "show_chart_labels": show_chart_labels
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
