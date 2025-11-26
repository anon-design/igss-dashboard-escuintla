"""
Módulo para carga y caché de datos del Dashboard Epidemiológico IGSS
"""

import pandas as pd
import streamlit as st
from pathlib import Path
import sys

# Agregar el directorio padre al path para imports
sys.path.append(str(Path(__file__).parent.parent))

from config import DATA_FILE, CATALOGOS_DIR, PROCEDENCIA_FILE


def load_all_data(uploaded_file=None):
    """
    Carga todos los datos necesarios para la aplicación, aceptando un archivo opcional.
    """
    data = {
        'data': load_data(uploaded_file),
        'capitulos': load_cie10_capitulos(),
        'eno': load_cie10_eno(),
        'cronicas': load_cie10_cronicas(),
        'diagnosticos': load_diagnosticos_nombres()
    }
    return data


def load_data(uploaded_file=None):
    """
    Carga, limpia y reconstruye los datos para garantizar la consistencia jerárquica.
    Puede cargar datos desde el archivo por defecto o desde un archivo CSV subido por el usuario.

    LÓGICA DE CORRECCIÓN:
    1. Se confía en los datos de las unidades específicas como la fuente principal.
    2. 'Otros' se calcula como los casos en 'General Escuintla' que no están en las específicas.
    3. 'General Escuintla' se RECONSTRUYE como la suma de las unidades específicas + 'Otros'.
    Esto garantiza que el todo es igual a la suma de sus partes.
    """
    try:
        if uploaded_file is not None:
            st.info("Procesando archivo cargado...")
            df_raw = pd.read_csv(uploaded_file)
        else:
            df_raw = pd.read_csv(DATA_FILE)

        # 1. Limpieza inicial
        required_cols = ['CIE10', 'Unidad', 'Año', 'Sexo', 'Edad', 'Casos']
        if not all(col in df_raw.columns for col in required_cols):
            missing_cols = [col for col in required_cols if col not in df_raw.columns]
            st.error(f"Faltan columnas requeridas en el archivo: {', '.join(missing_cols)}")
            return pd.DataFrame()

        df_raw = df_raw[~df_raw['Unidad'].str.contains('Procedencia', case=False, na=False)]
        df_raw['Año'] = pd.to_numeric(df_raw['Año'], errors='coerce')
        df_raw.dropna(subset=['Año'], inplace=True)
        df_raw['Año'] = df_raw['Año'].astype(int)
        df_raw['Casos'] = pd.to_numeric(df_raw['Casos'], errors='coerce').fillna(0).astype(int)
        df_raw['CIE10'] = df_raw['CIE10'].astype(str).str.replace(r'[^A-Z0-9]', '', regex=True).str.upper()

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
        df_merged['Casos_Especificas'] = df_merged['Casos_Especificas'].fillna(0)
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
        st.error(f"No se encontró el archivo de datos por defecto: {DATA_FILE}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error al cargar o procesar los datos: {str(e)}")
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
def get_capitulo_mapping(_df_capitulos):
    """
    Pre-calcula el mapeo de TODOS los códigos CIE-10 posibles a sus capítulos.
    Esto se hace UNA SOLA VEZ y se cachea.

    Genera códigos del A00-Z99 (26 letras × 100 números = 2600 combinaciones base)

    Returns:
        dict: Mapeo {codigo: nombre_capitulo}
    """
    if _df_capitulos.empty:
        return {}

    mapeo = {}

    # Para cada capítulo, generar todos los códigos que pertenecen a él
    for _, row in _df_capitulos.iterrows():
        inicio = str(row['rango_inicio']).upper()
        fin = str(row['rango_fin']).upper()
        nombre = row['nombre']

        letra_inicio = inicio[0]
        letra_fin = fin[0]
        num_inicio = int(inicio[1:3]) if len(inicio) >= 3 else 0
        num_fin = int(fin[1:3]) if len(fin) >= 3 else 99

        # Iterar sobre las letras del rango
        for letra_ord in range(ord(letra_inicio), ord(letra_fin) + 1):
            letra = chr(letra_ord)

            # Determinar rango de números para esta letra
            if letra == letra_inicio and letra == letra_fin:
                start_num, end_num = num_inicio, num_fin
            elif letra == letra_inicio:
                start_num, end_num = num_inicio, 99
            elif letra == letra_fin:
                start_num, end_num = 0, num_fin
            else:
                start_num, end_num = 0, 99

            # Generar todos los códigos
            for num in range(start_num, end_num + 1):
                codigo_base = f"{letra}{num:02d}"
                mapeo[codigo_base] = nombre
                # También agregar variantes con sufijos comunes
                for sufijo in range(10):
                    mapeo[f"{codigo_base}{sufijo}"] = nombre

    return mapeo


