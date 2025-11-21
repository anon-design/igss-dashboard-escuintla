"""
Módulo con funciones de filtrado para el Dashboard Epidemiológico IGSS
"""

import pandas as pd
import streamlit as st


def apply_filters(df, unidades=None, años=None, sexos=None, edades=None):
    """
    Aplica filtros múltiples al DataFrame.

    Args:
        df (pd.DataFrame): DataFrame a filtrar
        unidades (list): Lista de unidades a incluir (None = todas)
        años (list): Lista de años a incluir (None = todos)
        sexos (list): Lista de sexos a incluir (None = todos)
        edades (list): Lista de rangos de edad a incluir (None = todas)

    Returns:
        pd.DataFrame: DataFrame filtrado
    """
    df_filtered = df.copy()

    if unidades and len(unidades) > 0:
        df_filtered = df_filtered[df_filtered['Unidad'].isin(unidades)]

    if años and len(años) > 0:
        df_filtered = df_filtered[df_filtered['Año'].isin(años)]

    if sexos and len(sexos) > 0:
        df_filtered = df_filtered[df_filtered['Sexo'].isin(sexos)]

    if edades and len(edades) > 0:
        df_filtered = df_filtered[df_filtered['Edad'].isin(edades)]

    return df_filtered


def filter_by_age_group(df, pediatrico=False):
    """
    Filtra datos por grupo de edad (pediátrico o adultos).

    Args:
        df (pd.DataFrame): DataFrame a filtrar
        pediatrico (bool): True para pediátrico (0-15), False para adultos (>15)

    Returns:
        pd.DataFrame: DataFrame filtrado
    """
    if pediatrico:
        return df[df['Edad'] == '0-15'].copy()
    else:
        return df[df['Edad'] != '0-15'].copy()


def filter_by_cie10_codes(df, codigos):
    """
    Filtra datos por una lista de códigos CIE-10.

    Args:
        df (pd.DataFrame): DataFrame a filtrar
        codigos (list): Lista de códigos CIE-10

    Returns:
        pd.DataFrame: DataFrame filtrado
    """
    if not codigos or len(codigos) == 0:
        return df

    codigos_upper = [str(c).strip().upper() for c in codigos]
    return df[df['CIE10'].isin(codigos_upper)].copy()


def get_top_n(df, n=25, group_by='CIE10'):
    """
    Obtiene los top N registros más frecuentes.

    Args:
        df (pd.DataFrame): DataFrame con datos
        n (int): Número de elementos en el top
        group_by (str): Columna por la cual agrupar ('CIE10', 'Unidad', etc.)

    Returns:
        pd.DataFrame: DataFrame con top N
    """
    if df.empty:
        return pd.DataFrame()

    top = df.groupby(group_by)['Casos'].sum().nlargest(n).reset_index()
    top['Rank'] = range(1, len(top) + 1)

    return top


def aggregate_by_period(df, period='Año'):
    """
    Agrega datos por período de tiempo.

    Args:
        df (pd.DataFrame): DataFrame con datos
        period (str): Período de agregación ('Año', 'Mes', etc.)

    Returns:
        pd.DataFrame: DataFrame agregado
    """
    if df.empty:
        return pd.DataFrame()

    if period == 'Año':
        return df.groupby('Año')['Casos'].sum().reset_index()

    return df


def get_percentage_distribution(df, column):
    """
    Calcula la distribución porcentual de una columna.

    Args:
        df (pd.DataFrame): DataFrame con datos
        column (str): Columna para calcular distribución

    Returns:
        pd.DataFrame: DataFrame con valores y porcentajes
    """
    if df.empty:
        return pd.DataFrame()

    total = df['Casos'].sum()

    if total == 0:
        return pd.DataFrame()

    dist = df.groupby(column)['Casos'].sum().reset_index()
    dist['Porcentaje'] = (dist['Casos'] / total * 100).round(2)
    dist = dist.sort_values('Casos', ascending=False)

    return dist


def filter_by_time_range(df, año_inicio, año_fin):
    """
    Filtra datos por rango de años.

    Args:
        df (pd.DataFrame): DataFrame a filtrar
        año_inicio (int): Año de inicio
        año_fin (int): Año final

    Returns:
        pd.DataFrame: DataFrame filtrado
    """
    return df[(df['Año'] >= año_inicio) & (df['Año'] <= año_fin)].copy()


