"""
Módulo para carga y caché de datos del Dashboard Epidemiológico IGSS
"""

import pandas as pd
import streamlit as st
from pathlib import Path
import sys

# Agregar el directorio padre al path para imports
sys.path.append(str(Path(__file__).parent.parent))

from config import DATA_FILE, CATALOGOS_DIR


@st.cache_data(ttl=3600)
def load_data():
    """
    Carga, limpia y reconstruye los datos para garantizar la consistencia jerárquica.

    LÓGICA DE CORRECCIÓN:
    1. Se confía en los datos de las unidades específicas como la fuente principal.
    2. 'Otros' se calcula como los casos en 'General Escuintla' que no están en las específicas.
    3. 'General Escuintla' se RECONSTRUYE como la suma de las unidades específicas + 'Otros'.
    Esto garantiza que el todo es igual a la suma de sus partes.
    """
    try:
        df_raw = pd.read_csv(DATA_FILE)

        # 1. Limpieza inicial
        required_cols = ['CIE10', 'Unidad', 'Año', 'Sexo', 'Edad', 'Casos']
        if not all(col in df_raw.columns for col in required_cols):
            missing_cols = [col for col in required_cols if col not in df_raw.columns]
            st.error(f"Faltan columnas requeridas: {', '.join(missing_cols)}")
            return pd.DataFrame()

        df_raw = df_raw[~df_raw['Unidad'].str.contains('Procedencia', case=False, na=False)]
        df_raw['Año'] = pd.to_numeric(df_raw['Año'], errors='coerce')
        df_raw.dropna(subset=['Año'], inplace=True)
        df_raw['Año'] = df_raw['Año'].astype(int)
        df_raw['Casos'] = pd.to_numeric(df_raw['Casos'], errors='coerce').fillna(0).astype(int)
        df_raw['CIE10'] = df_raw['CIE10'].astype(str).str.strip().str.upper()

        # 2. Separar las partes del "todo" original
        unidades_especificas_nombres = [
            'Hospital Escuintla', 'Hospital Santa Lucia Cotzumalguapa',
            'Consultorio Masagua', 'Consultorio la Democracia', 'Consultorio Siquinala'
        ]
        df_general_orig = df_raw[df_raw['Unidad'] == 'General Escuintla'].copy()
        df_especificas = df_raw[df_raw['Unidad'].isin(unidades_especificas_nombres)].copy()

        # 3. Calcular 'Otros'
        group_cols = ['CIE10', 'Año', 'Sexo', 'Edad']
        df_especificas_agrupadas = df_especificas.groupby(group_cols, as_index=False)['Casos'].sum()
        
        df_merged = df_general_orig.merge(
            df_especificas_agrupadas.rename(columns={'Casos': 'Casos_Especificas'}),
            on=group_cols,
            how='left'
        )
        df_merged['Casos_Especificas'].fillna(0, inplace=True)
        df_merged['Casos_Otros'] = (df_merged['Casos'] - df_merged['Casos_Especificas']).clip(lower=0)

        df_otros = df_merged[df_merged['Casos_Otros'] > 0][group_cols + ['Casos_Otros']].copy()
        df_otros.rename(columns={'Casos_Otros': 'Casos'}, inplace=True)
        df_otros['Unidad'] = 'Otros'

        # 4. Combinar todas las partes verdaderas
        df_partes = pd.concat([df_especificas, df_otros], ignore_index=True)

        # 5. Reconstruir el "todo" ('General Escuintla')
        df_general_corregido = df_partes.groupby(group_cols, as_index=False)['Casos'].sum()
        df_general_corregido['Unidad'] = 'General Escuintla'

        # 6. Ensamblar el DataFrame final y consistente
        df_final = pd.concat([df_partes, df_general_corregido], ignore_index=True)

        return df_final

    except FileNotFoundError:
        st.error(f"No se encontró el archivo de datos: {DATA_FILE}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error al cargar los datos: {str(e)}")
        return pd.DataFrame()


