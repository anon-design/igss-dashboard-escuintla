"""
Módulo de Enfermedades de Notificación Obligatoria (ENO)
Vigilancia y análisis de enfermedades que requieren notificación a autoridades sanitarias
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from config import COLORS
from utils.data_loader import is_eno
from utils.filters import get_top_n
from utils.colors import (
    create_bar_chart,
    create_line_chart,
    create_pie_chart,
    create_metric_card_html,
    format_large_number
)


def render(df, df_eno):
    """
    Renderiza el módulo de ENO

    Args:
        df: DataFrame filtrado con datos
        df_eno: DataFrame con catálogo ENO
    """
    st.title("⚠️ Enfermedades de Notificación Obligatoria")
    st.markdown("### Vigilancia epidemiológica de enfermedades que requieren notificación")

    st.markdown("---")

    if df.empty:
        st.warning("No hay datos disponibles con los filtros seleccionados.")
        return

    # Filtrar solo ENO
    df_eno_data = df[df['CIE10'].apply(lambda x: is_eno(x, df_eno))].copy()

    if df_eno_data.empty:
        st.warning("No se encontraron casos de ENO con los filtros seleccionados.")
        return

    # Agregar información de categoría
    df_eno_data = df_eno_data.merge(
        df_eno[['cie10', 'nombre', 'categoria', 'notificacion']],
        left_on='CIE10',
        right_on='cie10',
        how='left'
    )

    # Métricas principales
    col1, col2, col3 = st.columns(3)

    total_casos = int(df_eno_data['Casos'].sum())
    total_eno = df_eno_data['CIE10'].nunique()
    años_cubiertos = len(df_eno_data['Año'].unique())

    with col1:
        st.markdown(
            create_metric_card_html(
                "Total Casos ENO",
                total_casos,
                color='danger'
            ),
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            create_metric_card_html(
                "ENO Detectadas",
                total_eno,
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

    # Top N ENO
    st.subheader("📊 Top N Enfermedades de Notificación Obligatoria")

    # --- Filtros Dinámicos ---
    with st.expander("⚙️ Opciones de Visualización"):
        top_n_value = st.number_input(
            "Selecciona el número de enfermedades a mostrar (N):",
            min_value=5,
            max_value=50,
            value=20,
            step=5,
            key="top_n_eno"
        )
    
    # Calcular todos los ENOs y luego filtrar
    all_eno = df_eno_data.groupby(['CIE10', 'nombre', 'categoria', 'notificacion'])['Casos'].sum().reset_index()
    all_eno = all_eno.sort_values('Casos', ascending=False)

    with st.expander("Filtro de Exclusión de Enfermedades", expanded=False):
        diagnosticos_disponibles = all_eno['nombre'].tolist()
        diagnosticos_seleccionados = st.multiselect(
            "Selecciona las enfermedades a incluir:",
            options=diagnosticos_disponibles,
            default=diagnosticos_disponibles,
            key="exclude_filter_eno"
        )
    
    # Aplicar filtros
    top_eno_filtrado = all_eno[all_eno['nombre'].isin(diagnosticos_seleccionados)].head(top_n_value)
    
    if not top_eno_filtrado.empty:
        top_eno_filtrado['Rank'] = range(1, len(top_eno_filtrado) + 1)
        top_eno_filtrado['Porcentaje'] = (top_eno_filtrado['Casos'] / total_casos * 100).round(2)

        # Tabla formateada
        tabla_display = top_eno_filtrado.copy()
        tabla_display['Casos'] = tabla_display['Casos'].apply(format_large_number)
        tabla_display = tabla_display[['Rank', 'CIE10', 'nombre', 'categoria', 'notificacion', 'Casos', 'Porcentaje']]
        tabla_display.columns = ['#', 'CIE-10', 'Enfermedad', 'Categoría', 'Notificación', 'Casos', '%']

        st.dataframe(tabla_display, use_container_width=True, hide_index=True)

        # Gráfico de barras
        st.subheader(f"📈 Visualización Top {len(top_eno_filtrado)} ENO")

        fig = create_bar_chart(
            top_eno_filtrado,
            x='Casos',
            y='nombre', # Usar nombre para el eje Y
            title=f'Top {len(top_eno_filtrado)} Enfermedades de Notificación Obligatoria',
            orientation='h'
        )
        fig.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            height=max(400, len(top_eno_filtrado) * 35)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No hay enfermedades seleccionadas para mostrar.")

    st.markdown("---")

    # Distribución por categoría
    st.subheader("🔍 Distribución por Categoría")

    col1, col2 = st.columns(2)

    casos_por_categoria = df_eno_data.groupby('categoria')['Casos'].sum().reset_index()
    casos_por_categoria = casos_por_categoria.sort_values('Casos', ascending=False)

    with col1:
        if not casos_por_categoria.empty:
            fig_pie = create_pie_chart(
                casos_por_categoria,
                values='Casos',
                names='categoria',
                title='Distribución por Categoría de ENO'
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

    # Tendencia temporal - Top N
    st.subheader("📅 Tendencia Temporal de las Principales ENO")

    if not top_eno_filtrado.empty:
        num_top_temporal = st.slider(
            "Selecciona el número de ENO para el análisis temporal:", 
            min_value=1, 
            max_value=min(10, len(top_eno_filtrado)), 
            value=min(5, len(top_eno_filtrado)),
            key="slider_temporal_eno"
        )

        top_codes_temporal = top_eno_filtrado.head(num_top_temporal)['CIE10'].tolist()
        df_top_temporal = df_eno_data[df_eno_data['CIE10'].isin(top_codes_temporal)]

        if not df_top_temporal.empty:
            tendencia = df_top_temporal.groupby(['Año', 'nombre'])['Casos'].sum().reset_index()

            fig_lineas = create_line_chart(
                tendencia,
                x='Año',
                y='Casos',
                title=f'Evolución Temporal de las {num_top_temporal} ENO Más Frecuentes',
                color='nombre'
            )
            st.plotly_chart(fig_lineas, use_container_width=True)
    else:
        st.warning("No hay enfermedades seleccionadas para mostrar análisis temporal.")

    st.markdown("---")

    # Información adicional
    with st.expander("ℹ️ Información sobre Enfermedades de Notificación Obligatoria"):
        st.markdown("""
        **¿Qué son las ENO?**

        Las Enfermedades de Notificación Obligatoria (ENO) son aquellas que por su potencial
        epidémico, gravedad o impacto en la salud pública deben ser reportadas a las autoridades
        sanitarias de manera inmediata o semanal.

        **Tipos de notificación:**
        - **Inmediata:** Requiere notificación en menos de 24 horas (ej: sarampión, cólera, peste)
        - **Semanal:** Se reporta semanalmente (ej: varicela, hepatitis)
        - **Individual:** Cada caso debe notificarse individualmente

        **Categorías principales:**
        - Inmediata
        - Inmunoprevenible
        - Vectorial (transmitidas por vectores)
        - ITS (Infecciones de Transmisión Sexual)
        - Zoonótica (de animales a humanos)
        - Transmisión alimentaria
        - Y otras categorías específicas

        **Importancia:**
        El sistema de vigilancia epidemiológica de ENO permite detectar brotes tempranamente,
        implementar medidas de control y prevenir epidemias.

        **Uso de filtros:**
        - Utiliza los filtros de la barra lateral para analizar por unidad, año o sexo
        - Los gráficos se actualizan automáticamente según los filtros aplicados
        """)
