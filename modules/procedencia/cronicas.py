"""
Módulo de Enfermedades Crónicas No Transmisibles por Procedencia
Análisis de ECNT segmentadas por departamento y municipio de origen

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

# Helper para convertir DataFrame a CSV para descarga
@st.cache_data
def convert_df_to_csv(df):
    return df.to_csv(index=False, encoding='utf-8-sig')


def render(df_procedencia, df_cronicas, filtro_departamento=None, filtro_municipio=None):
    """
    Renderiza análisis de enfermedades crónicas por procedencia
    """
    st.title("💊🌍 Enfermedades Crónicas por Procedencia")
    st.markdown("### Análisis de ECNT por origen geográfico de pacientes")

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
            key="depto_cronicas"
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
            key="muni_cronicas"
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
    # FILTRAR SOLO CRÓNICAS
    # =========================================================================
    codigos_cronicas = df_cronicas['cie10'].unique().tolist()
    df_cronicas_filtrado = df_filtrado[df_filtrado['CIE10'].isin(codigos_cronicas)]

    if df_cronicas_filtrado.empty:
        st.warning("No hay casos de enfermedades crónicas con los filtros seleccionados.")
        return

    # =========================================================================
    # MÉTRICAS
    # =========================================================================
    col1, col2, col3, col4 = st.columns(4)

    total_casos_cronicas = int(df_cronicas_filtrado['Casos'].sum())
    total_casos_general = int(df_filtrado['Casos'].sum())
    pct_cronicas = (total_casos_cronicas / total_casos_general * 100) if total_casos_general > 0 else 0
    cronicas_unicas = df_cronicas_filtrado['CIE10'].nunique()
    deptos_afectados = df_cronicas_filtrado['Departamento'].nunique()

    with col1:
        st.markdown(create_metric_card_html("Casos Crónicos", total_casos_cronicas, color='primary'), unsafe_allow_html=True)
    with col2:
        st.markdown(create_metric_card_html("% del Total", f"{pct_cronicas:.1f}%", color='warning'), unsafe_allow_html=True)
    with col3:
        st.markdown(create_metric_card_html("ECNT Diferentes", cronicas_unicas, color='info'), unsafe_allow_html=True)
    with col4:
        st.markdown(create_metric_card_html("Departamentos", deptos_afectados, color='success'), unsafe_allow_html=True)

    st.markdown("---")

    # =========================================================================
    # TOP ENFERMEDADES CRÓNICAS
    # =========================================================================
    st.subheader("📊 Enfermedades Crónicas Más Frecuentes")

    casos_por_cronica = df_cronicas_filtrado.groupby('CIE10')['Casos'].sum().reset_index()
    casos_por_cronica = casos_por_cronica.sort_values('Casos', ascending=False)
    casos_por_cronica['Rank'] = range(1, len(casos_por_cronica) + 1)

    # Agregar nombres
    casos_por_cronica = pd.merge(casos_por_cronica, df_cronicas[['cie10', 'nombre']],
                                  left_on='CIE10', right_on='cie10', how='left')
    casos_por_cronica['Enfermedad'] = casos_por_cronica['nombre'].fillna(casos_por_cronica['CIE10'])
    casos_por_cronica['Porcentaje'] = (casos_por_cronica['Casos'] / total_casos_cronicas * 100).round(2)

    col_tabla, col_grafico = st.columns([1, 1])

    with col_tabla:
        tabla_display = casos_por_cronica.copy()
        tabla_display['Casos'] = tabla_display['Casos'].apply(format_large_number)
        st.dataframe(
            tabla_display[['Rank', 'Enfermedad', 'CIE10', 'Casos', 'Porcentaje']].rename(
                columns={'Rank': '#', 'Porcentaje': '%'}
            ),
            use_container_width=True, hide_index=True, height=400
        )
        
        csv_data = convert_df_to_csv(casos_por_cronica[['Rank', 'CIE10', 'Enfermedad', 'Casos', 'Porcentaje']])
        st.download_button(
           label="📥 Descargar datos de ECNT (CSV)",
           data=csv_data,
           file_name="distribucion_cronicas_procedencia.csv",
           mime="text/csv",
        )

    with col_grafico:
        top_10 = casos_por_cronica.head(10).sort_values('Casos', ascending=True)
        fig = create_bar_chart(top_10, x='Casos', y='Enfermedad',
                               title='Top 10 Enfermedades Crónicas', orientation='h')
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # =========================================================================
    # TENDENCIA TEMPORAL
    # =========================================================================
    st.subheader("📅 Tendencia Temporal de ECNT")

    num_ecnt = st.slider("ECNT a analizar:", 1, min(10, len(casos_por_cronica)), 5, key="slider_cronicas_proc")

    top_cronicas_codes = casos_por_cronica.head(num_ecnt)['CIE10'].tolist()
    df_temporal = df_cronicas_filtrado[df_cronicas_filtrado['CIE10'].isin(top_cronicas_codes)]
    df_temporal = pd.merge(df_temporal, casos_por_cronica[['CIE10', 'Enfermedad']], on='CIE10', how='left')

    tendencia = df_temporal.groupby(['Año', 'Enfermedad'])['Casos'].sum().reset_index()

    if not tendencia.empty:
        fig_lineas = create_line_chart(tendencia, x='Año', y='Casos',
                                       title=f'Evolución Temporal - Top {num_ecnt} ECNT', color='Enfermedad')
        st.plotly_chart(fig_lineas, use_container_width=True)

    st.markdown("---")

    # =========================================================================
    # DISTRIBUCIÓN POR SEXO
    # =========================================================================
    st.subheader("👥 Distribución por Sexo")

    dist_sexo = df_cronicas_filtrado.groupby('Sexo')['Casos'].sum().reset_index()
    dist_sexo['Porcentaje'] = (dist_sexo['Casos'] / total_casos_cronicas * 100).round(1)

    col_s1, col_s2 = st.columns(2)

    with col_s1:
        fig_pie = create_pie_chart(dist_sexo, values='Casos', names='Sexo',
                                   title='Distribución por Sexo')
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_s2:
        for _, row in dist_sexo.iterrows():
            st.metric(row['Sexo'], f"{format_large_number(int(row['Casos']))} ({row['Porcentaje']}%)")

    st.markdown("---")

    # =========================================================================
    # DISTRIBUCIÓN GEOGRÁFICA
    # =========================================================================
    if not filtro_depto:
        st.subheader("🗺️ Distribución Geográfica de ECNT")

        dist_geo = df_cronicas_filtrado.groupby('Departamento')['Casos'].sum().reset_index()
        dist_geo = dist_geo.sort_values('Casos', ascending=False)
        dist_geo['Porcentaje'] = (dist_geo['Casos'] / total_casos_cronicas * 100).round(2)

        col_t, col_g = st.columns([1, 1])

        with col_t:
            dist_geo['Casos_fmt'] = dist_geo['Casos'].apply(format_large_number)
            st.dataframe(
                dist_geo[['Departamento', 'Casos_fmt', 'Porcentaje']].rename(
                    columns={'Casos_fmt': 'Casos ECNT', 'Porcentaje': '%'}
                ),
                use_container_width=True, hide_index=True
            )

        with col_g:
            top_deptos = dist_geo.head(10).sort_values('Casos', ascending=True)
            fig_geo = create_bar_chart(top_deptos, x='Casos', y='Departamento',
                                       title='Top 10 Departamentos con ECNT', orientation='h')
            st.plotly_chart(fig_geo, use_container_width=True)

    # Info
    with st.expander("ℹ️ Información sobre ECNT"):
        st.markdown(f"""
        **Enfermedades Crónicas No Transmisibles (ECNT)** incluyen:
        - Diabetes mellitus (E10-E14)
        - Hipertensión arterial (I10-I15)
        - Enfermedades cardiovasculares
        - Enfermedades respiratorias crónicas
        - Enfermedades renales crónicas

        **En este análisis:**
        - Total casos ECNT: {format_large_number(total_casos_cronicas)}
        - Representan el {pct_cronicas:.1f}% del total de morbilidad
        - {cronicas_unicas} tipos de ECNT identificadas
        - Presentes en {deptos_afectados} departamentos

        **Importancia:** Las ECNT representan la principal carga de enfermedad
        y permiten identificar zonas con mayor prevalencia para intervenciones.
        """)
