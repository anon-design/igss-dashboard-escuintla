"""
Módulo para renderizar la página de Inicio.
"""
import streamlit as st
import plotly.express as px
from config import APP_SUBTITLE, COLORS
from utils.colors import create_metric_card_html, format_large_number, apply_igss_theme
from utils.data_loader import get_data_summary

def render_main_page(df_filtrado, df_completo, stats):
    """
    Renderiza la página de inicio del dashboard.

    Args:
        df_filtrado (pd.DataFrame): DataFrame con los datos después de aplicar los filtros.
        df_completo (pd.DataFrame): DataFrame con todos los datos originales.
        stats (dict): Diccionario con estadísticas de resumen de los datos filtrados.
    """
    st.title("🏥 Dashboard Epidemiológico IGSS Escuintla")
    st.markdown(f"### {APP_SUBTITLE}")
    st.markdown("---")

    # --- 1. Métricas Principales ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(create_metric_card_html("Total de Casos", stats['total_casos'], color='primary'), unsafe_allow_html=True)
    with col2:
        st.markdown(create_metric_card_html("Diagnósticos Únicos", stats['total_diagnosticos'], color='success'), unsafe_allow_html=True)
    with col3:
        st.markdown(create_metric_card_html("Unidades Médicas", stats['unidades'], color='info'), unsafe_allow_html=True)
    with col4:
        st.markdown(create_metric_card_html("Casos Promedio/Año", stats['casos_promedio_anual'], color='warning'), unsafe_allow_html=True)
    
    st.markdown("---")

    # --- 2. Gráfico de Tendencia Anual ---
    st.subheader("📈 Tendencia de Casos por Año")
    casos_por_año = df_filtrado.groupby('Año')['Casos'].sum().reset_index()

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
    st.plotly_chart(fig, width='stretch')

    st.markdown("---")

    # --- 3. Información del Dashboard y Resumen de Datos ---
    col1, col2 = st.columns(2)
    with col1:
        with st.expander("📋 Acerca de este Dashboard", expanded=True):
            st.markdown("""
            **Módulos Disponibles:**
            - **Morbilidad Adultos**: Análisis de los 25 diagnósticos más frecuentes en población adulta (>15 años).
            - **Morbilidad Pediátrica**: Análisis de los 25 diagnósticos más frecuentes en población pediátrica (0-15 años).
            - **Capítulos CIE-10**: Distribución de casos por capítulo de la Clasificación Internacional de Enfermedades.
            - **ENO**: Vigilancia de Enfermedades de Notificación Obligatoria.
            - **Enfermedades Crónicas**: Análisis de enfermedades crónicas no transmisibles.
            - **Análisis Geográfico**: Distribución de casos por unidad médica.
            """)
    
    with col2:
        with st.expander("📊 Resumen de Datos Cargados", expanded=True):
            data_summary = get_data_summary(df_completo)
            st.info(f"""
            **Cobertura Temporal:** {data_summary['año_min']} - {data_summary['año_max']}
            **Total Registros:** {format_large_number(data_summary['total_registros'])}
            **Total Casos:** {format_large_number(data_summary['total_casos'])}
            **Códigos CIE-10:** {format_large_number(data_summary['codigos_unicos'])}
            """)

    st.markdown("---")
    
    # --- 4. Instrucciones de Uso ---
    st.info("""
    **💡 Instrucciones de Uso:**
    1. Utiliza el menú lateral para navegar entre los diferentes módulos.
    2. Aplica filtros en la barra lateral para segmentar los datos.
    3. Cada módulo incluye visualizaciones interactivas que puedes explorar.
    4. Los gráficos permiten zoom, exportación y tooltips informativos.
    """)
