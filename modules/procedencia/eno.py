"""
Módulo de Enfermedades de Notificación Obligatoria (ENO) por Procedencia
Análisis de ENO segmentadas por departamento y municipio de origen

IMPORTANTE: Solo usa "General Escuintla Procedencia" para evitar duplicación
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from config import COLORS
from utils.filters import get_top_n, UNIDAD_GENERAL_PROCEDENCIA
from utils.colors import (
    create_bar_chart, create_line_chart, create_pie_chart,
    create_metric_card_html, format_large_number, create_stacked_bar
)


def render(df_procedencia, df_eno, filtro_departamento=None, filtro_municipio=None):
    """
    Renderiza análisis de ENO por procedencia geográfica
    """
    st.title("⚠️🌍 Enfermedades de Notificación Obligatoria por Procedencia")
    st.markdown("### Vigilancia epidemiológica de ENO por origen geográfico de pacientes")

    if df_procedencia is None or df_procedencia.empty:
        st.error("No hay datos de procedencia disponibles.")
        return

    # Solo General Escuintla Procedencia
    df_general = df_procedencia[df_procedencia['Unidad'] == UNIDAD_GENERAL_PROCEDENCIA].copy()

    if df_general.empty:
        st.error("No hay datos de 'General Escuintla Procedencia'.")
        return

    # =========================================================================
    # FILTROS GEOGRÁFICOS
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
            key="depto_eno"
        )

    with col_f2:
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
            key="muni_eno"
        )

    # Aplicar filtros
    df_filtrado = df_general.copy()
    if filtro_depto:
        df_filtrado = df_filtrado[df_filtrado['Departamento'].isin(filtro_depto)]
    if filtro_muni:
        df_filtrado = df_filtrado[df_filtrado['Municipio'].isin(filtro_muni)]

    if filtro_depto or filtro_muni:
        contexto = ', '.join(filtro_muni[:3] if filtro_muni else filtro_depto[:3])
        st.info(f"📍 **Analizando pacientes procedentes de:** {contexto}")

    st.markdown("---")

    # =========================================================================
    # FILTRAR SOLO ENO
    # =========================================================================
    codigos_eno = df_eno['cie10'].unique().tolist()
    df_eno_filtrado = df_filtrado[df_filtrado['CIE10'].isin(codigos_eno)]

    if df_eno_filtrado.empty:
        st.warning("No hay casos de ENO con los filtros seleccionados.")
        return

    # =========================================================================
    # MÉTRICAS
    # =========================================================================
    col1, col2, col3, col4 = st.columns(4)

    total_casos_eno = int(df_eno_filtrado['Casos'].sum())
    total_casos_general = int(df_filtrado['Casos'].sum())
    pct_eno = (total_casos_eno / total_casos_general * 100) if total_casos_general > 0 else 0
    eno_unicas = df_eno_filtrado['CIE10'].nunique()
    deptos_afectados = df_eno_filtrado['Departamento'].nunique()

    with col1:
        st.markdown(create_metric_card_html("Casos ENO", total_casos_eno, color='danger'), unsafe_allow_html=True)
    with col2:
        st.markdown(create_metric_card_html("% del Total", f"{pct_eno:.1f}%", color='warning'), unsafe_allow_html=True)
    with col3:
        st.markdown(create_metric_card_html("ENO Diferentes", eno_unicas, color='info'), unsafe_allow_html=True)
    with col4:
        st.markdown(create_metric_card_html("Deptos Afectados", deptos_afectados, color='success'), unsafe_allow_html=True)

    st.markdown("---")

    # =========================================================================
    # TOP ENO
    # =========================================================================
    st.subheader("📊 Enfermedades de Notificación Obligatoria Más Frecuentes")

    casos_por_eno = df_eno_filtrado.groupby('CIE10')['Casos'].sum().reset_index()
    casos_por_eno = casos_por_eno.sort_values('Casos', ascending=False)
    casos_por_eno['Rank'] = range(1, len(casos_por_eno) + 1)

    # Agregar nombres
    casos_por_eno = pd.merge(casos_por_eno, df_eno[['cie10', 'nombre']], left_on='CIE10', right_on='cie10', how='left')
    casos_por_eno['ENO'] = casos_por_eno['nombre'].fillna(casos_por_eno['CIE10'])
    casos_por_eno['Porcentaje'] = (casos_por_eno['Casos'] / total_casos_eno * 100).round(2)

    col_tabla, col_grafico = st.columns([1, 1])

    with col_tabla:
        tabla_display = casos_por_eno.copy()
        tabla_display['Casos_fmt'] = tabla_display['Casos'].apply(format_large_number)
        st.dataframe(
            tabla_display[['Rank', 'ENO', 'CIE10', 'Casos_fmt', 'Porcentaje']].rename(
                columns={'Rank': '#', 'Casos_fmt': 'Casos', 'Porcentaje': '%'}
            ),
            use_container_width=True, hide_index=True, height=400
        )

    with col_grafico:
        top_10 = casos_por_eno.head(10).sort_values('Casos', ascending=True)
        fig = create_bar_chart(top_10, x='Casos', y='ENO', title='Top 10 ENO', orientation='h')
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # =========================================================================
    # TENDENCIA TEMPORAL
    # =========================================================================
    st.subheader("📅 Tendencia Temporal de ENO")

    num_eno = st.slider("ENO a analizar:", 1, min(10, len(casos_por_eno)), 5, key="slider_eno_proc")

    top_eno_codes = casos_por_eno.head(num_eno)['CIE10'].tolist()
    df_temporal = df_eno_filtrado[df_eno_filtrado['CIE10'].isin(top_eno_codes)]
    df_temporal = pd.merge(df_temporal, casos_por_eno[['CIE10', 'ENO']], on='CIE10', how='left')

    tendencia = df_temporal.groupby(['Año', 'ENO'])['Casos'].sum().reset_index()

    if not tendencia.empty:
        fig_lineas = create_line_chart(tendencia, x='Año', y='Casos',
                                       title=f'Evolución Temporal - Top {num_eno} ENO', color='ENO')
        st.plotly_chart(fig_lineas, use_container_width=True)

    st.markdown("---")

    # =========================================================================
    # MAPA DE CALOR GEOGRÁFICO
    # =========================================================================
    if not filtro_depto:
        st.subheader("🗺️ Distribución Geográfica de ENO")

        dist_geo = df_eno_filtrado.groupby('Departamento')['Casos'].sum().reset_index()
        dist_geo = dist_geo.sort_values('Casos', ascending=False)
        dist_geo['Porcentaje'] = (dist_geo['Casos'] / total_casos_eno * 100).round(2)

        col_t, col_g = st.columns([1, 1])

        with col_t:
            dist_geo['Casos_fmt'] = dist_geo['Casos'].apply(format_large_number)
            st.dataframe(
                dist_geo[['Departamento', 'Casos_fmt', 'Porcentaje']].rename(
                    columns={'Casos_fmt': 'Casos ENO', 'Porcentaje': '%'}
                ),
                use_container_width=True, hide_index=True
            )

        with col_g:
            top_deptos = dist_geo.head(10).sort_values('Casos', ascending=True)
            fig_geo = create_bar_chart(top_deptos, x='Casos', y='Departamento',
                                       title='Top 10 Departamentos con ENO', orientation='h')
            st.plotly_chart(fig_geo, use_container_width=True)

    # Info
    with st.expander("ℹ️ Información sobre ENO"):
        st.markdown(f"""
        **Enfermedades de Notificación Obligatoria (ENO)** son aquellas que por su
        importancia epidemiológica deben reportarse al sistema de vigilancia.

        **En este análisis:**
        - Total casos ENO: {format_large_number(total_casos_eno)}
        - Representan el {pct_eno:.1f}% del total de morbilidad
        - {eno_unicas} tipos de ENO identificadas
        - Presentes en {deptos_afectados} departamentos

        **Importancia:** Permite identificar zonas geográficas con mayor
        incidencia de enfermedades bajo vigilancia epidemiológica.
        """)