@st.cache_data
def load_cie10_capitulos():
    """
    Carga el catálogo de capítulos CIE-10.

    Returns:
        pd.DataFrame: DataFrame con capítulos CIE-10
    """
    try:
        df = pd.read_csv(CATALOGOS_DIR / "cie10_capitulos.csv")
        return df
    except Exception as e:
        st.error(f"Error al cargar catálogo de capítulos: {str(e)}")
        return pd.DataFrame()


@st.cache_data
def load_cie10_eno():
    """
    Carga el catálogo de Enfermedades de Notificación Obligatoria (ENO).

    Returns:
        pd.DataFrame: DataFrame con ENO
    """
    try:
        df = pd.read_csv(CATALOGOS_DIR / "cie10_eno.csv")
        df['cie10'] = df['cie10'].astype(str).str.strip().str.upper()
        return df
    except Exception as e:
        st.error(f"Error al cargar catálogo ENO: {str(e)}")
        return pd.DataFrame()


@st.cache_data
def load_cie10_cronicas():
    """
    Carga el catálogo de Enfermedades Crónicas.

    Returns:
        pd.DataFrame: DataFrame con enfermedades crónicas
    """
    try:
        df = pd.read_csv(CATALOGOS_DIR / "cie10_cronicas.csv")
        df['cie10'] = df['cie10'].astype(str).str.strip().str.upper()
        return df
    except Exception as e:
        st.error(f"Error al cargar catálogo de crónicas: {str(e)}")
        return pd.DataFrame()


def get_cie10_chapter(cie10_code, df_capitulos):
    """
    Determina el capítulo CIE-10 para un código dado.

    Args:
        cie10_code (str): Código CIE-10
        df_capitulos (pd.DataFrame): DataFrame con capítulos CIE-10

    Returns:
        str: Nombre del capítulo o "Sin clasificar"
    """
    if pd.isna(cie10_code) or cie10_code == '':
        return "Sin clasificar"

    cie10_code = str(cie10_code).strip().upper()

    # Extraer letra y número del código
    if len(cie10_code) < 3:
        return "Sin clasificar"

    letra = cie10_code[0]
    try:
        numero = int(''.join([c for c in cie10_code[1:] if c.isdigit()][:2]))
    except:
        return "Sin clasificar"

    # Buscar en catálogo
    for _, row in df_capitulos.iterrows():
        inicio = row['rango_inicio']
        fin = row['rango_fin']

        # Extraer letra y número del rango
        letra_inicio = inicio[0]
        letra_fin = fin[0]

        try:
            num_inicio = int(''.join([c for c in inicio[1:] if c.isdigit()][:2]))
            num_fin = int(''.join([c for c in fin[1:] if c.isdigit()][:2]))
        except:
            continue

        # Verificar si el código está en el rango
        if letra_inicio <= letra <= letra_fin:
            if letra == letra_inicio and letra == letra_fin:
                if num_inicio <= numero <= num_fin:
                    return row['nombre']
            elif letra == letra_inicio:
                if numero >= num_inicio:
                    return row['nombre']
            elif letra == letra_fin:
                if numero <= num_fin:
                    return row['nombre']
            else:
                return row['nombre']

    return "Sin clasificar"


def is_eno(cie10_code, df_eno):
    """
    Verifica si un código CIE-10 es una Enfermedad de Notificación Obligatoria.

    Args:
        cie10_code (str): Código CIE-10
        df_eno (pd.DataFrame): DataFrame con ENO

    Returns:
        bool: True si es ENO, False en caso contrario
    """
    if pd.isna(cie10_code) or cie10_code == '':
        return False

    cie10_code = str(cie10_code).strip().upper()
    return cie10_code in df_eno['cie10'].values


