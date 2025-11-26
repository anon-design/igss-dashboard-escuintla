"""
Módulo de Análisis Cruzado: Unidad de Atención × Procedencia Geográfica
Compara el perfil de procedencia de cada unidad médica

Este módulo permite analizar y comparar de dónde vienen los pacientes
a cada unidad del IGSS, identificando patrones de cobertura territorial.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from config import COLORS
from utils.filters import UNIDAD_GENERAL_PROCEDENCIA
from utils.colors import (
    create_metric_card_html,
    format_large_number,
    create_bar_chart,
    create_pie_chart
)


def get_unidades_especificas_procedencia(df):
    """Obtiene lista de unidades específicas (excluye General)"""
    todas = df['Unidad'].unique().tolist()
    return [u for u in todas if u != UNIDAD_GENERAL_PROCEDENCIA]


def calcular_perfil_unidad(df, unidad):
    """
    Calcula el perfil de procedencia para una unidad específica

    Returns:
        dict con métricas y distribuciones
    """
    df_unidad = df[df['Unidad'] == unidad].copy()

    if df_unidad.empty:
        return None

    total_casos = df_unidad['Casos'].sum()

    # Distribución por departamento
    dist_depto = df_unidad.groupby('Departamento')['Casos'].sum().reset_index()
    dist_depto['Porcentaje'] = (dist_depto['Casos'] / total_casos * 100).round(2)
    dist_depto = dist_depto.sort_values('Casos', ascending=False)

    # Distribución por municipio
    dist_muni = df_unidad.groupby(['Municipio', 'Departamento'])['Casos'].sum().reset_index()
    dist_muni['Porcentaje'] = (dist_muni['Casos'] / total_casos * 100).round(2)
    dist_muni = dist_muni.sort_values('Casos', ascending=False)

    # Concentración geográfica
    top1_depto = dist_depto.iloc[0] if len(dist_depto) > 0 else None
    top3_pct = dist_depto.head(3)['Porcentaje'].sum() if len(dist_depto) >= 3 else 0
    top5_pct = dist_depto.head(5)['Porcentaje'].sum() if len(dist_depto) >= 5 else 0

    return {
        'total_casos': total_casos,
        'n_departamentos': df_unidad['Departamento'].nunique(),
        'n_municipios': df_unidad['Municipio'].nunique(),
        'dist_depto': dist_depto,
        'dist_muni': dist_muni,
        'top1_depto': top1_depto,
        'top3_pct': top3_pct,
        'top5_pct': top5_pct
    }


def crear_heatmap_unidad_depto(df, unidades):
    """
    Crea heatmap de Unidad × Departamento

    Args:
        df: DataFrame de procedencia
        unidades: Lista de unidades a incluir

    Returns:
        Plotly Figure
    """
    df_filtrado = df[df['Unidad'].isin(unidades)].copy()

    # Pivotar datos
    pivot = df_filtrado.groupby(['Unidad', 'Departamento'])['Casos'].sum().reset_index()
    pivot_wide = pivot.pivot(index='Departamento', columns='Unidad', values='Casos').fillna(0)

    # Normalizar por columna (porcentaje dentro de cada unidad)
    pivot_pct = pivot_wide.div(pivot_wide.sum(axis=0), axis=1) * 100

    # Ordenar por total de casos
    pivot_pct = pivot_pct.loc[pivot_pct.sum(axis=1).sort_values(ascending=False).index]

    # Top 15 departamentos
    pivot_pct = pivot_pct.head(15)

    # Renombrar columnas (quitar " Procedencia")
    pivot_pct.columns = [c.replace(' Procedencia', '') for c in pivot_pct.columns]

    fig = px.imshow(
        pivot_pct,
        labels=dict(x="Unidad de Atención", y="Departamento de Procedencia", color="% Casos"),
        color_continuous_scale='Blues',
        aspect='auto'
    )

    fig.update_layout(
        title='Distribución Porcentual: Departamento × Unidad',
        height=500,
        xaxis_tickangle=-45
    )

    return fig


def crear_radar_comparativo(df, unidades, top_deptos=8):
    """
    Crea gráfico radar comparando el perfil de procedencia de múltiples unidades
    """
    df_filtrado = df[df['Unidad'].isin(unidades)].copy()

    # Top departamentos general
    top_deptos_list = df_filtrado.groupby('Departamento')['Casos'].sum().nlargest(top_deptos).index.tolist()

    # Calcular porcentajes por unidad
    datos_radar = []
    for unidad in unidades:
        df_unidad = df_filtrado[df_filtrado['Unidad'] == unidad]
        total = df_unidad['Casos'].sum()
        for depto in top_deptos_list:
            casos_depto = df_unidad[df_unidad['Departamento'] == depto]['Casos'].sum()
            pct = (casos_depto / total * 100) if total > 0 else 0
            datos_radar.append({
                'Unidad': unidad.replace(' Procedencia', ''),
                'Departamento': depto,
                'Porcentaje': pct
            })

    df_radar = pd.DataFrame(datos_radar)

    fig = px.line_polar(
        df_radar,
        r='Porcentaje',
        theta='Departamento',
        color='Unidad',
        line_close=True,
        title='Perfil de Procedencia por Unidad (Top Departamentos)'
    )

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, df_radar['Porcentaje'].max() * 1.1])
        ),
        height=500
    )

    return fig


def render(df_procedencia):
    """
    Renderiza el módulo de análisis cruzado Unidad × Procedencia

    Args:
        df_procedencia: DataFrame con datos de procedencia (todas las unidades)
    """
    st.title("Análisis Cruzado: Unidad × Procedencia")
    st.markdown("### Comparación del perfil geográfico de pacientes por unidad de atención")

    st.markdown("---")

    if df_procedencia is None or df_procedencia.empty:
        st.warning("No hay datos de procedencia disponibles.")
        return

    # Verificar que hay unidades específicas
    unidades_especificas = get_unidades_especificas_procedencia(df_procedencia)

    if not unidades_especificas:
        st.error("No hay unidades específicas de atención disponibles.")
        return

    # =========================================================================
    # SELECTOR DE UNIDADES
    # =========================================================================

    st.subheader("Selección de Unidades a Comparar")

    unidades_nombres = [u.replace(' Procedencia', '') for u in unidades_especificas]
    unidades_seleccionadas_nombres = st.multiselect(
        "Unidades a analizar:",
        options=unidades_nombres,
        default=unidades_nombres[:4],  # Primeras 4 por defecto
        key="cruzado_unidades"
    )

    if not unidades_seleccionadas_nombres:
        st.warning("Seleccione al menos una unidad para analizar.")
        return

    # Mapear de vuelta a nombres completos
    unidades_seleccionadas = [f"{u} Procedencia" for u in unidades_seleccionadas_nombres]

    st.markdown("---")

    # =========================================================================
    # MÉTRICAS COMPARATIVAS
    # =========================================================================

    st.subheader("Resumen por Unidad")

    # Calcular perfiles
    perfiles = {}
    for unidad in unidades_seleccionadas:
        perfiles[unidad] = calcular_perfil_unidad(df_procedencia, unidad)

    # Mostrar métricas en columnas
    cols = st.columns(len(unidades_seleccionadas))

    for i, (unidad, perfil) in enumerate(perfiles.items()):
        if perfil:
            with cols[i]:
                nombre_corto = unidad.replace(' Procedencia', '')
                st.markdown(f"**{nombre_corto}**")
                st.metric("Casos", format_large_number(int(perfil['total_casos'])))
                st.metric("Municipios", perfil['n_municipios'])
                st.metric("Deptos", perfil['n_departamentos'])
                if perfil['top1_depto'] is not None:
                    st.metric(
                        f"Principal: {perfil['top1_depto']['Departamento']}",
                        f"{perfil['top1_depto']['Porcentaje']:.1f}%"
                    )

    st.markdown("---")

    # =========================================================================
    # HEATMAP UNIDAD × DEPARTAMENTO
    # =========================================================================

    st.subheader("Mapa de Calor: Distribución Geográfica por Unidad")

    fig_heatmap = crear_heatmap_unidad_depto(df_procedencia, unidades_seleccionadas)
    st.plotly_chart(fig_heatmap, use_container_width=True)

    st.caption("""
    **Interpretación:** Cada columna representa una unidad y suma 100%.
    Los colores más intensos indican mayor proporción de pacientes de ese departamento.
    """)

    st.markdown("---")

    # =========================================================================
    # GRÁFICO RADAR COMPARATIVO
    # =========================================================================

    if len(unidades_seleccionadas) >= 2:
        st.subheader("Perfil Comparativo de Procedencia")

        fig_radar = crear_radar_comparativo(df_procedencia, unidades_seleccionadas)
        st.plotly_chart(fig_radar, use_container_width=True)

        st.caption("""
        **Interpretación:** Cada línea representa una unidad. Las puntas del radar
        muestran el porcentaje de pacientes de cada departamento principal.
        Perfiles similares indican cobertura territorial similar.
        """)

    st.markdown("---")

    # =========================================================================
    # TABLA COMPARATIVA DETALLADA
    # =========================================================================

    st.subheader("Tabla Comparativa: Top Departamentos por Unidad")

    # Crear tabla pivoteada
    df_filtrado = df_procedencia[df_procedencia['Unidad'].isin(unidades_seleccionadas)]
    tabla_pivot = df_filtrado.groupby(['Departamento', 'Unidad'])['Casos'].sum().reset_index()

    # Pivotar
    tabla_wide = tabla_pivot.pivot(index='Departamento', columns='Unidad', values='Casos').fillna(0)
    tabla_wide['Total'] = tabla_wide.sum(axis=1)
    tabla_wide = tabla_wide.sort_values('Total', ascending=False).head(15)

    # Renombrar columnas
    tabla_wide.columns = [c.replace(' Procedencia', '') if c != 'Total' else c for c in tabla_wide.columns]

    # Formatear números
    for col in tabla_wide.columns:
        tabla_wide[col] = tabla_wide[col].apply(lambda x: format_large_number(int(x)))

    tabla_wide = tabla_wide.reset_index()
    tabla_wide.insert(0, '#', range(1, len(tabla_wide) + 1))

    st.dataframe(
        tabla_wide,
        use_container_width=True,
        hide_index=True,
        height=450
    )

    st.markdown("---")

    # =========================================================================
    # ANÁLISIS DE CONCENTRACIÓN
    # =========================================================================

    st.subheader("Índice de Concentración Geográfica")

    st.markdown("""
    La concentración geográfica mide qué tan dispersos o concentrados están los
    pacientes de cada unidad. Un valor alto indica que la mayoría viene de pocos lugares.
    """)

    # Calcular índice de concentración (top 3 departamentos)
    concentracion_data = []
    for unidad, perfil in perfiles.items():
        if perfil:
            concentracion_data.append({
                'Unidad': unidad.replace(' Procedencia', ''),
                'Top 3 Deptos (%)': perfil['top3_pct'],
                'Top 5 Deptos (%)': perfil['top5_pct'],
                'Municipios Únicos': perfil['n_municipios']
            })

    df_concentracion = pd.DataFrame(concentracion_data)
    df_concentracion = df_concentracion.sort_values('Top 3 Deptos (%)', ascending=False)

    col_tabla, col_grafico = st.columns([1, 1])

    with col_tabla:
        st.dataframe(
            df_concentracion,
            use_container_width=True,
            hide_index=True
        )

    with col_grafico:
        fig_conc = px.bar(
            df_concentracion.sort_values('Top 3 Deptos (%)', ascending=True),
            x='Top 3 Deptos (%)',
            y='Unidad',
            orientation='h',
            title='Concentración en Top 3 Departamentos',
            color='Top 3 Deptos (%)',
            color_continuous_scale='Blues'
        )
        fig_conc.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig_conc, use_container_width=True)

    # =========================================================================
    # INFORMACIÓN
    # =========================================================================

    st.markdown("---")
    with st.expander("Información sobre el Análisis Cruzado"):
        st.markdown("""
        ### Propósito del Análisis

        Este módulo permite **comparar el perfil geográfico** de los pacientes
        atendidos en cada unidad del IGSS Escuintla.

        **Preguntas que responde:**
        - ¿De dónde vienen los pacientes de cada unidad?
        - ¿Qué unidades tienen cobertura territorial similar?
        - ¿Qué tan concentrada o dispersa es la procedencia de cada unidad?
        - ¿Hay departamentos que envían pacientes a múltiples unidades?

        **Indicadores clave:**
        - **Concentración Top 3:** Porcentaje de pacientes de los 3 departamentos principales
        - **Municipios únicos:** Diversidad geográfica de la población atendida
        - **Perfil radar:** Comparación visual del origen de pacientes

        **Uso práctico:**
        - Planificación de recursos según demanda geográfica
        - Identificación de áreas de influencia de cada unidad
        - Detección de solapamiento o vacíos de cobertura
        - Evaluación del alcance territorial del IGSS en la región
        """)
