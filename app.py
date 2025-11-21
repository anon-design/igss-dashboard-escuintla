"""
Dashboard Epidemiológico IGSS Escuintla
Aplicación principal con navegación por módulos
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Configurar path para imports
sys.path.append(str(Path(__file__).parent))

from config import COLORS, APP_SUBTITLE
from utils.data_loader import (
    load_data,
    load_cie10_capitulos,
    load_cie10_eno,
    load_cie10_cronicas,
    load_diagnosticos_nombres,
    get_data_summary
)
from utils.filters import (
    apply_filters,
    get_summary_stats,
    get_total_general,
    get_unidades_especificas,
    apply_filters_jerarquicos,
    get_distribucion_unidades,
    validar_seleccion_unidades
)
from utils.colors import create_metric_card_html, format_large_number


# ============================================================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================================================

st.set_page_config(
    page_title="Dashboard Epidemiológico IGSS Escuintla",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================================
# ESTILO CSS PERSONALIZADO
# ============================================================================

st.markdown(f"""
    <style>
    /* Adaptable a tema claro/oscuro */
    h1 {{
        color: {COLORS['primary']};
        font-weight: 700;
    }}
    h2 {{
        color: {COLORS['secondary']};
        font-weight: 600;
    }}
    h3 {{
        font-weight: 600;
    }}
    .stButton>button {{
        background-color: {COLORS['primary']};
        color: white !important;
        border-radius: 5px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }}
    .stButton>button:hover {{
        background-color: {COLORS['secondary']};
        opacity: 0.9;
    }}
    div[data-testid="stSidebarNav"] {{
        background-color: {COLORS['primary']}15;
    }}
    /* Mejorar contraste en modo oscuro */
    @media (prefers-color-scheme: dark) {{
        h3 {{
            color: #E0E0E0;
        }}
    }}
    </style>
