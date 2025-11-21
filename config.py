"""
Configuración del Dashboard Epidemiológico IGSS Escuintla
"""

import os
from pathlib import Path

# ============================================================
# RUTAS Y ARCHIVOS
# ============================================================

# Directorio base del proyecto
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR.parent / "bases_limpias"
CACHE_DIR = BASE_DIR / "data" / "cache"
CATALOGOS_DIR = BASE_DIR / "catalogos"

# Archivo de datos consolidado SIN PROCEDENCIA
# IMPORTANTE: Usar Rangos_SIN_PROCEDENCIA.csv (excluye datos de Procedencia)
DATA_FILE = DATA_DIR / "Rangos_SIN_PROCEDENCIA.csv"
DATA_PATH = str(DATA_FILE)  # Alias como string para compatibilidad

# Asegurar que los directorios existen
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# PALETA DE COLORES IGSS GUATEMALA
# ============================================================

COLORS = {
    # Colores principales IGSS
    'primary': '#0066A8',      # Azul IGSS
    'secondary': '#00A651',    # Verde IGSS
    'accent': '#FF6B35',       # Naranja (acento)

    # Escala de azules (para gráficos)
    'blue_scale': [
        '#E6F2FA',  # Azul muy claro
        '#99CCE6',  # Azul claro
        '#4DA6D9',  # Azul medio
        '#0066A8',  # Azul principal
        '#004A7C',  # Azul oscuro
    ],

    # Escala de verdes (para gráficos)
    'green_scale': [
        '#E6F7EE',  # Verde muy claro
        '#99DEBF',  # Verde claro
        '#4DC590',  # Verde medio
        '#00A651',  # Verde principal
        '#007A3D',  # Verde oscuro
    ],

    # Colores para categorías
    'categorical': [
        '#0066A8',  # Azul IGSS
        '#00A651',  # Verde IGSS
        '#FF6B35',  # Naranja
        '#FFB84D',  # Amarillo/Dorado
        '#A85C00',  # Café
        '#6B00A8',  # Morado
        '#00A8A8',  # Turquesa
    ],

    # Colores semánticos
    'success': '#00A651',
    'warning': '#FFB84D',
    'danger': '#FF6B35',
    'info': '#0066A8',

    # Colores de texto y fondo
    'text': '#2C3E50',
    'background': '#FFFFFF',
    'background_alt': '#F8F9FA',
}

# ============================================================
# CONFIGURACIÓN DE VISUALIZACIONES
# ============================================================

# Configuración de Plotly
PLOTLY_CONFIG = {
    'displayModeBar': True,
    'displaylogo': False,
    'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
    'toImageButtonOptions': {
        'format': 'png',
        'filename': 'grafico_igss',
        'height': 600,
        'width': 1000,
        'scale': 2
    }
}

# Template de Plotly personalizado
PLOTLY_TEMPLATE = {
    'layout': {
        'font': {'family': 'Arial, sans-serif', 'color': COLORS['text']},
        'title': {'font': {'size': 18, 'color': COLORS['primary']}},
        'paper_bgcolor': COLORS['background'],
        'plot_bgcolor': COLORS['background_alt'],
        'colorway': COLORS['categorical'],
        'hovermode': 'closest',
        'hoverlabel': {
            'bgcolor': 'white',
            'font_size': 12,
            'font_family': 'Arial'
        }
    }
}

# ============================================================
# CONFIGURACIÓN DE DATOS
# ============================================================

# Unidades médicas disponibles
UNIDADES = [
    "General Escuintla",
    "Consultorio Masagua",
    "Consultorio la Democracia",
    "Hospital Santa Lucia Cotzumalguapa",
    "Hospital Escuintla",
    "Consultorio Siquinala",
]

# Rangos de edad disponibles
RANGOS_EDAD = [
    "0-15",
    "16-20",
    "21-25",
    "26-30",
    "31-35",
    "36-40",
    "41-45",
    "46-50",
    "51-55",
    "56-60",
    ">61"
]

# Años disponibles
AÑOS = list(range(2018, 2026))  # 2018-2025

# Sexos
SEXOS = ["FEMENINO", "MASCULINO", "NO ESPECIFICADO"]

# ============================================================
# CONFIGURACIÓN DE REPORTES
# ============================================================

# Número de elementos en tops
TOP_N = 25

# Categorías de edad para adultos y pediátricos
EDAD_PEDIATRICA = "0-15"
EDADES_ADULTOS = [r for r in RANGOS_EDAD if r != "0-15"]

# ============================================================
# CONFIGURACIÓN DE LA APLICACIÓN
# ============================================================

# Título de la aplicación
APP_TITLE = "Dashboard Epidemiológico IGSS Escuintla"
APP_SUBTITLE = "Análisis de Morbilidad 2018-2025"

# Configuración de página de Streamlit
PAGE_CONFIG = {
    'page_title': 'Dashboard IGSS Escuintla',
    'page_icon': '📊',
    'layout': 'wide',
    'initial_sidebar_state': 'expanded'
}

# ============================================================
# MENSAJES Y TEXTOS
# ============================================================

MESSAGES = {
    'loading': 'Cargando datos...',
    'no_data': 'No hay datos disponibles para los filtros seleccionados.',
    'error': 'Error al cargar los datos. Verifique la ubicación del archivo.',
}
