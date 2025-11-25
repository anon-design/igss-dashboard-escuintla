"""
Módulo de Morbilidad en Adultos por Procedencia Geográfica
Análisis de los diagnósticos más frecuentes en población adulta (>15 años)
Segmentados por departamento y municipio de origen de los pacientes

IMPORTANTE: Solo usa "General Escuintla Procedencia" para evitar duplicación
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from config import COLORS
from utils.filters import (
    filter_by_age_group,
    get_top_n,
    get_total_general_procedencia,
    UNIDAD_GENERAL_PROCEDENCIA
)
from utils.colors import (
    create_bar_chart,
    create_line_chart,
    create_metric_card_html,
    format_large_number,
    create_stacked_bar
)


def render(df_procedencia, df_eno, df_cronicas, df_diagnosticos,
           filtro_departamento=None, filtro_municipio=None):
    """
    Renderiza el módulo de morbilidad en adultos por procedencia geográfica

    Args:
        df_procedencia: DataFrame con datos de procedencia
        df_eno: DataFrame con catálogo ENO
        df_cronicas: DataFrame con catálogo de crónicas
        df_diagnosticos: DataFrame con catálogo de nombres CIE-10
        filtro_departamento: Lista de departamentos seleccionados
        filtro_municipio: Lista de municipios seleccionados
    """
    st.title("👨🌍 Morbilidad Adultos por Procedencia")
    st.markdown("### Análisis de diagnósticos más frecuentes en adultos (>15 años) por origen geográfico")

    if df_procedencia is None or df_procedencia.empty:
        st.error("No hay datos de procedencia disponibles.")
        return

    # =========================================================================
    # FILTRAR SOLO GENERAL ESCUINTLA PROCEDENCIA (evitar duplicación)
    # =========================================================================
    df_general = df_procedencia[df_procedencia['Unidad'] == UNIDAD_GENERAL_PROCEDENCIA].copy()

    if df_general.empty:
        st.error("No hay datos de 'General Escuintla Procedencia'.")
        return

    # =========================================================================
    # FILTROS GEOGRÁFICOS EN LA PÁGINA
    # =========================================================================
    st.markdown("---")
    st.subheader("🗺️ Filtros de Procedencia Geográfica")

    col_f1, col_f2 = st.columns(2)

    with col_f1:
        departamentos_disponibles = sorted(df_general['Departamento'].unique().tolist())
        filtro_depto = st.multiselect(
            "Departamento de procedencia:",
            options=departamentos_disponibles,
            default=filtro_departamento or [],
            help="Filtrar pacientes por departamento de origen"
        )

    with col_f2:
        # Municipios filtrados por departamento si hay selección
        if filtro_depto:
            municipios_disponibles = sorted(
                df_general[df_general['Departamento'].isin(filtro_depto)]['Municipio'].unique().tolist()
            )
        else:
            municipios_disponibles = sorted(df_general['Municipio'].unique().tolist())

        filtro_muni = st.multiselect(
            "Municipio de procedencia:",
            options=municipios_disponibles,
            default=filtro_municipio or [],
            help="Filtrar pacientes por municipio de origen"
        )

    # Aplicar filtros geográficos
    df_filtrado_geo = df_general.copy()
    contexto_geo = "Todos los departamentos"

    if filtro_depto:
        df_filtrado_geo = df_filtrado_geo[df_filtrado_geo['Departamento'].isin(filtro_depto)]
        contexto_geo = f"Departamento(s): {', '.join(filtro_depto)}"

    if filtro_muni:
        df_filtrado_geo = df_filtrado_geo[df_filtrado_geo['Municipio'].isin(filtro_muni)]
        contexto_geo = f"Municipio(s): {', '.join(filtro_muni[:3])}{'...' if len(filtro_muni) > 3 else ''}"

    # Mostrar contexto
    if filtro_depto or filtro_muni:
        st.info(f"📍 **Analizando pacientes procedentes de:** {contexto_geo}")

    st.markdown("---")

    # =========================================================================
    # FILTRAR SOLO ADULTOS
    # =========================================================================
    df_adultos = filter_by_age_group(df_filtrado_geo, pediatrico=False)

    if df_adultos.empty:
        st.warning("No hay datos para población adulta con los filtros seleccionados.")
        return

    # =========================================================================
    # MÉTRICAS PRINCIPALES
    # =========================================================================
    col1, col2, col3, col4 = st.columns(4)

    total_casos = int(df_adultos['Casos'].sum())
    total_diagnosticos = df_adultos['CIE10'].nunique()
    años_cubiertos = len(df_adultos['Año'].unique())
    deptos_incluidos = df_adultos['Departamento'].nunique()

    with col1:
        st.markdown(
            create_metric_card_html("Total Casos Adultos", total_casos, color='primary'),
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            create_metric_card_html("Diagnósticos Únicos", total_diagnosticos, color='success'),
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            create_metric_card_html("Años Analizados", años_cubiertos, color='info'),
            unsafe_allow_html=True
        )

    with col4:
        st.markdown(
            create_metric_card_html("Departamentos", deptos_incluidos, color='warning'),
            unsafe_allow_html=True
        )

    st.markdown("---")

    # =========================================================================
    # TOP N DIAGNÓSTICOS
    # =========================================================================
    st.subheader("📊 Top N Diagnósticos Más Frecuentes")

    top_n_value = 25
    with st.expander("⚙️ Opciones de Visualización"):
        top_n_value = st.number_input(
            "Número de diagnósticos a mostrar:",
            min_value=5, max_value=100, value=25, step=5,
            key="top_n_adultos_proc"
        )

    top_n = get_top_n(df_adultos, n=top_n_value, group_by='CIE10')

    if not top_n.empty:
        # Unir con catálogo de nombres
        top_n = pd.merge(top_n, df_diagnosticos, left_on='CIE10', right_on='cie10', how='left')
        top_n['Diagnóstico'] = top_n['nombre'].fillna('Nombre no disponible')
        top_n.drop(columns=['cie10', 'nombre'], inplace=True, errors='ignore')

        # Calcular porcentajes
        top_n['Porcentaje'] = (top_n['Casos'] / total_casos * 100).round(2)

        # Agregar indicadores ENO y Crónica
        top_n['Es_ENO'] = top_n['CIE10'].apply(
            lambda x: '⚠️' if x in df_eno['cie10'].values else ''
        )
        top_n['Es_Cronica'] = top_n['CIE10'].apply(
            lambda x: '💊' if x in df_cronicas['cie10'].values else ''
        )

        # Tabla formateada
        top_display = top_n.copy()
        top_display['Casos_fmt'] = top_display['Casos'].apply(format_large_number)

        st.dataframe(
            top_display[['Rank', 'Diagnóstico', 'CIE10', 'Casos_fmt', 'Porcentaje', 'Es_ENO', 'Es_Cronica']].rename(
                columns={
                    'Rank': '#',
                    'CIE10': 'Código',
                    'Casos_fmt': 'Casos',
                    'Porcentaje': '%',
                    'Es_ENO': 'ENO',
                    'Es_Cronica': 'Crónica'
                }
            ),
            use_container_width=True,
            hide_index=True
        )

        st.info("💡 **Leyenda:** ⚠️ = ENO (Notificación Obligatoria) | 💊 = Enfermedad Crónica")

        # Gráfico de barras
        st.subheader(f"📈 Visualización Top {len(top_n)}")

        top_grafico = top_n.head(15).sort_values('Casos', ascending=True)
        fig = create_bar_chart(
            top_grafico,
            x='Casos',
            y='Diagnóstico',
            title=f'Top {len(top_grafico)} Diagnósticos en Adultos - Por Procedencia',
            orientation='h'
        )
        fig.update_layout(height=max(400, len(top_grafico) * 35))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # =========================================================================
    # TENDENCIA TEMPORAL
    # =========================================================================
    st.subheader("📅 Tendencia Temporal de Diagnósticos Principales")

    if not top_n.empty:
        num_top_temporal = st.slider(
            "Diagnósticos para análisis temporal:",
            min_value=1, max_value=min(10, len(top_n)), value=min(5, len(top_n)),
            key="slider_temporal_adultos_proc"
        )

        top_codes = top_n.head(num_top_temporal)['CIE10'].tolist()
        df_temporal = df_adultos[df_adultos['CIE10'].isin(top_codes)]
        df_temporal = pd.merge(df_temporal, top_n[['CIE10', 'Diagnóstico']], on='CIE10', how='left')

        tendencia = df_temporal.groupby(['Año', 'Diagnóstico'])['Casos'].sum().reset_index()

        if not tendencia.empty:
            fig_lineas = create_line_chart(
                tendencia,
                x='Año',
                y='Casos',
                title=f'Evolución Temporal - Top {num_top_temporal} Diagnósticos',
                color='Diagnóstico'
            )
            st.plotly_chart(fig_lineas, use_container_width=True)

        # Distribución por sexo
        st.subheader(f"👥 Distribución por Sexo - Top {num_top_temporal}")

        dist_sexo = df_temporal.groupby(['Diagnóstico', 'Sexo'])['Casos'].sum().reset_index()

        if not dist_sexo.empty:
            fig_sexo = create_stacked_bar(
                dist_sexo,
                x='Diagnóstico',
                y='Casos',
                title='Distribución por Sexo',
                color='Sexo'
            )
            st.plotly_chart(fig_sexo, use_container_width=True)

    st.markdown("---")

    # =========================================================================
    # DISTRIBUCIÓN GEOGRÁFICA DE TOP DIAGNÓSTICOS
    # =========================================================================
    st.subheader("🗺️ Distribución Geográfica de Diagnósticos Principales")

    if not top_n.empty and not filtro_depto:  # Solo si no hay filtro de depto
        top_5_codes = top_n.head(5)['CIE10'].tolist()
        df_geo = df_adultos[df_adultos['CIE10'].isin(top_5_codes)]
        df_geo = pd.merge(df_geo, top_n[['CIE10', 'Diagnóstico']], on='CIE10', how='left')

        dist_geo = df_geo.groupby(['Departamento', 'Diagnóstico'])['Casos'].sum().reset_index()

        if not dist_geo.empty:
            # Top 10 departamentos
            top_deptos = df_geo.groupby('Departamento')['Casos'].sum().nlargest(10).index.tolist()
            dist_geo_top = dist_geo[dist_geo['Departamento'].isin(top_deptos)]

            fig_geo = create_stacked_bar(
                dist_geo_top,
                x='Departamento',
                y='Casos',
                title='Top 5 Diagnósticos por Departamento de Procedencia',
                color='Diagnóstico'
            )
            fig_geo.update_layout(xaxis_tickangle=-45, height=500)
            st.plotly_chart(fig_geo, use_container_width=True)

    # =========================================================================
    # INFORMACIÓN
    # =========================================================================
    with st.expander("ℹ️ Información sobre este análisis"):
        st.markdown(f"""
        **Datos analizados:**
        - Fuente: Base de Procedencia Geográfica
        - Total de casos (adultos): {format_large_number(total_casos)}
        - Departamentos incluidos: {deptos_incluidos}
        - Período: {min(df_adultos['Año'])} - {max(df_adultos['Año'])}

        **Criterios:**
        - Población adulta: Rangos de edad > 15 años
        - Se excluyen los rangos pediátricos (0-15)

        **Interpretación:**
        - Los datos muestran de **dónde vienen** los pacientes (procedencia)
        - No confundir con **dónde se atendieron** (análisis por unidad)
        - ⚠️ = Enfermedad de Notificación Obligatoria (ENO)
        - 💊 = Enfermedad Crónica No Transmisible
        """)