def get_cie10_chapter_fast(cie10_code, mapeo_capitulos):
    """
    Versión RÁPIDA de get_cie10_chapter usando lookup directo.

    Args:
        cie10_code (str): Código CIE-10
        mapeo_capitulos (dict): Diccionario pre-calculado de mapeos

    Returns:
        str: Nombre del capítulo o "Sin clasificar"
    """
    if pd.isna(cie10_code) or cie10_code == '':
        return "Sin clasificar"

    codigo = str(cie10_code).strip().upper()

    # Intentar lookup directo
    if codigo in mapeo_capitulos:
        return mapeo_capitulos[codigo]

    # Intentar con solo los primeros 3 caracteres (base del código)
    if len(codigo) >= 3:
        codigo_base = codigo[:3]
        if codigo_base in mapeo_capitulos:
            return mapeo_capitulos[codigo_base]

    return "Sin clasificar"


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
    except (ValueError, IndexError):
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
        except (ValueError, IndexError):
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
            except ValueError:
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
    Carga el catálogo completo de nombres de diagnósticos, combinando el archivo
    principal de Excel con un archivo de parche (patch) para códigos faltantes.
    """
    df_main = pd.DataFrame()
    df_patch = pd.DataFrame()

    # 1. Cargar el archivo principal de Excel
    try:
        file_path = CATALOGOS_DIR / "diagnosticos_nombres.xlsx"
        sheet_name = 'ES2024 Completa + Marcadores'
        df_main = pd.read_excel(file_path, sheet_name=sheet_name, header=0)
        df_main = df_main[['Código', 'Descripción']].copy()
        df_main.columns = ['cie10', 'nombre']
    except FileNotFoundError:
        st.warning(f"Archivo principal de nombres no encontrado: {file_path}. Se usarán solo parches.")
    except Exception as e:
        st.error(f"Error al cargar el archivo Excel de diagnósticos: {e}")

    # 2. Cargar el archivo de parche CSV
    try:
        patch_path = CATALOGOS_DIR / "patch_nombres.csv"
        df_patch = pd.read_csv(patch_path)
        # Asegurarse que el parche tenga las columnas correctas
        if 'cie10' in df_patch.columns and 'nombre' in df_patch.columns:
            df_patch['cie10'] = df_patch['cie10'].astype(str).str.upper()
        else:
            st.warning(f"Archivo de parche {patch_path} no tiene el formato esperado (cie10, nombre).")
            df_patch = pd.DataFrame()
    except FileNotFoundError:
        # No es un error si el parche no existe
        pass
    except Exception as e:
        st.error(f"Error al cargar el archivo de parche de diagnósticos: {e}")

    # 3. Combinar ambos, dando prioridad al parche
    # Se coloca el parche primero y luego se eliminan duplicados manteniendo el primero.
    df_combined = pd.concat([df_patch, df_main], ignore_index=True)
    
    if df_combined.empty:
        st.error("No se pudo cargar ningún catálogo de nombres de diagnóstico.")
        return pd.DataFrame()

    # 4. Normalizar y limpiar
    df_combined.dropna(subset=['cie10', 'nombre'], inplace=True)
    df_combined['cie10'] = df_combined['cie10'].astype(str).str.replace(r'[^A-Z0-9]', '', regex=True).str.upper()
    df_combined = df_combined[~df_combined['cie10'].str.contains('-')]
    df_combined.drop_duplicates(subset=['cie10'], keep='first', inplace=True)

    return df_combined


@st.cache_data(ttl=3600)
def load_procedencia_data():
    """
    Carga los datos de procedencia geográfica.
    Estructura: CIE10 × Unidad × Año × Departamento × Municipio × Sexo × Edad → Casos

    Returns:
        pd.DataFrame: DataFrame con datos de procedencia geográfica
    """
    try:
        if not PROCEDENCIA_FILE.exists():
            st.error(f"No se encontró el archivo de procedencia: {PROCEDENCIA_FILE}")
            return None

        df = pd.read_csv(PROCEDENCIA_FILE, encoding='utf-8-sig')

        # Verificar columnas requeridas
        required_cols = ['CIE10', 'Unidad', 'Año', 'Departamento', 'Municipio', 'Sexo', 'Edad', 'Casos']
        if not all(col in df.columns for col in required_cols):
            missing_cols = [col for col in required_cols if col not in df.columns]
            st.error(f"Faltan columnas requeridas en el archivo de procedencia: {', '.join(missing_cols)}")
            return None

        # Convertir Año a int
        df['Año'] = pd.to_numeric(df['Año'], errors='coerce').astype('Int64')

        # Convertir Casos a int
        df['Casos'] = pd.to_numeric(df['Casos'], errors='coerce').fillna(0).astype(int)

        # Estandarizar columnas de texto
        for col in ['Departamento', 'Municipio', 'Sexo']:
            df[col] = df[col].str.strip().str.upper()

        # Limpiar código CIE10
        df['CIE10'] = df['CIE10'].astype(str).str.replace(r'[^A-Z0-9]', '', regex=True).str.upper()

        return df

    except FileNotFoundError:
        st.error(f"No se encontró el archivo de procedencia: {PROCEDENCIA_FILE}")
        return None
    except Exception as e:
        st.error(f"Error al cargar datos de procedencia: {str(e)}")
        return None


def get_procedencia_stats(df):
    """
    Retorna estadísticas básicas del dataset de procedencia.

    IMPORTANTE: Respeta la estructura jerárquica de los datos:
    - "General Escuintla Procedencia" = TOTAL COMPLETO (100% de casos)
    - Unidades específicas = SUBCONJUNTOS de General (NO sumar)
    - "Otros" = General - Suma(Específicas)

    Args:
        df (pd.DataFrame): DataFrame con datos de procedencia

    Returns:
        dict: Diccionario con estadísticas del dataset de procedencia
    """
    if df is None or df.empty:
        return {
            'total_registros': 0,
            'total_casos': 0,
            'total_casos_general': 0,
            'casos_especificas': 0,
            'casos_otros': 0,
            'años': [],
            'departamentos': 0,
            'municipios': 0,
            'unidades': 0,
            'codigos_cie10': 0
        }

    # Separar General de unidades específicas (estructura jerárquica)
    UNIDAD_GENERAL = 'General Escuintla Procedencia'
    df_general = df[df['Unidad'] == UNIDAD_GENERAL]
    df_especificas = df[df['Unidad'] != UNIDAD_GENERAL]

    # TOTAL REAL = solo General Escuintla Procedencia
    total_general = int(df_general['Casos'].sum())
    casos_especificas = int(df_especificas['Casos'].sum())
    casos_otros = total_general - casos_especificas  # No clasificados en unidades específicas

    return {
        'total_registros': len(df),
        'total_casos': total_general,  # CORRECTO: Solo General (no suma de todas)
        'total_casos_general': total_general,
        'casos_especificas': casos_especificas,
        'casos_otros': casos_otros,
        'pct_especificas': round(casos_especificas / total_general * 100, 2) if total_general > 0 else 0,
        'pct_otros': round(casos_otros / total_general * 100, 2) if total_general > 0 else 0,
        'años': sorted(df['Año'].dropna().unique().tolist()),
        'departamentos': df['Departamento'].nunique(),
        'municipios': df['Municipio'].nunique(),
        'unidades': df['Unidad'].nunique(),
        'codigos_cie10': df['CIE10'].nunique(),
        'año_min': int(df['Año'].min()) if not df['Año'].isna().all() else None,
        'año_max': int(df['Año'].max()) if not df['Año'].isna().all() else None,
        # Casos por año - SOLO de General para evitar duplicación
        'casos_por_año': df_general.groupby('Año')['Casos'].sum().to_dict() if not df_general['Año'].isna().all() else {}
    }
