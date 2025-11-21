"""
Módulo de Morbilidad en Adultos (>15 años)
Análisis de los 25 diagnósticos más frecuentes en población adulta
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from config import COLORS
from utils.filters import filter_by_age_group, get_top_n, aggregate_by_period
from utils.colors import create_bar_chart, create_line_chart, create_metric_card_html, format_large_number


def render(df, df_eno, df_cronicas, df_diagnosticos):
    """
    Renderiza el módulo de morbilidad en adultos

    Args:
        df: DataFrame filtrado con datos
        df_eno: DataFrame con catálogo ENO
        df_cronicas: DataFrame con catálogo de crónicas
        df_diagnosticos: DataFrame con el catálogo completo de nombres de CIE-10
    """
    st.title("👨 Morbilidad en Adultos")
    st.markdown("### Análisis de los 25 diagnósticos más frecuentes en población adulta (>15 años)")

    st.markdown("---")

    # Filtrar solo adultos (excluir 0-15)
    df_adultos = filter_by_age_group(df, pediatrico=False)

    if df_adultos.empty:
        st.warning("No hay datos disponibles para población adulta con los filtros seleccionados.")
        return

    # Métricas principales
    col1, col2, col3 = st.columns(3)

    total_casos = int(df_adultos['Casos'].sum())
    total_diagnosticos = df_adultos['CIE10'].nunique()
    años_cubiertos = len(df_adultos['Año'].unique())

    with col1:
        st.markdown(
            create_metric_card_html(
                "Total Casos Adultos",
                total_casos,
                color='primary'
            ),
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            create_metric_card_html(
                "Diagnósticos Únicos",
                total_diagnosticos,
                color='success'
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

    # Top N diagnósticos
    st.subheader("📊 Top N Diagnósticos Más Frecuentes")

    # Widget para seleccionar N
    top_n_value = st.number_input(
        "Selecciona el número de diagnósticos a mostrar (N):",
        min_value=5,
        max_value=100,
        value=25,
        step=5
    )

    top_n = get_top_n(df_adultos, n=top_n_value, group_by='CIE10')

    if not top_n.empty:
        # Unir con el catálogo completo de nombres
        top_n = pd.merge(top_n, df_diagnosticos, left_on='CIE10', right_on='cie10', how='left')
        top_n['Diagnóstico'] = top_n['nombre'].fillna('Nombre no disponible')
        top_n.drop(columns=['cie10', 'nombre'], inplace=True)
        
        # Filtro de exclusión
        diagnosticos_disponibles = top_n['Diagnóstico'].tolist()
        diagnosticos_seleccionados = st.multiselect(
            "Selecciona los diagnósticos a incluir en la tabla y gráfico:",
            options=diagnosticos_disponibles,
            default=diagnosticos_disponibles
        )
        
        # Filtrar el dataframe basado en la selección
        top_n_filtrado = top_n[top_n['Diagnóstico'].isin(diagnosticos_seleccionados)]

        # Calcular porcentajes
        top_n_filtrado['Porcentaje'] = (top_n_filtrado['Casos'] / total_casos * 100).round(2)

        # Agregar información adicional (ENO, Crónica)
        top_n_filtrado['Es_ENO'] = top_n_filtrado['CIE10'].apply(
            lambda x: '⚠️' if x in df_eno['cie10'].values else ''
        )
        top_n_filtrado['Es_Cronica'] = top_n_filtrado['CIE10'].apply(
            lambda x: '💊' if x in df_cronicas['cie10'].values else ''
        )

        # Crear tabla formateada
        top_display = top_n_filtrado.copy()
        top_display['Casos'] = top_display['Casos'].apply(format_large_number)
        
        # Reordenar columnas para mostrar
        column_order = ['#', 'Diagnóstico', 'Código CIE-10', 'Casos', '%', 'ENO', 'Crónica']
        top_display_renamed = top_display.rename(columns={
            'Rank': '#',
            'CIE10': 'Código CIE-10',
            'Porcentaje': '%',
            'Es_ENO': 'ENO',
            'Es_Cronica': 'Crónica'
        })
        st.dataframe(top_display_renamed[column_order], use_container_width=True, hide_index=True)

        st.info("💡 **Leyenda:** ⚠️ = Enfermedad de Notificación Obligatoria | 💊 = Enfermedad Crónica")

        # Gráfico de barras horizontales
        st.subheader(f"📈 Visualización Top {len(top_n_filtrado)}")

        if not top_n_filtrado.empty:
            fig = create_bar_chart(
                top_n_filtrado,
                x='Casos',
                y='Diagnóstico',
                title=f'Top {len(top_n_filtrado)} Diagnósticos en Adultos',
                orientation='h'
            )

            fig.update_layout(
                yaxis={'categoryorder': 'total ascending'},
                height=max(400, len(top_n_filtrado) * 30) # Altura dinámica
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No hay diagnósticos seleccionados para mostrar en el gráfico.")

    st.markdown("---")

    # Análisis temporal del Top 10
    st.subheader("📅 Tendencia Temporal - Top 10 Diagnósticos")

    top_10_codes = top_25.head(10)['CIE10'].tolist()
    df_top10 = df_adultos[df_adultos['CIE10'].isin(top_10_codes)]

    # Agrupar por año y código
    tendencia = df_top10.groupby(['Año', 'CIE10'])['Casos'].sum().reset_index()

    if not tendencia.empty:
        fig_lineas = create_line_chart(
            tendencia,
            x='Año',
            y='Casos',
            title='Evolución Temporal de los 10 Diagnósticos Más Frecuentes',
            color='CIE10'
        )

        fig_lineas.update_layout(height=500)

        st.plotly_chart(fig_lineas, use_container_width=True)

    st.markdown("---")

    # Distribución por sexo del Top 10
    st.subheader("👥 Distribución por Sexo - Top 10 Diagnósticos")

    col1, col2 = st.columns(2)

    with col1:
        # Por sexo
        dist_sexo = df_top10.groupby(['CIE10', 'Sexo'])['Casos'].sum().reset_index()

        if not dist_sexo.empty:
            from utils.colors import create_stacked_bar

            fig_sexo = create_stacked_bar(
                dist_sexo,
                x='CIE10',
                y='Casos',
                title='Distribución por Sexo',
                color='Sexo'
            )

            fig_sexo.update_layout(height=400)
            st.plotly_chart(fig_sexo, use_container_width=True)

    with col2:
        # Tabla resumen por sexo
        pivot_sexo = df_top10.pivot_table(
            index='CIE10',
            columns='Sexo',
            values='Casos',
            aggfunc='sum',
            fill_value=0
        )

        if not pivot_sexo.empty:
            st.markdown("**Resumen Numérico:**")
            st.dataframe(pivot_sexo.style.format("{:,.0f}"), use_container_width=True)

    st.markdown("---")

    # Información adicional
    with st.expander("ℹ️ Información sobre este análisis"):
        st.markdown("""
        **Criterios de inclusión:**
        - Población adulta: Todos los rangos de edad excepto 0-15 años
        - Se analizan los 25 diagnósticos con mayor frecuencia

        **Interpretación:**
        - Los diagnósticos marcados con ⚠️ son Enfermedades de Notificación Obligatoria (ENO)
        - Los diagnósticos marcados con 💊 son Enfermedades Crónicas
        - El porcentaje se calcula sobre el total de casos en adultos

        **Uso de filtros:**
        - Utiliza los filtros de la barra lateral para segmentar por unidad, año o sexo
        - Los gráficos se actualizan automáticamente según los filtros aplicados
        """)
