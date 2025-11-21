"""
Módulo de Análisis Geográfico
Distribución de casos por unidad médica del IGSS Escuintla
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from config import COLORS
from utils.filters import get_top_n
from utils.colors import (
    create_bar_chart,
    create_line_chart,
    create_pie_chart,
    create_metric_card_html,
    format_large_number,
    create_stacked_bar
)


def render(df, df_eno, df_cronicas, df_diagnosticos):
    """
    Renderiza el módulo de análisis geográfico

    Args:
        df: DataFrame filtrado con datos
        df_eno: DataFrame con catálogo ENO
        df_cronicas: DataFrame con catálogo de crónicas
        df_diagnosticos: DataFrame con el catálogo completo de nombres de CIE-10
    """
    st.title("🗺️ Análisis Geográfico")
    st.markdown("### Distribución de casos por unidad médica del IGSS Escuintla")

    st.markdown("---")

    if df.empty:
        st.warning("No hay datos disponibles con los filtros seleccionados.")
        return

    # Métricas principales
    col1, col2, col3 = st.columns(3)

    total_casos = int(df['Casos'].sum())
    total_unidades = df['Unidad'].nunique()
    unidad_principal = df.groupby('Unidad')['Casos'].sum().idxmax() if total_casos > 0 else 'N/A'

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
                "Unidades Representadas",
                total_unidades,
                color='success'
            ),
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            create_metric_card_html(
                "Unidad Principal",
                unidad_principal[:20] + "..." if len(str(unidad_principal)) > 20 else unidad_principal,
                color='info'
            ),
            unsafe_allow_html=True
        )

    st.markdown("---")

    # Distribución por unidad
    st.subheader("📊 Distribución de Casos por Unidad")

    casos_por_unidad = df.groupby('Unidad')['Casos'].sum().reset_index()
    casos_por_unidad = casos_por_unidad.sort_values('Casos', ascending=False)

    if not casos_por_unidad.empty:
        # Calcular porcentajes
        casos_por_unidad['Porcentaje'] = (casos_por_unidad['Casos'] / total_casos * 100).round(2)
        casos_por_unidad['Rank'] = range(1, len(casos_por_unidad) + 1)

        # Crear tabla formateada
        tabla_display = casos_por_unidad.copy()
        tabla_display['Casos'] = tabla_display['Casos'].apply(format_large_number)
        tabla_display = tabla_display[['Rank', 'Unidad', 'Casos', 'Porcentaje']]
        tabla_display.columns = ['#', 'Unidad Médica', 'Casos', '%']

        st.dataframe(tabla_display, use_container_width=True, hide_index=True)

        # Gráfico de barras horizontales
        st.subheader("📈 Visualización por Unidad")

        fig_barras = create_bar_chart(
            casos_por_unidad,
            x='Casos',
            y='Unidad',
            title='Distribución de Casos por Unidad Médica',
            orientation='h'
        )

        fig_barras.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            height=max(400, len(casos_por_unidad) * 50)  # Altura dinámica
        )

        st.plotly_chart(fig_barras, use_container_width=True)

    st.markdown("---")

    # Gráfico circular - Distribución porcentual
    st.subheader("🥧 Distribución Porcentual por Unidad")

    col1, col2 = st.columns(2)

    with col1:
        if not casos_por_unidad.empty:
            # Si hay más de 5 unidades, agrupar las menores en "Otros"
            if len(casos_por_unidad) > 5:
                top_5 = casos_por_unidad.head(5).copy()
                otros_casos = casos_por_unidad.iloc[5:]['Casos'].sum()
                otros_row = pd.DataFrame({
                    'Unidad': ['Otros'],
                    'Casos': [otros_casos],
                    'Porcentaje': [(otros_casos / total_casos * 100)]
                })
                data_pie = pd.concat([top_5, otros_row], ignore_index=True)
            else:
                data_pie = casos_por_unidad.copy()

            fig_pie = create_pie_chart(
                data_pie,
                values='Casos',
                names='Unidad',
                title='Distribución Porcentual por Unidad'
            )

            fig_pie.update_layout(height=500)
            st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        st.markdown("**Resumen por Unidad:**")
        resumen_display = casos_por_unidad.copy()
        resumen_display['Casos'] = resumen_display['Casos'].apply(format_large_number)
        resumen_display = resumen_display[['Rank', 'Unidad', 'Casos', 'Porcentaje']]
        resumen_display.columns = ['#', 'Unidad', 'Casos', '%']
        st.dataframe(resumen_display, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Tendencia temporal por unidad
    st.subheader("📅 Tendencia Temporal por Unidad")

    # Usar las top 5 unidades para no saturar el gráfico
    top_5_unidades = casos_por_unidad.head(5)['Unidad'].tolist()
    df_top5 = df[df['Unidad'].isin(top_5_unidades)]

    if not df_top5.empty and 'Año' in df_top5.columns:
        tendencia_unidades = df_top5.groupby(['Año', 'Unidad'])['Casos'].sum().reset_index()

        if not tendencia_unidades.empty:
            fig_lineas = create_line_chart(
                tendencia_unidades,
                x='Año',
                y='Casos',
                title='Evolución Temporal - Top 5 Unidades',
                color='Unidad'
            )

            fig_lineas.update_layout(height=500)
            st.plotly_chart(fig_lineas, use_container_width=True)

    st.markdown("---")

    # Top N diagnósticos por unidad
    st.subheader("🔍 Top N Diagnósticos por Unidad")

    # Selector de unidad
    unidades_disponibles = sorted(df['Unidad'].unique())
    unidad_seleccionada = st.selectbox(
        "Selecciona una unidad para ver sus diagnósticos más frecuentes:",
        unidades_disponibles,
        index=0,
        key="unidad_selector_geografico"
    )

    if unidad_seleccionada:
        df_unidad = df[df['Unidad'] == unidad_seleccionada]

        if not df_unidad.empty:
            # --- Filtros Dinámicos ---
            with st.expander("⚙️ Opciones de Visualización"):
                top_n_value = st.number_input(
                    "Selecciona el número de diagnósticos a mostrar (N):",
                    min_value=5,
                    max_value=50,
                    value=10,
                    step=5,
                    key="top_n_geografico"
                )
            
            # Calcular todos los diagnósticos de la unidad
            all_diagnosticos_unidad = df_unidad.groupby('CIE10')['Casos'].sum().reset_index()
            all_diagnosticos_unidad = all_diagnosticos_unidad.sort_values('Casos', ascending=False)
            
            # Unir nombres ANTES del filtro de exclusión
            all_diagnosticos_unidad = pd.merge(all_diagnosticos_unidad, df_diagnosticos, left_on='CIE10', right_on='cie10', how='left')
            all_diagnosticos_unidad['Diagnóstico'] = all_diagnosticos_unidad['nombre'].fillna('Nombre no disponible')
            all_diagnosticos_unidad.drop(columns=['cie10', 'nombre'], inplace=True)

            with st.expander("Filtro de Exclusión de Diagnósticos", expanded=False):
                diagnosticos_disponibles = all_diagnosticos_unidad['Diagnóstico'].tolist()
                diagnosticos_seleccionados = st.multiselect(
                    "Selecciona los diagnósticos a incluir:",
                    options=diagnosticos_disponibles,
                    default=diagnosticos_disponibles,
                    key="exclude_filter_geografico"
                )
            
            # Aplicar filtros
            top_n_filtrado = all_diagnosticos_unidad[all_diagnosticos_unidad['Diagnóstico'].isin(diagnosticos_seleccionados)].head(top_n_value)

            if not top_n_filtrado.empty:
                top_n_filtrado['Rank'] = range(1, len(top_n_filtrado) + 1)
                total_unidad = df_unidad['Casos'].sum()
                top_n_filtrado['Porcentaje'] = (top_n_filtrado['Casos'] / total_unidad * 100).round(2)

                # Marcar ENO y crónicas
                top_n_filtrado['Es_ENO'] = top_n_filtrado['CIE10'].apply(
                    lambda x: '⚠️' if x in df_eno['cie10'].values else ''
                )
                top_n_filtrado['Es_Cronica'] = top_n_filtrado['CIE10'].apply(
                    lambda x: '💊' if x in df_cronicas['cie10'].values else ''
                )

                # Tabla formateada
                col1, col2 = st.columns([2, 1])

                with col1:
                    tabla_top_n = top_n_filtrado.copy()
                    tabla_top_n['Casos'] = tabla_top_n['Casos'].apply(format_large_number)
                    
                    # Directamente asignar los nombres de las columnas para evitar conflictos
                    tabla_top_n = tabla_top_n[['Rank', 'Diagnóstico', 'CIE10', 'Casos', 'Porcentaje', 'Es_ENO', 'Es_Cronica']]
                    tabla_top_n.columns = ['#', 'Diagnóstico', 'CIE-10', 'Casos', '%', 'ENO', 'Crónica']
                    
                    st.dataframe(tabla_top_n, use_container_width=True, hide_index=True)
                    st.info("💡 **Leyenda:** ⚠️ = ENO | 💊 = Crónica")

                with col2:
                    # Gráfico de barras
                    fig_top_n = create_bar_chart(
                        top_n_filtrado,
                        x='Casos',
                        y='Diagnóstico',
                        title=f'Top {len(top_n_filtrado)} - {unidad_seleccionada}',
                        orientation='h'
                    )
                    fig_top_n.update_layout(
                        yaxis={'categoryorder': 'total ascending'},
                        height=max(400, len(top_n_filtrado) * 30)
                    )
                    st.plotly_chart(fig_top_n, use_container_width=True)
            else:
                st.warning("No hay diagnósticos seleccionados para mostrar.")

    st.markdown("---")

    # Comparación de sexo entre unidades (Top 5)
    st.subheader("👥 Distribución por Sexo - Top 5 Unidades")

    df_top5_sexo = df[df['Unidad'].isin(top_5_unidades)]

    if not df_top5_sexo.empty and 'Sexo' in df_top5_sexo.columns:
        dist_sexo = df_top5_sexo.groupby(['Unidad', 'Sexo'])['Casos'].sum().reset_index()

        if not dist_sexo.empty:
            fig_sexo = create_stacked_bar(
                dist_sexo,
                x='Unidad',
                y='Casos',
                title='Distribución por Sexo - Top 5 Unidades',
                color='Sexo'
            )

            fig_sexo.update_layout(height=500)
            st.plotly_chart(fig_sexo, use_container_width=True)

    st.markdown("---")

    # Comparación de edades entre unidades
    st.subheader("📊 Distribución por Edad - Comparación entre Unidades")

    if 'Edad' in df.columns:
        # Crear grupos de edad
        def clasificar_edad(edad):
            try:
                edad_num = int(edad.split('-')[0]) if isinstance(edad, str) and '-' in edad else int(edad)
                if edad_num < 15:
                    return '0-14 (Pediátrico)'
                elif edad_num < 30:
                    return '15-29 (Joven)'
                elif edad_num < 45:
                    return '30-44 (Adulto)'
                elif edad_num < 60:
                    return '45-59 (Adulto mayor)'
                else:
                    return '60+ (Adulto mayor)'
            except:
                return 'No especificado'

        df_edad = df.copy()
        df_edad['Grupo_Edad'] = df_edad['Edad'].apply(clasificar_edad)

        # Filtrar top 5 unidades
        df_edad_top5 = df_edad[df_edad['Unidad'].isin(top_5_unidades)]

        dist_edad = df_edad_top5.groupby(['Unidad', 'Grupo_Edad'])['Casos'].sum().reset_index()

        if not dist_edad.empty:
            fig_edad = create_stacked_bar(
                dist_edad,
                x='Unidad',
                y='Casos',
                title='Distribución por Grupo de Edad - Top 5 Unidades',
                color='Grupo_Edad'
            )

            fig_edad.update_layout(height=500)
            st.plotly_chart(fig_edad, use_container_width=True)

    st.markdown("---")

    # Información adicional
    with st.expander("ℹ️ Información sobre el Análisis Geográfico"):
        st.markdown("""
        **¿Qué es el análisis geográfico?**

        El análisis geográfico permite identificar la distribución de casos de morbilidad
        entre las diferentes unidades médicas del IGSS Escuintla, facilitando:

        - Identificación de unidades con mayor carga asistencial
        - Detección de patrones específicos por ubicación
        - Planificación de recursos según demanda
        - Optimización de la red de servicios

        **Unidades incluidas en el análisis:**
        - **General Escuintla:** Datos consolidados de toda la región
        - **Hospital Escuintla:** Hospital de referencia departamental
        - **Hospital Santa Lucia Cotzumalguapa:** Hospital regional
        - **Consultorio Masagua:** Unidad periférica
        - **Consultorio la Democracia:** Unidad periférica
        - **Consultorio Siquinala:** Unidad periférica

        **Interpretación:**
        - Las unidades hospitalarias suelen tener mayor volumen por su complejidad
        - Los consultorios periféricos atienden principalmente patología ambulatoria
        - La distribución por edad refleja el perfil demográfico de cada área

        **Aplicaciones prácticas:**
        - **Planificación:** Asignación de personal según carga de trabajo
        - **Logística:** Distribución de insumos y medicamentos
        - **Prevención:** Programas focalizados según perfil epidemiológico local
        - **Referencia:** Optimización de sistemas de referencia y contrarreferencia

        **Uso de filtros:**
        - Utiliza los filtros de la barra lateral para analizar períodos específicos
        - Combina filtros de año, sexo y edad para análisis detallados
        - Los gráficos se actualizan automáticamente según los filtros aplicados
        """)