""", unsafe_allow_html=True)


# ============================================================================
# CARGAR DATOS
# ============================================================================

@st.cache_data
def load_all_data():
    """Carga todos los datos necesarios con caché"""
    return {
        'data': load_data(),
        'capitulos': load_cie10_capitulos(),
        'eno': load_cie10_eno(),
        'cronicas': load_cie10_cronicas(),
        'diagnosticos': load_diagnosticos_nombres()
    }

# Cargar datos
with st.spinner('Cargando datos...'):
    datos = load_all_data()
    df = datos['data']
    df_capitulos = datos['capitulos']
    df_eno = datos['eno']
    df_cronicas = datos['cronicas']
    df_diagnosticos = datos['diagnosticos']

# Verificar que los datos se cargaron correctamente
if df.empty:
    st.error("⚠️ No se pudieron cargar los datos. Verifica que el archivo de datos esté en la ubicación correcta.")
    st.stop()


# ============================================================================
# SIDEBAR - NAVEGACIÓN
# ============================================================================

st.sidebar.image("https://via.placeholder.com/250x80/0066A8/FFFFFF?text=IGSS+Escuintla",
                 use_column_width=True)

st.sidebar.title("📊 Dashboard Epidemiológico")
st.sidebar.markdown("---")

# Menú de navegación
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


# ============================================================================
# SIDEBAR - FILTROS GLOBALES
# ============================================================================

st.sidebar.subheader("🔍 Filtros Generales")

# Obtener listas únicas para filtros
unidades_especificas_disponibles = get_unidades_especificas(df)
años_disponibles = sorted(df['Año'].unique().tolist())
sexos_disponibles = sorted(df['Sexo'].unique().tolist())
edades_disponibles = sorted(df['Edad'].unique().tolist())

# TOTAL GENERAL (siempre visible)
total_general = get_total_general(df)

# Filtro de Unidad (JERÁRQUICO)
st.sidebar.info(f"""
**Total General Escuintla**
{format_large_number(total_general)} casos
""")

filtro_unidad = st.sidebar.multiselect(
    "Filtrar por Unidad Específica:",
    options=unidades_especificas_disponibles,
    default=[],
    help="Selecciona unidades específicas para ver desglose. Vacío = muestra General completo"
)

# Filtro de Año
filtro_año = st.sidebar.multiselect(
    "Año:",
    options=años_disponibles,
    default=años_disponibles,
    help="Selecciona uno o más años"
)

# Filtro de Sexo
filtro_sexo = st.sidebar.multiselect(
    "Sexo:",
    options=sexos_disponibles,
    default=sexos_disponibles,
    help="Selecciona uno o más sexos"
)

# Filtro de Edad (opcional - colapsar por defecto)
with st.sidebar.expander("Filtro Avanzado: Edad"):
    filtro_edad = st.multiselect(
        "Rangos de edad:",
        options=edades_disponibles,
        default=edades_disponibles,
        help="Selecciona uno o más rangos de edad"
    )

# Aplicar filtros JERÁRQUICOS
df_filtrado = apply_filters_jerarquicos(
    df,
    unidades_seleccionadas=filtro_unidad if filtro_unidad else None,
    años=filtro_año if filtro_año else None,
    sexos=filtro_sexo if filtro_sexo else None,
    edades=filtro_edad if filtro_edad else None
)

# Estadísticas del filtrado
stats = get_summary_stats(df_filtrado)

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


# ============================================================================
# CONTENIDO PRINCIPAL - ROUTER
# ============================================================================

page = menu_options[selected_page]

# Página de Inicio
if page == "inicio":
    st.title("🏥 Dashboard Epidemiológico IGSS Escuintla")
    st.markdown(f"### {APP_SUBTITLE}")

    st.markdown("---")

    # Métricas principales en 4 columnas
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            create_metric_card_html(
                "Total de Casos",
                stats['total_casos'],
                color='primary'
            ),
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            create_metric_card_html(
                "Diagnósticos Únicos",
                stats['total_diagnosticos'],
                color='success'
            ),
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            create_metric_card_html(
                "Unidades Médicas",
                stats['unidades'],
                color='info'
            ),
            unsafe_allow_html=True
        )

    with col4:
        st.markdown(
            create_metric_card_html(
                "Casos Promedio/Año",
                stats['casos_promedio_anual'],
                color='warning'
            ),
            unsafe_allow_html=True
        )

    st.markdown("---")

    # Información del dashboard
    st.subheader("📋 Acerca de este Dashboard")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **Módulos Disponibles:**

        - **Morbilidad Adultos**: Análisis de los 25 diagnósticos más frecuentes en población adulta (>15 años)
        - **Morbilidad Pediátrica**: Análisis de los 25 diagnósticos más frecuentes en población pediátrica (0-15 años)
        - **Capítulos CIE-10**: Distribución de casos por capítulo de la Clasificación Internacional de Enfermedades
        - **ENO**: Vigilancia de Enfermedades de Notificación Obligatoria
        - **Enfermedades Crónicas**: Análisis de enfermedades crónicas no transmisibles
        - **Análisis Geográfico**: Distribución de casos por unidad médica
        """)

    with col2:
        st.markdown("""
        **Características:**

        - ✓ Visualizaciones interactivas con Plotly
        - ✓ Filtros dinámicos por unidad, año, sexo y edad
        - ✓ Análisis temporal de tendencias
        - ✓ Comparación entre períodos
        - ✓ Exportación de datos y gráficos
        - ✓ Actualización automática con datos recientes
        """)

    st.markdown("---")

    # Resumen de datos
    st.subheader("📊 Resumen de Datos Cargados")

    data_summary = get_data_summary(df)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.info(f"""
        **Cobertura Temporal**

        - Año inicial: {data_summary['año_min']}
        - Año final: {data_summary['año_max']}
        - Total años: {len(data_summary['años'])}
        """)

    with col2:
        st.success(f"""
        **Datos Generales**

        - Total registros: {format_large_number(data_summary['total_registros'])}
        - Total casos: {format_large_number(data_summary['total_casos'])}
        - Códigos CIE-10: {format_large_number(data_summary['codigos_unicos'])}
        """)

    with col3:
        st.warning(f"""
        **Unidades Médicas**

        {chr(10).join(['- ' + u for u in data_summary['unidades'][:6]])}
        """)

    st.markdown("---")

    # Gráfico de tendencia anual
    st.subheader("📈 Tendencia de Casos por Año")

    casos_por_año = df_filtrado.groupby('Año')['Casos'].sum().reset_index()

    import plotly.express as px
    from utils.colors import apply_igss_theme

    fig = px.line(
        casos_por_año,
        x='Año',
        y='Casos',
        markers=True,
        title='Evolución de Casos por Año'
    )

    fig.update_traces(
        line=dict(color=COLORS['primary'], width=3),
        marker=dict(size=10, color=COLORS['secondary'])
    )

    fig = apply_igss_theme(fig)

    st.plotly_chart(fig, use_container_width=True)

    # Instrucciones
    st.markdown("---")
    st.info("""
    **💡 Instrucciones de Uso:**

    1. Utiliza el menú lateral para navegar entre los diferentes módulos
    2. Aplica filtros en la barra lateral para segmentar los datos
    3. Cada módulo incluye visualizaciones interactivas que puedes explorar
    4. Los gráficos permiten zoom, exportación y tooltips informativos
    """)

# Importar módulos de reportes
elif page == "adultos":
    from modules import morbilidad_adultos
    morbilidad_adultos.render(df_filtrado, df_eno, df_cronicas, df_capitulos, df_diagnosticos)

elif page == "pediatrica":
    from modules import morbilidad_pediatrica
    morbilidad_pediatrica.render(df_filtrado, df_eno, df_cronicas, df_capitulos, df_diagnosticos)

elif page == "capitulos":
    from modules import capitulos
    capitulos.render(df_filtrado, df_capitulos)

elif page == "eno":
    from modules import eno
    eno.render(df_filtrado, df_eno)

elif page == "cronicas":
    from modules import cronicas
    cronicas.render(df_filtrado, df_cronicas)

elif page == "geografico":
    from modules import geografico
    geografico.render(df_filtrado, df_eno, df_cronicas, df_capitulos)


# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown(f"""
<div style='text-align: center; color: #888; font-size: 14px;'>
    <p>Dashboard Epidemiológico IGSS Escuintla | Datos: 2018-2025</p>
    <p>Desarrollado con Streamlit + Plotly + Pandas</p>
</div>
""", unsafe_allow_html=True)
