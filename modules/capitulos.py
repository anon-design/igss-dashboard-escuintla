"""
Módulo de Análisis por Capítulos CIE-10
Distribución de casos por capítulo de la Clasificación Internacional de Enfermedades
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from config import COLORS
from utils.data_loader import get_cie10_chapter
from utils.filters import get_top_n
from utils.colors import (
    create_bar_chart,
    create_line_chart,
    create_pie_chart,
    create_metric_card_html,
    format_large_number
)


def render(df, df_capitulos):
    """
    Renderiza el módulo de análisis por capítulos CIE-10

    Args:
        df: DataFrame filtrado con datos
        df_capitulos: DataFrame con catálogo de capítulos CIE-10
    """
    st.title("📚 Análisis por Capítulos CIE-10")
    st.markdown("### Distribución de casos según la Clasificación Internacional de Enfermedades")

    st.markdown("---")

    if df.empty:
        st.warning("No hay datos disponibles con los filtros seleccionados.")
        return

    # Agregar columna de capítulo a cada registro
    df_capitulos_analisis = df.copy()
    df_capitulos_analisis['Capitulo'] = df_capitulos_analisis['CIE10'].apply(
        lambda x: get_cie10_chapter(x, df_capitulos)
    )

    # Agrupar por capítulo
    casos_por_capitulo = df_capitulos_analisis.groupby('Capitulo')['Casos'].sum().reset_index()
    casos_por_capitulo = casos_por_capitulo.sort_values('Casos', ascending=False)

    # Métricas principales
    col1, col2, col3 = st.columns(3)

    total_casos = int(df['Casos'].sum())
    total_capitulos = len(casos_por_capitulo)
    capitulo_principal = casos_por_capitulo.iloc[0]['Capitulo'] if not casos_por_capitulo.empty else 'N/A'

    with col1:
        st.markdown(
            create_metric_card_html(
                "Total de Casos",
                total_casos,
                color='primary'
            ),
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            create_metric_card_html(
                "Capítulos Representados",
                total_capitulos,
                color='success'
            ),
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            create_metric_card_html(
                "Capítulo Principal",
                f"{capitulo_principal[:20]}...",
                color='info'
            ),
            unsafe_allow_html=True
        )

    st.markdown("---")

    # Tabla de todos los capítulos
    st.subheader("📊 Distribución por Capítulo CIE-10")

    if not casos_por_capitulo.empty:
        # Calcular porcentajes
        casos_por_capitulo['Porcentaje'] = (casos_por_capitulo['Casos'] / total_casos * 100).round(2)
        casos_por_capitulo['Rank'] = range(1, len(casos_por_capitulo) + 1)

        # Crear tabla formateada
        tabla_display = casos_por_capitulo.copy()
        tabla_display['Casos'] = tabla_display['Casos'].apply(format_large_number)
        tabla_display = tabla_display[['Rank', 'Capitulo', 'Casos', 'Porcentaje']]
        tabla_display.columns = ['#', 'Capítulo CIE-10', 'Casos', '%']

        st.dataframe(tabla_display, use_container_width=True, hide_index=True)

        # Gráfico de barras horizontales
        st.subheader("📈 Visualización por Capítulo")

        fig_barras = create_bar_chart(
            casos_por_capitulo,
            x='Casos',
            y='Capitulo',
            title='Distribución de Casos por Capítulo CIE-10',
            orientation='h'
        )

        fig_barras.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            height=600
        )

        st.plotly_chart(fig_barras, use_container_width=True)

    st.markdown("---")

    # Gráfico circular - Top 10 capítulos
    st.subheader("🥧 Top 10 Capítulos - Distribución Porcentual")

    col1, col2 = st.columns(2)

    with col1:
        if not casos_por_capitulo.empty:
            top_10_capitulos = casos_por_capitulo.head(10).copy()

            # Agregar categoría "Otros" si hay más de 10 capítulos
            if len(casos_por_capitulo) > 10:
                otros_casos = casos_por_capitulo.iloc[10:]['Casos'].sum()
                otros_row = pd.DataFrame({
                    'Capitulo': ['Otros'],
                    'Casos': [otros_casos],
                    'Porcentaje': [(otros_casos / total_casos * 100)]
                })
                top_10_capitulos = pd.concat([top_10_capitulos, otros_row], ignore_index=True)

            # Simplificar nombres para el gráfico
            top_10_capitulos['Capitulo_Corto'] = top_10_capitulos['Capitulo'].apply(
                lambda x: x[:40] + '...' if len(x) > 40 else x
            )

            fig_pie = create_pie_chart(
                top_10_capitulos,
                values='Casos',
                names='Capitulo_Corto',
                title='Top 10 Capítulos'
            )

            fig_pie.update_layout(height=500)
            st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        if not casos_por_capitulo.empty:
            st.markdown("**Top 10 Capítulos:**")
            top_10_display = casos_por_capitulo.head(10).copy()
            top_10_display['Casos'] = top_10_display['Casos'].apply(format_large_number)
            top_10_display = top_10_display[['Rank', 'Capitulo', 'Casos', 'Porcentaje']]
            top_10_display.columns = ['#', 'Capítulo', 'Casos', '%']
            st.dataframe(top_10_display, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Análisis temporal - Top 5 capítulos
    st.subheader("📅 Tendencia Temporal - Top 5 Capítulos")

    top_5_capitulos = casos_por_capitulo.head(5)['Capitulo'].tolist()

    # Filtrar datos para top 5
    df_top5 = df_capitulos_analisis[df_capitulos_analisis['Capitulo'].isin(top_5_capitulos)]

    if not df_top5.empty:
        # Agrupar por año y capítulo
        tendencia = df_top5.groupby(['Año', 'Capitulo'])['Casos'].sum().reset_index()

        fig_lineas = create_line_chart(
            tendencia,
            x='Año',
            y='Casos',
            title='Evolución Temporal de los 5 Capítulos Más Frecuentes',
            color='Capitulo'
        )

        fig_lineas.update_layout(height=500)

        st.plotly_chart(fig_lineas, use_container_width=True)

    st.markdown("---")

    # Distribución por sexo - Top 5 capítulos
    st.subheader("👥 Distribución por Sexo - Top 5 Capítulos")

    if not df_top5.empty:
        dist_sexo = df_top5.groupby(['Capitulo', 'Sexo'])['Casos'].sum().reset_index()

        if not dist_sexo.empty:
            from utils.colors import create_stacked_bar

            # Simplificar nombres de capítulos
            dist_sexo['Capitulo_Corto'] = dist_sexo['Capitulo'].apply(
                lambda x: x[:30] + '...' if len(x) > 30 else x
            )

            fig_sexo = create_stacked_bar(
                dist_sexo,
                x='Capitulo_Corto',
                y='Casos',
                title='Distribución por Sexo - Top 5 Capítulos',
                color='Sexo'
            )

            fig_sexo.update_layout(height=500)
            st.plotly_chart(fig_sexo, use_container_width=True)

    st.markdown("---")

    # Información adicional
    with st.expander("ℹ️ Información sobre los Capítulos CIE-10"):
        st.markdown("""
        **¿Qué es la Clasificación Internacional de Enfermedades (CIE-10)?**

        La CIE-10 es un sistema de clasificación de enfermedades y problemas relacionados con la salud
        desarrollado por la Organización Mundial de la Salud (OMS). Organiza las enfermedades en 21 capítulos
        principales según su naturaleza y sistema corporal afectado.

        **Capítulos principales:**
        - **I:** Enfermedades infecciosas y parasitarias (A00-B99)
        - **II:** Neoplasias (C00-D48)
        - **III:** Enfermedades de la sangre (D50-D89)
        - **IV:** Enfermedades endocrinas, nutricionales y metabólicas (E00-E90)
        - **V:** Trastornos mentales (F00-F99)
        - **VI-VIII:** Enfermedades del sistema nervioso, ojo y oído (G00-H95)
        - **IX:** Enfermedades del sistema circulatorio (I00-I99)
        - **X:** Enfermedades del sistema respiratorio (J00-J99)
        - **XI:** Enfermedades del sistema digestivo (K00-K93)
        - **XII:** Enfermedades de la piel (L00-L99)
        - **XIII:** Enfermedades del sistema musculoesquelético (M00-M99)
        - **XIV:** Enfermedades del sistema genitourinario (N00-N99)
        - **XV:** Embarazo, parto y puerperio (O00-O99)
        - **XVI:** Condiciones originadas en el período perinatal (P00-P96)
        - **XVII:** Malformaciones congénitas (Q00-Q99)
        - **XVIII:** Síntomas y hallazgos anormales (R00-R99)
        - **XIX:** Traumatismos y envenenamientos (S00-T98)
        - **XX:** Causas externas de morbilidad (V01-Y98)
        - **XXI:** Factores que influyen en el estado de salud (Z00-Z99)

        **Uso de filtros:**
        - Utiliza los filtros de la barra lateral para segmentar por unidad, año o sexo
        - Los gráficos se actualizan automáticamente según los filtros aplicados
        """)
