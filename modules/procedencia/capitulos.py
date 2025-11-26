"""
Módulo de Capítulos CIE-10 por Procedencia Geográfica
Distribución de casos según clasificación por capítulos de enfermedades
Segmentados por departamento y municipio de origen

IMPORTANTE: Solo usa "General Escuintla Procedencia" para evitar duplicación
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from config import COLORS
from utils.filters import UNIDAD_GENERAL_PROCEDENCIA
from utils.colors import (
    create_bar_chart, create_line_chart, create_pie_chart,
    create_metric_card_html, format_large_number
)


def get_capitulo(cie10, df_capitulos):
    """Obtiene el capítulo CIE-10 para un código"""
    if pd.isna(cie10):
        return 'Sin clasificar'
    codigo = str(cie10).upper().strip()
    for _, row in df_capitulos.iterrows():
        if row['rango_inicio'] <= codigo <= row['rango_fin']:
            return row['nombre']
    return 'Sin clasificar'


def render(df_procedencia, df_capitulos, filtro_departamento=None, filtro_municipio=None):
    """
    Renderiza análisis por capítulos CIE-10 con datos de procedencia
    """
    st.title("📚🌍 Capítulos CIE-10 por Procedencia")
    st.markdown("### Distribución de diagnósticos por capítulo y origen geográfico")

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
            key="depto_capitulos"
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
            key="muni_capitulos"
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

    if df_filtrado.empty:
        st.warning("No hay datos con los filtros seleccionados.")
        return

    # =========================================================================
    # CLASIFICAR POR CAPÍTULOS
    # =========================================================================
    df_analisis = df_filtrado.copy()
    df_analisis['Capitulo'] = df_analisis['CIE10'].apply(lambda x: get_capitulo(x, df_capitulos))

    # =========================================================================
    # MÉTRICAS
    # =========================================================================
    col1, col2, col3, col4 = st.columns(4)

    total_casos = int(df_analisis['Casos'].sum())
    total_capitulos = df_analisis['Capitulo'].nunique()
    años_cubiertos = len(df_analisis['Año'].unique())
    deptos_incluidos = df_analisis['Departamento'].nunique()

    with col1:
        st.markdown(create_metric_card_html("Total Casos", total_casos, color='primary'), unsafe_allow_html=True)
    with col2:
        st.markdown(create_metric_card_html("Capítulos", total_capitulos, color='success'), unsafe_allow_html=True)
    with col3:
        st.markdown(create_metric_card_html("Años", años_cubiertos, color='info'), unsafe_allow_html=True)
    with col4:
        st.markdown(create_metric_card_html("Departamentos", deptos_incluidos, color='warning'), unsafe_allow_html=True)

    st.markdown("---")

    # =========================================================================
    # DISTRIBUCIÓN POR CAPÍTULOS
    # =========================================================================
    st.subheader("📊 Distribución por Capítulos CIE-10")

    casos_capitulo = df_analisis.groupby('Capitulo')['Casos'].sum().reset_index()
    casos_capitulo = casos_capitulo.sort_values('Casos', ascending=False)
    casos_capitulo['Porcentaje'] = (casos_capitulo['Casos'] / total_casos * 100).round(2)
    casos_capitulo['Rank'] = range(1, len(casos_capitulo) + 1)

    col_tabla, col_grafico = st.columns([1, 1])

    with col_tabla:
        tabla_display = casos_capitulo.copy()
        tabla_display['Casos_fmt'] = tabla_display['Casos'].apply(format_large_number)
        st.dataframe(
            tabla_display[['Rank', 'Capitulo', 'Casos_fmt', 'Porcentaje']].rename(
                columns={'Rank': '#', 'Capitulo': 'Capítulo', 'Casos_fmt': 'Casos', 'Porcentaje': '%'}
            ),
            use_container_width=True, hide_index=True, height=500
        )

    with col_grafico:
        top_10_cap = casos_capitulo.head(10)
        fig_pie = create_pie_chart(top_10_cap, values='Casos', names='Capitulo',
                                   title='Top 10 Capítulos CIE-10')
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")

    # =========================================================================
    # TENDENCIA TEMPORAL
    # =========================================================================
    st.subheader("📅 Tendencia Temporal por Capítulo")

    num_cap = st.slider("Capítulos a analizar:", 1, min(10, len(casos_capitulo)), 5, key="slider_cap_proc")

    top_caps = casos_capitulo.head(num_cap)['Capitulo'].tolist()
    df_temporal = df_analisis[df_analisis['Capitulo'].isin(top_caps)]

    tendencia = df_temporal.groupby(['Año', 'Capitulo'])['Casos'].sum().reset_index()

    if not tendencia.empty:
        fig_lineas = create_line_chart(tendencia, x='Año', y='Casos',
                                       title=f'Evolución Temporal - Top {num_cap} Capítulos', color='Capitulo')
        st.plotly_chart(fig_lineas, use_container_width=True)

    st.markdown("---")

    # =========================================================================
    # DISTRIBUCIÓN GEOGRÁFICA
    # =========================================================================
    if not filtro_depto:
        st.subheader("🗺️ Distribución Geográfica por Capítulo")

        top_3_caps = casos_capitulo.head(3)['Capitulo'].tolist()
        df_geo = df_analisis[df_analisis['Capitulo'].isin(top_3_caps)]
        dist_geo = df_geo.groupby(['Departamento', 'Capitulo'])['Casos'].sum().reset_index()

        top_deptos = df_geo.groupby('Departamento')['Casos'].sum().nlargest(10).index.tolist()
        dist_geo_top = dist_geo[dist_geo['Departamento'].isin(top_deptos)]

        if not dist_geo_top.empty:
            fig_geo = create_bar_chart(
                dist_geo_top.sort_values('Casos', ascending=True),
                x='Casos', y='Departamento',
                title='Top 3 Capítulos por Departamento',
                orientation='h'
            )
            fig_geo.update_layout(height=500)
            st.plotly_chart(fig_geo, use_container_width=True)

    # Info
    with st.expander("ℹ️ Información sobre Capítulos CIE-10"):
        st.markdown("""
        **Los capítulos CIE-10** agrupan los diagnósticos por sistemas o categorías:
        - Capítulo I: Enfermedades infecciosas
        - Capítulo II: Neoplasias
        - Capítulo IX: Enfermedades del sistema circulatorio
        - Capítulo X: Enfermedades del sistema respiratorio
        - etc.

        **Este análisis muestra** la distribución de casos según el capítulo,
        segmentada por el origen geográfico de los pacientes.
        """)
