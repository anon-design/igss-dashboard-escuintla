"""
Módulo para gestión de paleta de colores IGSS y funciones de visualización
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from config import COLORS, PLOTLY_TEMPLATE


def get_color_scale(n_colors, palette='categorical'):
    """
    Obtiene una escala de colores para n elementos.

    Args:
        n_colors (int): Número de colores necesarios
        palette (str): Tipo de paleta ('categorical', 'blue_scale', 'green_scale')

    Returns:
        list: Lista de colores en formato hexadecimal
    """
    if palette == 'blue_scale':
        base_colors = COLORS['blue_scale']
    elif palette == 'green_scale':
        base_colors = COLORS['green_scale']
    else:
        base_colors = COLORS['categorical']

    # Si necesitamos más colores de los disponibles, repetir la paleta
    if n_colors <= len(base_colors):
        return base_colors[:n_colors]
    else:
        # Repetir colores si se necesitan más
        repeated = (base_colors * ((n_colors // len(base_colors)) + 1))
        return repeated[:n_colors]


def get_semantic_color(type='info'):
    """
    Obtiene un color semántico según el tipo.

    Args:
        type (str): Tipo de color ('info', 'success', 'warning', 'danger')

    Returns:
        str: Color en formato hexadecimal
    """
    semantic_map = {
        'info': COLORS['info'],
        'success': COLORS['success'],
        'warning': COLORS['warning'],
        'danger': COLORS['danger'],
        'primary': COLORS['primary'],
        'secondary': COLORS['secondary']
    }

    return semantic_map.get(type, COLORS['primary'])


def create_bar_chart(df, x, y, title='', orientation='v', color=None):
    """
    Crea un gráfico de barras con estilo IGSS.

    Args:
        df (pd.DataFrame): DataFrame con datos
        x (str): Columna para eje X
        y (str): Columna para eje Y
        title (str): Título del gráfico
        orientation (str): Orientación ('v' vertical, 'h' horizontal)
        color (str): Columna para colorear (opcional)

    Returns:
        go.Figure: Figura de Plotly
    """
    if color:
        fig = px.bar(
            df,
            x=x,
            y=y,
            title=title,
            orientation=orientation,
            color=color,
            color_discrete_sequence=COLORS['categorical'],
        )
    else:
        fig = px.bar(
            df,
            x=x,
            y=y,
            title=title,
            orientation=orientation,
            color_discrete_sequence=[COLORS['primary']],
        )

    # Etiquetas visibles siempre (por traza, soporta múltiples colores)
    if orientation == 'h':
        for trace in fig.data:
            vals = trace.x
            def fmt(v):
                try:
                    return f"{v:,.0f}" if v is not None and pd.notna(v) else ""
                except (TypeError, ValueError):
                    return ""
            text_vals = [fmt(v) for v in vals]
            trace.update(text=text_vals, texttemplate='%{text}', textposition='outside', cliponaxis=False)
        fig.update_layout(xaxis_tickformat=',')
    else:
        for trace in fig.data:
            vals = trace.y
            def fmt(v):
                try:
                    return f"{v:,.0f}" if v is not None and pd.notna(v) else ""
                except (TypeError, ValueError):
                    return ""
            text_vals = [fmt(v) for v in vals]
            trace.update(text=text_vals, texttemplate='%{text}', textposition='outside', cliponaxis=False)
        fig.update_layout(yaxis_tickformat=',')

    fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide', margin=dict(r=40))

    return apply_igss_theme(fig)


def create_line_chart(df, x, y, title='', color=None):
    """
    Crea un gráfico de líneas con estilo IGSS.

    Args:
        df (pd.DataFrame): DataFrame con datos
        x (str): Columna para eje X
        y (str): Columna para eje Y
        title (str): Título del gráfico
        color (str): Columna para colorear (opcional)

    Returns:
        go.Figure: Figura de Plotly
    """
    if color:
        fig = px.line(
            df,
            x=x,
            y=y,
            title=title,
            color=color,
            color_discrete_sequence=COLORS['categorical'],
        )
    else:
        fig = px.line(
            df,
            x=x,
            y=y,
            title=title,
            color_discrete_sequence=[COLORS['primary']],
        )

    # Líneas con puntos y etiquetas visibles
    for trace in fig.data:
        vals = trace.y
        def fmt(v):
            try:
                return f"{v:,.0f}" if v is not None and pd.notna(v) else ""
            except (TypeError, ValueError):
                return ""
        text_vals = [fmt(v) for v in vals]
        trace.update(
            line=dict(width=3),
            mode='lines+markers+text',
            text=text_vals,
            texttemplate='%{text}',
            textposition='top center'
        )
    fig.update_layout(yaxis_tickformat=',', uniformtext_minsize=8, uniformtext_mode='hide')

    return apply_igss_theme(fig)


def create_pie_chart(df, values, names, title=''):
    """
    Crea un gráfico circular con estilo IGSS.

    Args:
        df (pd.DataFrame): DataFrame con datos
        values (str): Columna con valores
        names (str): Columna con nombres
        title (str): Título del gráfico

    Returns:
        go.Figure: Figura de Plotly
    """
    fig = px.pie(
        df,
        values=values,
        names=names,
        title=title,
        color_discrete_sequence=COLORS['categorical']
    )

    # Mostrar porcentaje y número absoluto
    fig.update_traces(textposition='inside', textinfo='label+percent+value')

    return apply_igss_theme(fig)


def create_heatmap(df, title=''):
    """
    Crea un mapa de calor con estilo IGSS.

    Args:
        df (pd.DataFrame): DataFrame con datos (matriz)
        title (str): Título del gráfico

    Returns:
        go.Figure: Figura de Plotly
    """
    fig = go.Figure(data=go.Heatmap(
        z=df.values,
        x=df.columns,
        y=df.index,
        colorscale='Blues',
        hoverongaps=False
    ))

    fig.update_layout(title=title)

    return apply_igss_theme(fig)


def create_stacked_bar(df, x, y, title='', color=None):
    """
    Crea un gráfico de barras apiladas con estilo IGSS.

    Args:
        df (pd.DataFrame): DataFrame con datos
        x (str): Columna para eje X
        y (str): Columna para eje Y
        title (str): Título del gráfico
        color (str): Columna para apilar

    Returns:
        go.Figure: Figura de Plotly
    """
    fig = px.bar(
        df,
        x=x,
        y=y,
        title=title,
        color=color,
        barmode='stack',
        color_discrete_sequence=COLORS['categorical']
    )

    # Textos sin NaN por traza
    for trace in fig.data:
        vals = trace.y
        def fmt(v):
            try:
                return f"{v:,.0f}" if v is not None and pd.notna(v) else ""
            except (TypeError, ValueError):
                return ""
        text_vals = [fmt(v) for v in vals]
        trace.update(
            text=text_vals,
            texttemplate='%{text}',
            textposition='inside',
            insidetextanchor='middle'
        )
    fig.update_layout(yaxis_tickformat=',', uniformtext_minsize=8, uniformtext_mode='hide')

    return apply_igss_theme(fig)


def format_large_number(n):
    """
    Formatea números grandes con separadores de miles.

    Args:
        n (int/float): Número a formatear

    Returns:
        str: Número formateado
    """
    return f"{n:,.0f}"


def create_metric_card_html(title, value, delta=None, color='primary'):
    """
    Crea HTML para una tarjeta de métrica adaptable a modo claro/oscuro.

    Args:
        title (str): Título de la métrica
        value (str/int): Valor principal
        delta (str): Cambio/delta (opcional)
        color (str): Color de la tarjeta

    Returns:
        str: HTML de la tarjeta
    """
    bg_color = get_semantic_color(color)

    delta_html = ''
    if delta:
        delta_html = f'<div style="font-size: 14px; opacity: 0.7;">{delta}</div>'

    html = f"""
    <div style="
        background: linear-gradient(135deg, {bg_color}08 0%, {bg_color}18 100%);
        border-left: 4px solid {bg_color};
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    ">
        <div style="font-size: 14px; opacity: 0.8; font-weight: 500; margin-bottom: 8px;">{title}</div>
        <div style="font-size: 32px; color: {bg_color}; font-weight: bold; margin: 8px 0;">
            {format_large_number(value) if isinstance(value, (int, float)) else value}
        </div>
        {delta_html}
    </div>
    """

    return html


def apply_igss_theme(fig):
    """
    Aplica el tema IGSS a una figura de Plotly existente.

    Args:
        fig (go.Figure): Figura de Plotly

    Returns:
        go.Figure: Figura con tema aplicado
    """
    fig.update_layout(
        font=PLOTLY_TEMPLATE['layout']['font'],
        title_font=PLOTLY_TEMPLATE['layout']['title']['font'],
        paper_bgcolor=PLOTLY_TEMPLATE['layout']['paper_bgcolor'],
        plot_bgcolor=PLOTLY_TEMPLATE['layout']['plot_bgcolor'],
        hovermode=PLOTLY_TEMPLATE['layout']['hovermode'],
        colorway=PLOTLY_TEMPLATE['layout']['colorway']
    )

    return fig
