"""
Módulo de Diagramas Sankey - Flujos de Pacientes
Visualización del flujo: Municipio de Procedencia → Unidad de Atención

Este módulo permite analizar de dónde vienen los pacientes y dónde son atendidos,
mostrando los flujos principales entre municipios de origen y unidades médicas.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from config import COLORS
from utils.filters import UNIDAD_GENERAL_PROCEDENCIA
from utils.colors import create_metric_card_html, format_large_number


def get_unidades_especificas_procedencia(df):
    """Obtiene lista de unidades específicas (excluye General)"""
    todas = df['Unidad'].unique().tolist()
    return [u for u in todas if u != UNIDAD_GENERAL_PROCEDENCIA]


def preparar_datos_sankey(df, top_municipios=15, top_unidades=None):
    """
    Prepara datos para el diagrama Sankey

    Args:
        df: DataFrame con datos de procedencia
        top_municipios: Número de municipios principales a mostrar
        top_unidades: Lista de unidades a incluir (None = todas las específicas)

    Returns:
        dict con source, target, value, labels, colors
    """
    # Solo unidades específicas (no General)
    unidades_especificas = get_unidades_especificas_procedencia(df)

    if top_unidades:
        unidades_especificas = [u for u in unidades_especificas if u in top_unidades]

    df_especificas = df[df['Unidad'].isin(unidades_especificas)].copy()

    if df_especificas.empty:
        return None

    # Agrupar por Municipio y Unidad
    flujos = df_especificas.groupby(['Municipio', 'Unidad'])['Casos'].sum().reset_index()

    # Top municipios por total de casos
    top_munis = flujos.groupby('Municipio')['Casos'].sum().nlargest(top_municipios).index.tolist()

    # Filtrar solo top municipios
    flujos = flujos[flujos['Municipio'].isin(top_munis)]

    # Crear listas de nodos únicos
    municipios = flujos['Municipio'].unique().tolist()
    unidades = flujos['Unidad'].unique().tolist()

    # Mapear a índices
    # Municipios: 0 a len(municipios)-1
    # Unidades: len(municipios) a len(municipios)+len(unidades)-1
    muni_to_idx = {m: i for i, m in enumerate(municipios)}
    unidad_to_idx = {u: i + len(municipios) for i, u in enumerate(unidades)}

    # Crear listas para Sankey
    sources = []
    targets = []
    values = []

    for _, row in flujos.iterrows():
        sources.append(muni_to_idx[row['Municipio']])
        targets.append(unidad_to_idx[row['Unidad']])
        values.append(row['Casos'])

    # Etiquetas de nodos
    labels = municipios + [u.replace(' Procedencia', '') for u in unidades]

    # Colores
    # Municipios en escala de azules, Unidades en escala de verdes
    node_colors = (
        [COLORS['blue_scale'][2]] * len(municipios) +
        [COLORS['green_scale'][3]] * len(unidades)
    )

    # Color de enlaces (transparente basado en el nodo origen)
    link_colors = ['rgba(0, 102, 168, 0.3)'] * len(sources)

    return {
        'sources': sources,
        'targets': targets,
        'values': values,
        'labels': labels,
        'node_colors': node_colors,
        'link_colors': link_colors,
        'municipios': municipios,
        'unidades': unidades
    }


def crear_sankey(datos_sankey, titulo="Flujo de Pacientes: Municipio → Unidad"):
    """
    Crea el diagrama Sankey con Plotly
    """
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=datos_sankey['labels'],
            color=datos_sankey['node_colors'],
            hovertemplate='%{label}<br>%{value:,.0f} casos<extra></extra>'
        ),
        link=dict(
            source=datos_sankey['sources'],
            target=datos_sankey['targets'],
            value=datos_sankey['values'],
            color=datos_sankey['link_colors'],
            hovertemplate='%{source.label} → %{target.label}<br>%{value:,.0f} casos<extra></extra>'
        )
    )])

    fig.update_layout(
        title=dict(
            text=titulo,
            font=dict(size=18, color=COLORS['primary'])
        ),
        font=dict(size=12),
        height=600,
        paper_bgcolor='white',
        plot_bgcolor='white'
    )

    return fig


def render(df_procedencia):
    """
    Renderiza el módulo de diagramas Sankey de flujos de pacientes

    Args:
        df_procedencia: DataFrame con datos de procedencia (todas las unidades)
    """
    st.title("Flujos de Pacientes: Sankey")
    st.markdown("### Visualización del flujo desde municipios de origen hacia unidades de atención")

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
    # CONTROLES DE FILTRO
    # =========================================================================

    st.subheader("Configuración del Diagrama")

    col_f1, col_f2, col_f3 = st.columns(3)

    with col_f1:
        top_n = st.slider(
            "Municipios principales a mostrar:",
            min_value=5,
            max_value=30,
            value=15,
            step=5,
            key="sankey_top_n"
        )

    with col_f2:
        # Filtro de departamento para los municipios
        departamentos = sorted(df_procedencia['Departamento'].unique().tolist())
        filtro_depto = st.multiselect(
            "Filtrar por departamento de origen:",
            options=departamentos,
            default=[],
            key="sankey_depto"
        )

    with col_f3:
        # Filtro de unidades a incluir
        unidades_opciones = [u.replace(' Procedencia', '') for u in unidades_especificas]
        unidades_seleccionadas = st.multiselect(
            "Unidades a incluir:",
            options=unidades_opciones,
            default=unidades_opciones,
            key="sankey_unidades"
        )

    # Mapear de vuelta a nombres completos
    unidades_filtradas = [f"{u} Procedencia" for u in unidades_seleccionadas] if unidades_seleccionadas else None

    # Aplicar filtro de departamento
    df_filtrado = df_procedencia.copy()
    if filtro_depto:
        df_filtrado = df_filtrado[df_filtrado['Departamento'].isin(filtro_depto)]

    st.markdown("---")

    # =========================================================================
    # MÉTRICAS RESUMEN
    # =========================================================================

    df_especificas = df_filtrado[df_filtrado['Unidad'].isin(unidades_especificas)]

    if df_especificas.empty:
        st.warning("No hay datos con los filtros seleccionados.")
        return

    total_casos = df_especificas['Casos'].sum()
    total_municipios = df_especificas['Municipio'].nunique()
    total_unidades = df_especificas['Unidad'].nunique()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            create_metric_card_html("Casos en Flujo", format_large_number(int(total_casos)), color='primary'),
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            create_metric_card_html("Municipios Origen", total_municipios, color='info'),
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            create_metric_card_html("Unidades Destino", total_unidades, color='success'),
            unsafe_allow_html=True
        )

    st.markdown("---")

    # =========================================================================
    # DIAGRAMA SANKEY PRINCIPAL
    # =========================================================================

    st.subheader("Diagrama de Flujo Sankey")

    datos_sankey = preparar_datos_sankey(
        df_filtrado,
        top_municipios=top_n,
        top_unidades=unidades_filtradas
    )

    if datos_sankey:
        titulo = "Flujo de Pacientes: Municipio de Procedencia → Unidad de Atención"
        if filtro_depto:
            titulo += f" ({', '.join(filtro_depto[:2])}{'...' if len(filtro_depto) > 2 else ''})"

        fig_sankey = crear_sankey(datos_sankey, titulo)
        st.plotly_chart(fig_sankey, width='stretch')

        st.caption(f"""
        **Cómo leer este diagrama:**
        - **Izquierda (azul):** Top {len(datos_sankey['municipios'])} municipios de donde provienen los pacientes
        - **Derecha (verde):** Unidades del IGSS donde fueron atendidos
        - **Grosor de las líneas:** Proporción de pacientes en ese flujo
        - Pase el cursor sobre las líneas para ver el número exacto de casos
        """)
    else:
        st.warning("No hay suficientes datos para generar el diagrama Sankey.")

    st.markdown("---")

    # =========================================================================
    # TABLA DE FLUJOS PRINCIPALES
    # =========================================================================

    st.subheader("Top Flujos Municipio → Unidad")

    # Crear tabla de flujos principales
    flujos_tabla = df_especificas.groupby(['Municipio', 'Departamento', 'Unidad'])['Casos'].sum().reset_index()
    flujos_tabla = flujos_tabla.sort_values('Casos', ascending=False).head(20)
    flujos_tabla['Unidad_corta'] = flujos_tabla['Unidad'].str.replace(' Procedencia', '')
    flujos_tabla['Rank'] = range(1, len(flujos_tabla) + 1)
    flujos_tabla['Casos_fmt'] = flujos_tabla['Casos'].apply(format_large_number)

    st.dataframe(
        flujos_tabla[['Rank', 'Municipio', 'Departamento', 'Unidad_corta', 'Casos_fmt']].rename(
            columns={
                'Rank': '#',
                'Unidad_corta': 'Unidad',
                'Casos_fmt': 'Casos'
            }
        ),
        width='stretch',
        hide_index=True,
        height=500
    )

    # =========================================================================
    # INFORMACIÓN
    # =========================================================================

    st.markdown("---")
    with st.expander("Información sobre el Diagrama Sankey"):
        st.markdown("""
        ### Interpretación del Diagrama

        El **diagrama Sankey** muestra el flujo de pacientes desde su municipio de
        procedencia hacia la unidad del IGSS donde fueron atendidos.

        **Elementos del diagrama:**
        - **Nodos izquierdos (azules):** Municipios de donde provienen los pacientes
        - **Nodos derechos (verdes):** Unidades médicas del IGSS Escuintla
        - **Enlaces (líneas):** Flujo de pacientes entre origen y destino
        - **Grosor del enlace:** Proporcional al número de casos

        **Uso analítico:**
        - Identificar las principales rutas de referencia de pacientes
        - Detectar unidades que reciben pacientes de municipios lejanos
        - Planificar la distribución de recursos según demanda geográfica
        - Evaluar la cobertura territorial de cada unidad

        **Nota:** Solo se muestran las unidades específicas. El "General Escuintla Procedencia"
        representa el total y no se incluye en los flujos para evitar duplicación.
        """)