def create_crosstab(df, index_col, columns_col, values_col='Casos', aggfunc='sum'):
    """
    Crea una tabla cruzada (pivot table).

    Args:
        df (pd.DataFrame): DataFrame con datos
        index_col (str): Columna para índice (filas)
        columns_col (str): Columna para columnas
        values_col (str): Columna con valores
        aggfunc (str): Función de agregación

    Returns:
        pd.DataFrame: Tabla cruzada
    """
    if df.empty:
        return pd.DataFrame()

    return pd.crosstab(
        index=df[index_col],
        columns=df[columns_col],
        values=df[values_col],
        aggfunc=aggfunc
    ).fillna(0)


def compare_periods(df, period1, period2, group_by='CIE10'):
    """
    Compara dos períodos de tiempo.

    Args:
        df (pd.DataFrame): DataFrame con datos
        period1 (list): Lista de años del período 1
        period2 (list): Lista de años del período 2
        group_by (str): Columna por la cual agrupar

    Returns:
        pd.DataFrame: DataFrame con comparación
    """
    if df.empty:
        return pd.DataFrame()

    df1 = df[df['Año'].isin(period1)].groupby(group_by)['Casos'].sum()
    df2 = df[df['Año'].isin(period2)].groupby(group_by)['Casos'].sum()

    comparison = pd.DataFrame({
        'Periodo_1': df1,
        'Periodo_2': df2
    }).fillna(0)

    comparison['Diferencia'] = comparison['Periodo_2'] - comparison['Periodo_1']
    comparison['Cambio_Porcentual'] = ((comparison['Periodo_2'] - comparison['Periodo_1']) / comparison['Periodo_1'] * 100).round(2)
    comparison = comparison.replace([float('inf'), -float('inf')], 0)

    return comparison.reset_index()


def search_diagnosis(df, search_term, df_eno=None, df_cronicas=None):
    """
    Busca diagnósticos por término de búsqueda.

    Args:
        df (pd.DataFrame): DataFrame con datos
        search_term (str): Término a buscar
        df_eno (pd.DataFrame): DataFrame con catálogo ENO (opcional)
        df_cronicas (pd.DataFrame): DataFrame con catálogo crónicas (opcional)

    Returns:
        pd.DataFrame: DataFrame con resultados de búsqueda
    """
    if df.empty or not search_term:
        return pd.DataFrame()

    search_term = search_term.upper().strip()

    # Buscar en códigos CIE-10
    results = df[df['CIE10'].str.contains(search_term, na=False)].copy()

    # Si hay catálogos, buscar también en nombres
    if df_eno is not None and not df_eno.empty:
        matching_codes = df_eno[
            df_eno['nombre'].str.contains(search_term, case=False, na=False)
        ]['cie10'].tolist()
        results = pd.concat([results, df[df['CIE10'].isin(matching_codes)]])

    if df_cronicas is not None and not df_cronicas.empty:
        matching_codes = df_cronicas[
            df_cronicas['nombre'].str.contains(search_term, case=False, na=False)
        ]['cie10'].tolist()
        results = pd.concat([results, df[df['CIE10'].isin(matching_codes)]])

    return results.drop_duplicates()


def get_summary_stats(df):
    """
    Calcula estadísticas resumen del DataFrame filtrado.

    Args:
        df (pd.DataFrame): DataFrame con datos

    Returns:
        dict: Diccionario con estadísticas
    """
    if df.empty:
        return {
            'total_casos': 0,
            'total_diagnosticos': 0,
            'años_cubiertos': 0,
            'unidades': 0
        }

    return {
        'total_casos': int(df['Casos'].sum()),
        'total_diagnosticos': int(df['CIE10'].nunique()),
        'años_cubiertos': len(df['Año'].unique()),
        'unidades': len(df['Unidad'].unique()),
        'casos_promedio_anual': int(df.groupby('Año')['Casos'].sum().mean()),
        'diagnostico_mas_frecuente': df.groupby('CIE10')['Casos'].sum().idxmax() if not df.empty else None
    }


# ============================================================================
# FUNCIONES DE FILTRADO JERÁRQUICO
# ============================================================================

def get_total_general(df):
    """
    Obtiene el total general de casos (solo "General Escuintla").

    IMPORTANTE: "General Escuintla" es el TOTAL de todos los casos.
    Las demás unidades son SUBCONJUNTOS de General, NO adicionales.

    Args:
        df (pd.DataFrame): DataFrame completo

    Returns:
        int: Total de casos en "General Escuintla"
    """
    if df.empty:
        return 0

    df_general = df[df['Unidad'] == 'General Escuintla']
    return int(df_general['Casos'].sum())


def get_unidades_especificas(df):
    """
    Obtiene la lista de unidades específicas (excluyendo "General Escuintla").

    Args:
        df (pd.DataFrame): DataFrame completo

    Returns:
        list: Lista de unidades específicas
    """
    if df.empty or 'Unidad' not in df.columns:
        return []

    unidades = sorted(df['Unidad'].unique().tolist())
    # Excluir "General Escuintla" y variantes
    unidades_especificas = [
        u for u in unidades
        if u not in ['General Escuintla'] and 'Procedencia' not in u
    ]
    return unidades_especificas


