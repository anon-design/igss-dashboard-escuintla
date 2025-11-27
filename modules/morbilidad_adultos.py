"""
Módulo de Morbilidad en Adultos (>15 años)
Análisis de los 25 diagnósticos más frecuentes en población adulta
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from utils.colors import create_bar_chart, create_line_chart, create_metric_card_html, format_large_number, create_stacked_bar

# Helper para convertir DataFrame a CSV para descarga
@st.cache_data
def convert_df_to_csv(df):
    return df.to_csv(index=False, encoding='utf-8-sig')


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
    st.markdown("### Análisis de los diagnósticos más frecuentes en población adulta (>15 años)")

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
    show_all_dx = st.checkbox("Mostrar todos los diagnósticos", key="show_all_adultos")
    
    subheader_dx = "📊 Diagnósticos Frecuentes" if show_all_dx else "📊 Top N Diagnósticos Más Frecuentes"
    st.subheader(subheader_dx)

    top_n_value = 25
    if not show_all_dx:
        with st.expander("⚙️ Opciones de Visualización"):
            top_n_value = st.number_input(
                "Selecciona el número de diagnósticos a mostrar (N):",
                min_value=5,
                max_value=100,
                value=25,
                step=5,
                disabled=show_all_dx
            )
    
    n_param = None if show_all_dx else top_n_value
    top_n = get_top_n(df_adultos, n=n_param, group_by='CIE10')

    if not top_n.empty:
        # Unir con el catálogo completo de nombres
        top_n = pd.merge(top_n, df_diagnosticos, left_on='CIE10', right_on='cie10', how='left')
        top_n['Diagnóstico'] = top_n['nombre'].fillna('Nombre no disponible')
        top_n.drop(columns=['cie10', 'nombre'], inplace=True)
        
        with st.expander("Filtro de Exclusión de Diagnósticos", expanded=False):
            diagnosticos_disponibles = top_n['Diagnóstico'].tolist()
            diagnosticos_seleccionados = st.multiselect(
                "Selecciona los diagnósticos a incluir en la tabla y gráfico:",
                options=diagnosticos_disponibles,
                default=diagnosticos_disponibles
            )
        
        top_n_filtrado = top_n[top_n['Diagnóstico'].isin(diagnosticos_seleccionados)]
        top_n_filtrado['Porcentaje'] = (top_n_filtrado['Casos'] / total_casos * 100).round(2)
        top_n_filtrado['Es_ENO'] = top_n_filtrado['CIE10'].apply(
            lambda x: '⚠️' if x in df_eno['cie10'].values else ''
        )
        top_n_filtrado['Es_Cronica'] = top_n_filtrado['CIE10'].apply(
            lambda x: '💊' if x in df_cronicas['cie10'].values else ''
        )

        top_display = top_n_filtrado.copy()
        top_display['Casos'] = top_display['Casos'].apply(format_large_number)
        
        column_order = ['#', 'Diagnóstico', 'Código CIE-10', 'Casos', '%', 'ENO', 'Crónica']
        top_display_renamed = top_display.rename(columns={
            'Rank': '#',
            'CIE10': 'Código CIE-10',
            'Porcentaje': '%',
            'Es_ENO': 'ENO',
            'Es_Cronica': 'Crónica'
        })
        st.dataframe(top_display_renamed[column_order], width='stretch', hide_index=True)

        st.info("💡 **Leyenda:** ⚠️ = Enfermedad de Notificación Obligatoria | 💊 = Enfermedad Crónica")

        df_download = get_top_n(df_adultos, n=None, group_by='CIE10')
        df_download = pd.merge(df_download, df_diagnosticos, left_on='CIE10', right_on='cie10', how='left')
        df_download['Diagnóstico'] = df_download['nombre'].fillna('Nombre no disponible')
        csv_data = convert_df_to_csv(df_download[['Rank', 'CIE10', 'Diagnóstico', 'Casos']])
        
        st.download_button(
           label="📥 Descargar todos los diagnósticos (CSV)",
           data=csv_data,
           file_name="diagnosticos_adultos.csv",
           mime="text/csv",
        )

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
                height=max(400, len(top_n_filtrado) * 30)
            )
            st.plotly_chart(fig, width='stretch')
        else:
            st.warning("No hay diagnósticos seleccionados para mostrar en el gráfico.")

    st.markdown("---")
    
    st.subheader("📅 Tendencia Temporal de los Diagnósticos Principales")
    
    if not top_n.empty: # Use top_n here before filtering
        num_top_temporal = st.slider(
            "Selecciona el número de diagnósticos para el análisis temporal:", 
            min_value=1, 
            max_value=min(10, len(top_n)), 
            value=min(5, len(top_n)),
            key="slider_temporal_adultos"
        )
        top_codes_temporal = top_n.head(num_top_temporal)['CIE10'].tolist()
        df_top_temporal = df_adultos[df_adultos['CIE10'].isin(top_codes_temporal)]
        
        df_top_temporal = pd.merge(df_top_temporal, top_n[['CIE10', 'Diagnóstico']], on='CIE10', how='left')

        tendencia = df_top_temporal.groupby(['Año', 'Diagnóstico'])['Casos'].sum().reset_index()
        
        if not tendencia.empty:
            fig_lineas = create_line_chart(
                tendencia,
                x='Año',
                y='Casos',
                title=f'Evolución Temporal de los {num_top_temporal} Diagnósticos Más Frecuentes',
                color='Diagnóstico'
            )
            st.plotly_chart(fig_lineas, width='stretch')

        st.markdown("---")

        st.subheader(f"👥 Distribución por Sexo - Top {num_top_temporal} Diagnósticos")

        col1, col2 = st.columns([3, 2])

        with col1:
            dist_sexo = df_top_temporal.groupby(['Diagnóstico', 'Sexo'])['Casos'].sum().reset_index()

            if not dist_sexo.empty:
                fig_sexo = create_stacked_bar(
                    dist_sexo,
                    x='Diagnóstico',
                    y='Casos',
                    title='Distribución por Sexo',
                    color='Sexo'
                )
                st.plotly_chart(fig_sexo, width='stretch')

        with col2:
            pivot_sexo = df_top_temporal.pivot_table(
                index='Diagnóstico',
                columns='Sexo',
                values='Casos',
                aggfunc='sum',
                fill_value=0
            )

            if not pivot_sexo.empty:
                st.markdown("**Resumen Numérico:**")
                st.dataframe(pivot_sexo.style.format("{:,.0f}"), width='stretch')
    else:
        st.warning("No hay diagnósticos para mostrar análisis temporal o por sexo.")

    st.markdown("---")
    with st.expander("ℹ️ Información sobre este análisis"):
        st.markdown("""
        **Criterios de inclusión:**
        - Población adulta: Todos los rangos de edad excepto 0-15 años
        - Se analizan los diagnósticos con mayor frecuencia

        **Interpretación:**
        - Los diagnósticos marcados con ⚠️ son Enfermedades de Notificación Obligatoria (ENO)
        - Los diagnósticos marcados con 💊 son Enfermedades Crónicas
        - El porcentaje se calcula sobre el total de casos en adultos

        **Uso de filtros:**
        - Utiliza los filtros de la barra lateral para segmentar por unidad, año o sexo
        - Los gráficos se actualizan automáticamente según los filtros aplicados
        """)

