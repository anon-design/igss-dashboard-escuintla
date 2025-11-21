"""
Módulo de Enfermedades Crónicas
Análisis de enfermedades crónicas no transmisibles
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from config import COLORS
from utils.data_loader import is_cronica
from utils.filters import get_top_n
from utils.colors import (
    create_bar_chart,
    create_line_chart,
    create_pie_chart,
    create_metric_card_html,
    format_large_number
)


def render(df, df_cronicas):
    """
    Renderiza el módulo de enfermedades crónicas

    Args:
        df: DataFrame filtrado con datos
        df_cronicas: DataFrame con catálogo de crónicas
    """
    st.title("💊 Enfermedades Crónicas")
    st.markdown("### Análisis de enfermedades crónicas no transmisibles")

    st.markdown("---")

    if df.empty:
        st.warning("No hay datos disponibles con los filtros seleccionados.")
        return

    # Filtrar solo crónicas
    df_cronicas_data = df[df['CIE10'].apply(lambda x: is_cronica(x, df_cronicas))].copy()

    if df_cronicas_data.empty:
        st.warning("No se encontraron casos de enfermedades crónicas con los filtros seleccionados.")
        return

    # Agregar información de categoría
    df_cronicas_data = df_cronicas_data.merge(
        df_cronicas[['cie10', 'nombre', 'categoria', 'subcategoria']],
        left_on='CIE10',
        right_on='cie10',
        how='left'
    )

    # Métricas principales
    col1, col2, col3 = st.columns(3)

    total_casos = int(df_cronicas_data['Casos'].sum())
    total_cronicas = df_cronicas_data['CIE10'].nunique()
    años_cubiertos = len(df_cronicas_data['Año'].unique())

    with col1:
        st.markdown(
            create_metric_card_html(
                "Total Casos Crónicas",
                total_casos,
                color='primary'
            ),
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            create_metric_card_html(
                "Enfermedades Detectadas",
                total_cronicas,
                color='warning'
            ),
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            create_metric_card_html(
                "Años Analizados",
                años_cubiertos,
                color='info'
            ),
            unsafe_allow_html=True
        )

    st.markdown("---")

    # Top N crónicas
    st.subheader("📊 Top N Enfermedades Crónicas")

    # --- Filtros Dinámicos ---
    with st.expander("⚙️ Opciones de Visualización"):
        top_n_value = st.number_input(
            "Selecciona el número de enfermedades a mostrar (N):",
            min_value=5,
            max_value=50,
            value=20,
            step=5,
            key="top_n_cronicas"
        )

    # Calcular todas las crónicas y luego filtrar
    all_cronicas = df_cronicas_data.groupby(['CIE10', 'nombre', 'categoria'])['Casos'].sum().reset_index()
    all_cronicas = all_cronicas.sort_values('Casos', ascending=False)
    
    with st.expander("Filtro de Exclusión de Enfermedades", expanded=False):
        diagnosticos_disponibles = all_cronicas['nombre'].tolist()
        diagnosticos_seleccionados = st.multiselect(
            "Selecciona las enfermedades a incluir:",
            options=diagnosticos_disponibles,
            default=diagnosticos_disponibles,
            key="exclude_filter_cronicas"
        )
    
    # Aplicar filtros
    top_cronicas_filtrado = all_cronicas[all_cronicas['nombre'].isin(diagnosticos_seleccionados)].head(top_n_value)

    if not top_cronicas_filtrado.empty:
        top_cronicas_filtrado['Rank'] = range(1, len(top_cronicas_filtrado) + 1)
        top_cronicas_filtrado['Porcentaje'] = (top_cronicas_filtrado['Casos'] / total_casos * 100).round(2)

        # Tabla formateada
        tabla_display = top_cronicas_filtrado.copy()
        tabla_display['Casos'] = tabla_display['Casos'].apply(format_large_number)
        tabla_display = tabla_display[['Rank', 'CIE10', 'nombre', 'categoria', 'Casos', 'Porcentaje']]
        tabla_display.columns = ['#', 'CIE-10', 'Enfermedad', 'Categoría', 'Casos', '%']

        st.dataframe(tabla_display, use_container_width=True, hide_index=True)

        # Gráfico de barras
        st.subheader(f"📈 Visualización Top {len(top_cronicas_filtrado)}")

        fig = create_bar_chart(
            top_cronicas_filtrado,
            x='Casos',
            y='nombre', # Usar nombre para el eje Y
            title=f'Top {len(top_cronicas_filtrado)} Enfermedades Crónicas',
            orientation='h'
        )
        fig.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            height=max(400, len(top_cronicas_filtrado) * 35)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No hay enfermedades seleccionadas para mostrar.")

    st.markdown("---")

    # Distribución por categoría
    st.subheader("🔍 Distribución por Categoría")

    col1, col2 = st.columns(2)

    casos_por_categoria = df_cronicas_data.groupby('categoria')['Casos'].sum().reset_index()
    casos_por_categoria = casos_por_categoria.sort_values('Casos', ascending=False)

    with col1:
        if not casos_por_categoria.empty:
            fig_pie = create_pie_chart(
                casos_por_categoria,
                values='Casos',
                names='categoria',
                title='Distribución por Categoría'
            )
            fig_pie.update_layout(height=500)
            st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        st.markdown("**Casos por Categoría:**")
        casos_por_categoria['Porcentaje'] = (casos_por_categoria['Casos'] / total_casos * 100).round(2)
        casos_por_categoria['Casos_fmt'] = casos_por_categoria['Casos'].apply(format_large_number)
        st.dataframe(
            casos_por_categoria[['categoria', 'Casos_fmt', 'Porcentaje']].rename(
                columns={'categoria': 'Categoría', 'Casos_fmt': 'Casos', 'Porcentaje': '%'}
            ),
            use_container_width=True,
            hide_index=True
        )

    st.markdown("---")

    # Tendencia temporal - Top 10
    st.subheader("📅 Tendencia Temporal - Top 10")

    top_10_codes = top_cronicas.head(10)['CIE10'].tolist()
    df_top10 = df_cronicas_data[df_cronicas_data['CIE10'].isin(top_10_codes)]

    if not df_top10.empty:
        tendencia = df_top10.groupby(['Año', 'CIE10'])['Casos'].sum().reset_index()

        fig_lineas = create_line_chart(
            tendencia,
            x='Año',
            y='Casos',
            title='Evolución Temporal de las 10 Crónicas Más Frecuentes',
            color='CIE10'
        )

        fig_lineas.update_layout(height=500)
        st.plotly_chart(fig_lineas, use_container_width=True)

    st.markdown("---")

    # Información adicional
    with st.expander("ℹ️ Información sobre Enfermedades Crónicas"):
        st.markdown("""
        **¿Qué son las enfermedades crónicas?**

        Las enfermedades crónicas no transmisibles (ECNT) son afecciones de larga duración
        con una progresión generalmente lenta. Son la principal causa de muerte y discapacidad
        en el mundo.

        **Categorías principales:**
        - **Metabólicas:** Diabetes, obesidad, dislipidemia, hiperuricemia
        - **Cardiovasculares:** Hipertensión, insuficiencia cardíaca, enfermedades coronarias
        - **Respiratorias:** EPOC, asma bronquial
        - **Digestivas:** Cirrosis hepática, enfermedad inflamatoria intestinal
        - **Renales:** Insuficiencia renal crónica, enfermedad renal diabética
        - **Reumatológicas:** Artritis reumatoide, osteoartrosis
        - **Neurológicas:** Epilepsia, enfermedad de Parkinson, demencias
        - **Psiquiátricas:** Depresión, trastornos de ansiedad
        - **Oncológicas:** Cáncer en sus diversas formas
        - **Hematológicas:** Anemias crónicas

        **Factores de riesgo:**
        - Tabaquismo
        - Sedentarismo
        - Dieta inadecuada
        - Consumo de alcohol
        - Estrés crónico

        **Importancia:**
        La vigilancia de enfermedades crónicas permite implementar programas de prevención,
        seguimiento y control que mejoran la calidad de vida de los pacientes y reducen
        complicaciones a largo plazo.

        **Uso de filtros:**
        - Utiliza los filtros de la barra lateral para analizar por unidad, año, sexo o edad
        - Los gráficos se actualizan automáticamente según los filtros aplicados
        """)