def apply_filters_jerarquicos(df, unidades_seleccionadas=None, años=None, sexos=None, edades=None):
    """
    Aplica filtros respetando la estructura jerárquica de los datos.

    ESTRUCTURA JERÁRQUICA:
    - "General Escuintla" = TOTAL (100% de casos)
    - Unidades específicas = SUBCONJUNTOS de General (NO adicionales)
    - "Otros" = Casos en General que NO están en unidades específicas (calculado automáticamente)

    IMPORTANTE: "Otros" ahora existe como valor en la columna 'Unidad' y se puede filtrar
    directamente como cualquier otra unidad, gracias a la función calcular_registros_otros()
    en data_loader.py.

    REGLAS:
    1. Si no hay selección de unidades: retorna "General Escuintla" (total)
    2. Si hay selección: retorna SOLO las unidades específicas seleccionadas (incluyendo "Otros")
    3. NUNCA mezcla "General Escuintla" con unidades específicas

    Args:
        df (pd.DataFrame): DataFrame completo (incluye registros de "Otros")
        unidades_seleccionadas (list): Lista de unidades específicas a filtrar
        años (list): Lista de años a incluir (None = todos)
        sexos (list): Lista de sexos a incluir (None = todos)
        edades (list): Lista de rangos de edad a incluir (None = todas)

    Returns:
        pd.DataFrame: DataFrame filtrado jerárquicamente
    """
    if df.empty:
        return df

    # Si no hay selección de unidades, mostrar "General Escuintla"
    if not unidades_seleccionadas or len(unidades_seleccionadas) == 0:
        df_filtered = df[df['Unidad'] == 'General Escuintla'].copy()
    else:
        # Filtrar por unidades específicas seleccionadas
        # NUNCA incluir "General Escuintla" aquí
        # "Otros" ahora puede filtrarse directamente
        unidades_validas = [u for u in unidades_seleccionadas if u != 'General Escuintla']

        if unidades_validas:
            df_filtered = df[df['Unidad'].isin(unidades_validas)].copy()
        else:
            # Si solo se seleccionó "General Escuintla" (no debería pasar), mostrar General
            df_filtered = df[df['Unidad'] == 'General Escuintla'].copy()

    # Aplicar filtros adicionales (año, sexo, edad)
    if años and len(años) > 0:
        df_filtered = df_filtered[df_filtered['Año'].isin(años)]

    if sexos and len(sexos) > 0:
        df_filtered = df_filtered[df_filtered['Sexo'].isin(sexos)]

    if edades and len(edades) > 0:
        df_filtered = df_filtered[df_filtered['Edad'].isin(edades)]

    return df_filtered


def get_distribucion_unidades(df):
    """
    Obtiene la distribución de casos por todas las unidades (incluyendo 'Otros').
    'Otros' ya está pre-calculado en el DataFrame de entrada.

    Returns:
        pd.DataFrame: DataFrame con columnas:
            - Unidad: nombre de la unidad
            - Casos: total de casos
            - Porcentaje: % respecto al total general
    """
    if df.empty:
        return pd.DataFrame()

    total_general = get_total_general(df)
    if total_general == 0:
        return pd.DataFrame()

    # Agrupar por unidad para obtener los casos. Esto incluye 'Otros' automáticamente.
    df_dist = df[df['Unidad'] != 'General Escuintla'].groupby('Unidad', as_index=False)['Casos'].sum()
    
    # Calcular el porcentaje respecto al total general
    df_dist['Porcentaje'] = (df_dist['Casos'] / total_general * 100).round(2)
    
    # Ordenar por casos
    df_dist = df_dist.sort_values('Casos', ascending=False)
    
    return df_dist


def validar_seleccion_unidades(unidades_seleccionadas):
    """
    Valida que la selección de unidades sea correcta (no mezclar General con específicas).

    Args:
        unidades_seleccionadas (list): Lista de unidades seleccionadas

    Returns:
        tuple: (es_valida, mensaje_error)
    """
    if not unidades_seleccionadas or len(unidades_seleccionadas) == 0:
        return True, None

    # Verificar si se seleccionó "General Escuintla" junto con otras
    if 'General Escuintla' in unidades_seleccionadas and len(unidades_seleccionadas) > 1:
        return False, "⚠️ No se puede seleccionar 'General Escuintla' junto con otras unidades. 'General Escuintla' ya contiene todos los casos."

    return True, None
