"""
Módulo de Morbilidad Pediátrica por Procedencia Geográfica
Análisis de diagnósticos más frecuentes en población pediátrica (0-15 años)
Segmentados por departamento y municipio de origen

IMPORTANTE: Solo usa "General Escuintla Procedencia" para evitar duplicación
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from config import COLORS
from utils.filters import filter_by_age_group, get_top_n, get_context_df_procedencia
from utils.colors import (
    create_bar_chart, create_line_chart, create_metric_card_html,
    format_large_number, create_stacked_bar
)

# Helper para convertir DataFrame a CSV para descarga
@st.cache_data
def convert_df_to_csv(df):
    return df.to_csv(index=False, encoding='utf-8-sig')


def render(df_procedencia, df_eno, df_cronicas, df_diagnosticos,
           filtro_departamento=None, filtro_municipio=None):
    """
    Renderiza el módulo de morbilidad pediátrica por procedencia
    """
    st.title("👶🌍 Morbilidad Pediátrica por Procedencia")
    st.markdown("### Análisis de diagnósticos en población pediátrica (0-15 años) por origen geográfico")

    if df_procedencia is None or df_procedencia.empty:
        st.error("No hay datos de procedencia disponibles.")
        return

    # Base de análisis (evita duplicación si vienen todas las unidades)
    df_base = get_context_df_procedencia(df_procedencia)

    # =========================================================================
    # FILTROS GEOGRÁFICOS
    # =========================================================================
    st.markdown("---")
    st.subheader("🗺️ Filtros de Procedencia Geográfica")

    col_f1, col_f2 = st.columns(2)

    with col_f1:
        departamentos_disponibles = sorted(df_base['Departamento'].unique().tolist())
        filtro_depto = st.multiselect(
            "Departamento de procedencia:",
            options=departamentos_disponibles,
            default=filtro_departamento or [],
            key="depto_pediatrica"
        )

    with col_f2:
        if filtro_depto:
            municipios_disponibles = sorted(
                df_base[df_base['Departamento'].isin(filtro_depto)]['Municipio'].unique().tolist()
            )
        else:
            municipios_disponibles = sorted(df_base['Municipio'].unique().tolist())

        filtro_muni = st.multiselect(
            "Municipio de procedencia:",
            options=municipios_disponibles,
            default=filtro_municipio or [],
            key="muni_pediatrica"
        )

    # Aplicar filtros
    df_filtrado_geo = df_base.copy()
    if filtro_depto:
        df_filtrado_geo = df_filtrado_geo[df_filtrado_geo['Departamento'].isin(filtro_depto)]
    if filtro_muni:
        df_filtrado_geo = df_filtrado_geo[df_filtrado_geo['Municipio'].isin(filtro_muni)]

    if filtro_depto or filtro_muni:
        contexto = ', '.join(filtro_muni[:3] if filtro_muni else filtro_depto[:3])
        st.info(f"📍 **Analizando pacientes procedentes de:** {contexto}")

    st.markdown("---")

    # Filtrar pediátricos
    df_pediatricos = filter_by_age_group(df_filtrado_geo, pediatrico=True)

    if df_pediatricos.empty:
        st.warning("No hay datos para población pediátrica con los filtros seleccionados.")
        return

    # =========================================================================
    # MÉTRICAS
    # =========================================================================
    col1, col2, col3, col4 = st.columns(4)

    total_casos = int(df_pediatricos['Casos'].sum())
    total_diagnosticos = df_pediatricos['CIE10'].nunique()
    años_cubiertos = len(df_pediatricos['Año'].unique())
    deptos_incluidos = df_pediatricos['Departamento'].nunique()

    with col1:
        st.markdown(create_metric_card_html("Total Casos Pediátricos", total_casos, color='primary'), unsafe_allow_html=True)
    with col2:
        st.markdown(create_metric_card_html("Diagnósticos Únicos", total_diagnosticos, color='success'), unsafe_allow_html=True)
    with col3:
        st.markdown(create_metric_card_html("Años Analizados", años_cubiertos, color='info'), unsafe_allow_html=True)
    with col4:
        st.markdown(create_metric_card_html("Departamentos", deptos_incluidos, color='warning'), unsafe_allow_html=True)

    st.markdown("---")

    # =========================================================================
    # TOP DIAGNÓSTICOS
    # =========================================================================
    show_all_dx = st.checkbox("Mostrar todos los diagnósticos (puede ser lento)", key="show_all_pediatrica_proc")
    
    subheader_dx = "📊 Diagnósticos Más Frecuentes" if show_all_dx else "📊 Top N Diagnósticos Más Frecuentes"
    st.subheader(subheader_dx)

    top_n_value = 25
    if not show_all_dx:
        with st.expander("⚙️ Opciones de Visualización"):
            top_n_value = st.number_input(
                "Número de diagnósticos:", min_value=5, max_value=100, value=25, step=5,
                key="top_n_pediatrica_proc",
                disabled=show_all_dx
            )

    n_param = None if show_all_dx else top_n_value
    top_n = get_top_n(df_pediatricos, n=n_param, group_by='CIE10')

    if not top_n.empty:
        top_n = pd.merge(top_n, df_diagnosticos, left_on='CIE10', right_on='cie10', how='left')
        top_n['Diagnóstico'] = top_n['nombre'].fillna('Nombre no disponible')
        top_n.drop(columns=['cie10', 'nombre'], inplace=True, errors='ignore')
        top_n['Porcentaje'] = (top_n['Casos'] / total_casos * 100).round(2)
        top_n['Es_ENO'] = top_n['CIE10'].apply(lambda x: '⚠️' if x in df_eno['cie10'].values else '')
        top_n['Es_Cronica'] = top_n['CIE10'].apply(lambda x: '💊' if x in df_cronicas['cie10'].values else '')

        top_display = top_n.copy()
        top_display['Casos'] = top_display['Casos'].apply(format_large_number)

        st.dataframe(
            top_display[['Rank', 'Diagnóstico', 'CIE10', 'Casos', 'Porcentaje', 'Es_ENO', 'Es_Cronica']].rename(
                columns={'Rank': '#', 'CIE10': 'Código', 'Porcentaje': '%', 'Es_ENO': 'ENO', 'Es_Cronica': 'Crónica'}
            ),
            use_container_width=True, hide_index=True
        )

        st.info("💡 **Leyenda:** ⚠️ = ENO | 💊 = Enfermedad Crónica")

        # Botón de descarga
        df_download = get_top_n(df_pediatricos, n=None, group_by='CIE10')
        df_download = pd.merge(df_download, df_diagnosticos, left_on='CIE10', right_on='cie10', how='left')
        df_download['Diagnóstico'] = df_download['nombre'].fillna('Nombre no disponible')
        csv_data = convert_df_to_csv(df_download[['Rank', 'CIE10', 'Diagnóstico', 'Casos']])
        
        st.download_button(
           label="📥 Descargar todos los diagnósticos (CSV)",
           data=csv_data,
           file_name="diagnosticos_pediatricos_procedencia.csv",
           mime="text/csv",
        )

        # Gráfico
        st.subheader(f"📈 Visualización Top {top_n_value if not show_all_dx else 15}")
        top_grafico = top_n.head(15).sort_values('Casos', ascending=True)
        fig = create_bar_chart(top_grafico, x='Casos', y='Diagnóstico',
                               title=f'Top {len(top_grafico)} Diagnósticos Pediátricos - Por Procedencia', orientation='h')
        fig.update_layout(height=max(400, len(top_grafico) * 35))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # =========================================================================
    # TENDENCIA TEMPORAL
    # =========================================================================
    st.subheader("📅 Tendencia Temporal")

    if not top_n.empty:
        num_top = st.slider("Diagnósticos para análisis temporal:", 1, min(10, len(top_n)), min(5, len(top_n)),
                            key="slider_pediatrica_proc")
        top_codes = top_n.head(num_top)['CIE10'].tolist()
        df_temporal = df_pediatricos[df_pediatricos['CIE10'].isin(top_codes)]
        df_temporal = pd.merge(df_temporal, top_n[['CIE10', 'Diagnóstico']], on='CIE10', how='left')

        tendencia = df_temporal.groupby(['Año', 'Diagnóstico'])['Casos'].sum().reset_index()
        if not tendencia.empty:
            fig_lineas = create_line_chart(tendencia, x='Año', y='Casos',
                                           title=f'Evolución Temporal - Top {num_top}', color='Diagnóstico')
            st.plotly_chart(fig_lineas, use_container_width=True)

        # Sexo
        st.subheader(f"👥 Distribución por Sexo - Top {num_top}")
        dist_sexo = df_temporal.groupby(['Diagnóstico', 'Sexo'])['Casos'].sum().reset_index()
        if not dist_sexo.empty:
            fig_sexo = create_stacked_bar(dist_sexo, x='Diagnóstico', y='Casos', title='Por Sexo', color='Sexo')
            st.plotly_chart(fig_sexo, use_container_width=True)

    # Info
    with st.expander("ℹ️ Información"):
        st.markdown(f"""
        **Población pediátrica:** 0-15 años
        **Total casos:** {format_large_number(total_casos)}
        **Fuente:** Base de Procedencia Geográfica IGSS Escuintla
        """)