def is_cronica(cie10_code, df_cronicas):
    """
    Verifica si un código CIE-10 es una Enfermedad Crónica.

    Args:
        cie10_code (str): Código CIE-10
        df_cronicas (pd.DataFrame): DataFrame con crónicas

    Returns:
        bool: True si es crónica, False en caso contrario
    """
    if pd.isna(cie10_code) or cie10_code == '':
        return False

    cie10_code = str(cie10_code).strip().upper()

    # Verificar código exacto
    if cie10_code in df_cronicas['cie10'].values:
        return True

    # Verificar rangos (ej: C00-C97 para cáncer)
    for cronica_code in df_cronicas['cie10'].values:
        if '-' in cronica_code:
            # Es un rango
            try:
                inicio, fin = cronica_code.split('-')
                if inicio <= cie10_code <= fin:
                    return True
            except:
                continue

    return False


def get_cie10_info(cie10_code, df_eno, df_cronicas):
    """
    Obtiene información completa de un código CIE-10.

    Args:
        cie10_code (str): Código CIE-10
        df_eno (pd.DataFrame): DataFrame con ENO
        df_cronicas (pd.DataFrame): DataFrame con crónicas

    Returns:
        dict: Diccionario con información del código
    """
    info = {
        'codigo': cie10_code,
        'es_eno': is_eno(cie10_code, df_eno),
        'es_cronica': is_cronica(cie10_code, df_cronicas),
        'nombre_eno': None,
        'categoria_eno': None,
        'nombre_cronica': None,
        'categoria_cronica': None
    }

    # Buscar en ENO
    if info['es_eno']:
        eno_row = df_eno[df_eno['cie10'] == cie10_code.upper()]
        if not eno_row.empty:
            info['nombre_eno'] = eno_row.iloc[0]['nombre']
            info['categoria_eno'] = eno_row.iloc[0]['categoria']

    # Buscar en crónicas
    if info['es_cronica']:
        cronica_row = df_cronicas[df_cronicas['cie10'] == cie10_code.upper()]
        if not cronica_row.empty:
            info['nombre_cronica'] = cronica_row.iloc[0]['nombre']
            info['categoria_cronica'] = cronica_row.iloc[0]['categoria']

    return info


def get_data_summary(df):
    """
    Obtiene un resumen de los datos cargados.

    Args:
        df (pd.DataFrame): DataFrame con datos

    Returns:
        dict: Diccionario con estadísticas del dataset
    """
    if df.empty:
        return {
            'total_registros': 0,
            'total_casos': 0,
            'años': [],
            'unidades': [],
            'codigos_unicos': 0
        }

    return {
        'total_registros': len(df),
        'total_casos': int(df['Casos'].sum()),
        'años': sorted(df['Año'].unique().tolist()),
        'unidades': sorted(df['Unidad'].unique().tolist()),
        'codigos_unicos': df['CIE10'].nunique(),
        'año_min': int(df['Año'].min()),
        'año_max': int(df['Año'].max()),
        'casos_por_año': df.groupby('Año')['Casos'].sum().to_dict()
    }


@st.cache_data
def load_diagnosticos_nombres():
    """
    Carga el catálogo completo de nombres de diagnósticos desde el archivo Excel.
    """
    try:
        file_path = CATALOGOS_DIR / "diagnosticos_nombres.xlsx"
        sheet_name = 'ES2024 Completa + Marcadores'
        
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=0)
        
        # Seleccionar y renombrar columnas
        df = df[['Código', 'Descripción']].copy()
        df.columns = ['cie10', 'nombre']
        
        # Normalizar códigos CIE-10 (eliminar puntos y otros caracteres)
        df['cie10'] = df['cie10'].astype(str).str.replace(r'[^A-Z0-9]', '', regex=True)
        
        # Eliminar filas donde el código es un capítulo (ej. A00-A09)
        df = df[~df['cie10'].str.contains('-')]
        
        df.dropna(subset=['cie10', 'nombre'], inplace=True)
        df.drop_duplicates(subset=['cie10'], inplace=True)
        
        return df

    except FileNotFoundError:
        st.error(f"No se encontró el archivo de nombres de diagnósticos: {file_path}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error al cargar nombres de diagnósticos: {str(e)}")
        return pd.DataFrame()
