"""
Módulo de Análisis de Procedencia Geográfica - Vista General
Distribución de casos por departamento y municipio de origen de los pacientes

IMPORTANTE: Estructura Jerárquica
- "General Escuintla Procedencia" = TOTAL COMPLETO (100% de casos)
- Unidades específicas = SUBCONJUNTOS de General
- "Otros" = General - Suma(Específicas)
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from config import COLORS
from utils.filters import (
    get_total_general_procedencia,
    get_distribucion_departamentos,
    get_distribucion_municipios,
    get_distribucion_unidades_procedencia,
    calcular_casos_otros_procedencia,
    UNIDAD_GENERAL_PROCEDENCIA
)
from utils.colors import (
    create_bar_chart,
    create_line_chart,
    create_pie_chart,
    create_metric_card_html,
    format_large_number
)

# Helper para convertir DataFrame a CSV para descarga
@st.cache_data
def convert_df_to_csv(df):
    return df.to_csv(index=False, encoding='utf-8-sig')


def render(df_procedencia):
    """
    Renderiza el módulo de análisis de procedencia geográfica - vista general

    Args:
        df_procedencia: DataFrame con datos de procedencia (todas las unidades)
    """
    st.title("🌍 Procedencia: Análisis General")
    st.markdown("### De dónde vienen los pacientes atendidos en el IGSS Escuintla")

    st.markdown("---")

    if df_procedencia is None or df_procedencia.empty:
        st.warning("No hay datos de procedencia disponibles.")
        return

    # =========================================================================
    # MÉTRICAS PRINCIPALES
    # =========================================================================

    # Obtener solo datos de General (el total real, sin duplicación)
    df_general = df_procedencia[df_procedencia['Unidad'] == UNIDAD_GENERAL_PROCEDENCIA]

    total_casos = get_total_general_procedencia(df_procedencia)
    total_departamentos = df_general['Departamento'].nunique()
    total_municipios = df_general['Municipio'].nunique()
    total_codigos = df_general['CIE10'].nunique()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            create_metric_card_html(
                "Total de Casos",
                format_large_number(total_casos),
                color='primary'
            ),
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            create_metric_card_html(
                "Departamentos",
                total_departamentos,
                color='success'
            ),
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            create_metric_card_html(
                "Municipios",
                total_municipios,
                color='info'
            ),
            unsafe_allow_html=True
        )

    with col4:
        st.markdown(
            create_metric_card_html(
                "Diagnósticos",
                format_large_number(total_codigos),
                color='warning'
            ),
            unsafe_allow_html=True
        )

    st.markdown("---")

    # =========================================================================
    # DISTRIBUCIÓN POR DEPARTAMENTO
    # =========================================================================

    st.subheader("📊 Distribución por Departamento de Procedencia")

    df_deptos = get_distribucion_departamentos(df_procedencia)

    if not df_deptos.empty:
        col_tabla, col_grafico = st.columns([1, 1])

        with col_tabla:
            # Tabla de departamentos
            st.write("Lista Completa de Departamentos")
            tabla_deptos = df_deptos.copy()
            tabla_deptos['Rank'] = range(1, len(tabla_deptos) + 1)
            tabla_deptos['Casos'] = tabla_deptos['Casos'].apply(format_large_number)
            tabla_deptos['Porcentaje'] = tabla_deptos['Porcentaje'].apply(lambda x: f"{x:.2f}%")

            st.dataframe(
                tabla_deptos[['Rank', 'Departamento', 'Casos', 'Porcentaje']].rename(
                    columns={'Rank': '#', 'Porcentaje': '%'}
                ),
                width='stretch',
                hide_index=True,
                height=400
            )
            
            csv_deptos = convert_df_to_csv(df_deptos)
            st.download_button(
                label="📥 Descargar datos de Departamentos (CSV)",
                data=csv_deptos,
                file_name='distribucion_departamentos.csv',
                mime='text/csv',
            )

        with col_grafico:
            # Gráfico TOP 10 departamentos
            top_deptos = df_deptos.head(10).sort_values('Casos', ascending=True)
            fig_deptos = create_bar_chart(
                top_deptos,
                x='Casos',
                y='Departamento',
                title='TOP 10 Departamentos de Procedencia',
                orientation='h'
            )
            st.plotly_chart(fig_deptos, width='stretch')

    # =========================================================================
    # DISTRIBUCIÓN POR MUNICIPIO
    # =========================================================================

    st.markdown("---")
    
    show_all_mun = st.checkbox("Mostrar todos los municipios (puede ser lento)")
    
    subheader_mun = "🏘️ Distribución de Municipios de Procedencia" if show_all_mun else "🏘️ TOP 20 Municipios de Procedencia"
    top_n_mun = None if show_all_mun else 20
    height_mun = 800 if show_all_mun else 500
    
    st.subheader(subheader_mun)

    df_municipios = get_distribucion_municipios(df_procedencia, top_n=top_n_mun)

    if not df_municipios.empty:
        col_tabla2, col_grafico2 = st.columns([1, 1])

        with col_tabla2:
            tabla_munis = df_municipios.copy()
            tabla_munis['Rank'] = range(1, len(tabla_munis) + 1)
            tabla_munis['Casos'] = tabla_munis['Casos'].apply(format_large_number)
            tabla_munis['Porcentaje'] = tabla_munis['Porcentaje'].apply(lambda x: f"{x:.2f}%")

            st.dataframe(
                tabla_munis[['Rank', 'Municipio', 'Departamento', 'Casos', 'Porcentaje']].rename(
                    columns={'Rank': '#', 'Porcentaje': '%'}
                ),
                width='stretch',
                hide_index=True,
                height=height_mun
            )

            # Para la descarga, siempre obtener la lista completa
            df_municipios_full = get_distribucion_municipios(df_procedencia, top_n=None)
            csv_munis = convert_df_to_csv(df_municipios_full)
            st.download_button(
                label="📥 Descargar datos de Municipios (CSV)",
                data=csv_munis,
                file_name='distribucion_municipios.csv',
                mime='text/csv',
            )

        with col_grafico2:
            # Gráfico TOP 10 municipios (independiente de la selección de tabla)
            top_munis = df_municipios.head(10).sort_values('Casos', ascending=True)
            fig_munis = create_bar_chart(
                top_munis,
                x='Casos',
                y='Municipio',
                title='TOP 10 Municipios de Procedencia',
                orientation='h'
            )
            st.plotly_chart(fig_munis, width='stretch')

    # =========================================================================
    # CONCENTRACIÓN GEOGRÁFICA
    # =========================================================================

    st.markdown("---")
    st.subheader("📈 Análisis de Concentración Geográfica")

    if not df_deptos.empty:
        # Calcular concentración
        top1 = df_deptos.iloc[0] if len(df_deptos) > 0 else None
        top3_pct = df_deptos.head(3)['Porcentaje'].sum() if len(df_deptos) >= 3 else 0
        top5_pct = df_deptos.head(5)['Porcentaje'].sum() if len(df_deptos) >= 5 else 0

        col_c1, col_c2, col_c3 = st.columns(3)

        with col_c1:
            if top1 is not None:
                st.metric(
                    label=f"1er Depto: {top1['Departamento']}",
                    value=f"{top1['Porcentaje']:.1f}%",
                    delta=f"{format_large_number(int(top1['Casos']))} casos"
                )

        with col_c2:
            st.metric(
                label="Concentración TOP 3 Deptos",
                value=f"{top3_pct:.1f}%"
            )

        with col_c3:
            st.metric(
                label="Concentración TOP 5 Deptos",
                value=f"{top5_pct:.1f}%"
            )

    # =========================================================================
    # MAPA TREEMAP DE DISTRIBUCIÓN GEOGRÁFICA
    # =========================================================================

    st.markdown("---")
    st.subheader("🗺️ Mapa de Distribución Geográfica")

    if not df_deptos.empty and not df_municipios.empty:
        import plotly.express as px

        # Crear datos para treemap (Departamento > Municipio)
        df_treemap = df_general.groupby(['Departamento', 'Municipio'])['Casos'].sum().reset_index()

        # Treemap jerárquico
        fig_treemap = px.treemap(
            df_treemap,
            path=['Departamento', 'Municipio'],
            values='Casos',
            title='Distribución Geográfica de Procedencia (Depto → Municipio)',
            color='Casos',
            color_continuous_scale='Blues'
        )
        fig_treemap.update_layout(
            height=600,
            margin=dict(t=50, l=25, r=25, b=25)
        )
        st.plotly_chart(fig_treemap, width='stretch')

        st.caption("""
        **Cómo leer este gráfico:** El tamaño de cada rectángulo representa la cantidad de casos.
        Los rectángulos grandes agrupan departamentos; dentro de cada uno están los municipios.
        Haga clic en un departamento para ver sus municipios en detalle.
        """)

    # =========================================================================
    # DISTRIBUCIÓN POR UNIDAD DE ATENCIÓN
    # =========================================================================

    st.markdown("---")
    st.subheader("🏥 Distribución por Unidad de Atención")

    st.info("""
    **Nota:** El total de casos es de "General Escuintla Procedencia" (100%).
    Las unidades específicas son subconjuntos clasificados.
    "Otros" representa casos no clasificados en unidades específicas.
    """)

    df_unidades = get_distribucion_unidades_procedencia(df_procedencia)

    if not df_unidades.empty:
        col_u1, col_u2 = st.columns([1, 1])

        with col_u1:
            # Tabla
            tabla_unidades = df_unidades.copy()
            tabla_unidades['Casos_fmt'] = tabla_unidades['Casos'].apply(format_large_number)
            tabla_unidades['Pct_fmt'] = tabla_unidades['Porcentaje'].apply(lambda x: f"{x:.2f}%")

            st.dataframe(
                tabla_unidades[['Unidad', 'Casos_fmt', 'Pct_fmt']].rename(
                    columns={'Casos_fmt': 'Casos', 'Pct_fmt': '% del Total'}
                ),
                width='stretch',
                hide_index=True
            )

        with col_u2:
            # Gráfico de pie
            fig_pie = create_pie_chart(
                df_unidades,
                values='Casos',
                names='Unidad',
                title='Distribución por Unidad de Atención'
            )
            st.plotly_chart(fig_pie, width='stretch')

    # =========================================================================
    # INFORMACIÓN SOBRE LOS DATOS
    # =========================================================================

    st.markdown("---")
    with st.expander("ℹ️ Información sobre los datos de procedencia"):
        st.markdown(f"""
        ### Estructura de los datos

        - **Total de casos:** {format_large_number(total_casos)} (período 2018-2025)
        - **Departamentos de origen:** {total_departamentos}
        - **Municipios de origen:** {total_municipios}
        - **Diagnósticos CIE-10:** {format_large_number(total_codigos)}

        ### Interpretación

        Los datos de **procedencia** indican **de dónde vienen** los pacientes que fueron
        atendidos en las unidades del IGSS Escuintla. Esto permite analizar:

        - La **cobertura geográfica** de las unidades médicas
        - Los **flujos de pacientes** desde diferentes municipios
        - La **demanda de servicios** por área geográfica
        - Las **necesidades de atención** en zonas específicas

        ### Diferencia con datos de Atención

        | Aspecto | Datos de Atención | Datos de Procedencia |
        |---------|-------------------|---------------------|
        | **Pregunta** | ¿Dónde se atendieron? | ¿De dónde vienen? |
        | **Dimensión clave** | Unidad de atención | Municipio de origen |
        | **Uso principal** | Carga de trabajo por unidad | Cobertura geográfica |
        """)
