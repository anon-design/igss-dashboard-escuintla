# Dashboard Epidemiológico - IGSS Escuintla

Dashboard interactivo para análisis epidemiológico de morbilidad del Instituto Guatemalteco de Seguridad Social (IGSS) - Región Escuintla.

## Descripción

Sistema de visualización y análisis de datos epidemiológicos que procesa y presenta información sobre:

- **Morbilidad en Adultos** (>15 años): Análisis de los 25 diagnósticos más frecuentes en población adulta
- **Morbilidad Pediátrica** (0-15 años): Análisis de los 25 diagnósticos más frecuentes en población pediátrica
- **Análisis por Capítulos CIE-10**: Distribución de casos según la Clasificación Internacional de Enfermedades
- **Enfermedades de Notificación Obligatoria (ENO)**: Vigilancia epidemiológica de enfermedades que requieren notificación
- **Enfermedades Crónicas**: Análisis de enfermedades crónicas no transmisibles
- **Análisis Geográfico**: Distribución de casos por unidad médica

## Características

- Visualizaciones interactivas con Plotly
- Filtros dinámicos por unidad, año, sexo y edad
- Identificación automática de ENO y enfermedades crónicas
- Gráficos de tendencias temporales
- Comparaciones por sexo y edad
- Paleta de colores institucional del IGSS
- Interfaz moderna y responsiva
- Optimización de carga con caché de datos

## Requisitos del Sistema

- Python 3.8 o superior
- 4 GB RAM mínimo (recomendado: 8 GB)
- Navegador web moderno (Chrome, Firefox, Safari, Edge)

## Instalación

### 1. Clonar o descargar el proyecto

```bash
cd /ruta/a/tu/proyecto/dashboard
```

### 2. Crear entorno virtual (recomendado)

```bash
# En Windows
python -m venv venv
venv\Scripts\activate

# En macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Preparar datos

Asegúrate de tener el archivo de datos consolidado en la ubicación correcta:

```
/claude/bases_limpias/Rangos_CONSOLIDADA.csv
```

El archivo debe contener las siguientes columnas:
- `CIE10`: Código CIE-10 del diagnóstico
- `Unidad`: Unidad médica
- `Año`: Año del registro
- `Sexo`: Sexo del paciente (FEMENINO, MASCULINO, NO ESPECIFICADO)
- `Edad`: Edad o rango de edad
- `Casos`: Número de casos

## Uso

### Iniciar el dashboard

```bash
streamlit run app.py
```

El dashboard se abrirá automáticamente en tu navegador web en `http://localhost:8501`

### Navegación

1. **Barra lateral izquierda**: Contiene los filtros globales y el menú de navegación
   - Filtros: Unidad, Año, Sexo, Edad
   - Navegación: Selecciona el módulo de análisis que deseas ver

2. **Panel principal**: Muestra el contenido del módulo seleccionado
   - Métricas resumidas en la parte superior
   - Tablas de datos
   - Gráficos interactivos
   - Información adicional en expandibles

### Filtros

Los filtros en la barra lateral se aplican globalmente a todos los módulos:

- **Unidad**: Selecciona una o más unidades médicas para analizar
- **Año**: Selecciona uno o más años (rango 2018-2025)
- **Sexo**: Filtra por sexo (FEMENINO, MASCULINO, NO ESPECIFICADO)
- **Edad**: Filtra por rango de edad específico

Los cambios en los filtros actualizan automáticamente todas las visualizaciones.

### Módulos Disponibles

#### 1. Inicio
- Resumen general de estadísticas
- Tendencias temporales
- Métricas clave del período seleccionado

#### 2. Morbilidad Adultos
- Top 25 diagnósticos más frecuentes en mayores de 15 años
- Identificación de ENO y enfermedades crónicas
- Tendencias temporales y distribución por sexo

#### 3. Morbilidad Pediátrica
- Top 25 diagnósticos más frecuentes en población de 0-15 años
- Patrones específicos de morbilidad infantil
- Análisis temporal y por sexo

#### 4. Análisis por Capítulos CIE-10
- Distribución de casos por los 21 capítulos de CIE-10
- Tendencias por capítulo
- Distribución por sexo en principales capítulos

#### 5. ENO (Enfermedades de Notificación Obligatoria)
- Top 20 ENO más frecuentes
- Clasificación por tipo de notificación (inmediata, semanal)
- Distribución por categoría epidemiológica

#### 6. Enfermedades Crónicas
- Top 20 enfermedades crónicas más frecuentes
- Clasificación por categoría (metabólicas, cardiovasculares, etc.)
- Evolución temporal de principales crónicas

#### 7. Análisis Geográfico
- Distribución de casos por unidad médica
- Top diagnósticos por unidad
- Comparaciones entre unidades
- Distribución demográfica por unidad

## Estructura del Proyecto

```
dashboard/
├── app.py                          # Aplicación principal
├── config.py                       # Configuración y colores IGSS
├── requirements.txt                # Dependencias del proyecto
├── README.md                       # Este archivo
│
├── data/                           # Catálogos de datos
│   ├── capitulos_cie10.csv        # Catálogo de capítulos CIE-10
│   ├── catalogo_eno.csv           # Catálogo de ENO
│   └── catalogo_cronicas.csv      # Catálogo de enfermedades crónicas
│
├── modules/                        # Módulos de análisis
│   ├── __init__.py
│   ├── morbilidad_adultos.py     # Análisis adultos
│   ├── morbilidad_pediatrica.py  # Análisis pediátrico
│   ├── capitulos.py               # Análisis por capítulos
│   ├── eno.py                     # Análisis ENO
│   ├── cronicas.py                # Análisis crónicas
│   └── geografico.py              # Análisis geográfico
│
└── utils/                          # Utilidades
    ├── __init__.py
    ├── data_loader.py             # Carga de datos y caché
    ├── filters.py                 # Funciones de filtrado
    └── colors.py                  # Paleta de colores y gráficos
```

## Personalización

### Cambiar la ruta de datos

Edita el archivo `config.py`:

```python
# Ruta al archivo de datos consolidado
DATA_PATH = '/ruta/a/tu/Rangos_CONSOLIDADA.csv'
```

### Modificar colores institucionales

Edita el diccionario `COLORS` en `config.py`:

```python
COLORS = {
    'primary': '#0066A8',    # Azul IGSS
    'secondary': '#00A651',  # Verde IGSS
    'accent': '#FF6B35',     # Naranja
    # ...
}
```

### Agregar nuevos módulos

1. Crea un nuevo archivo en `modules/tu_modulo.py`
2. Implementa la función `render(df, df_eno, df_cronicas, df_capitulos)`
3. Importa y registra en `app.py`

## Solución de Problemas

### El dashboard no carga los datos

**Error**: `FileNotFoundError: [Errno 2] No such file or directory: '.../Rangos_CONSOLIDADA.csv'`

**Solución**: Verifica que el archivo de datos esté en la ubicación correcta especificada en `config.py`

### Error de memoria

**Error**: `MemoryError` o el dashboard se congela

**Solución**:
- Reduce el rango de años en los filtros
- Filtra por una unidad específica
- Aumenta la RAM disponible
- Considera usar una muestra de los datos para pruebas

### Gráficos no se visualizan

**Solución**:
- Actualiza el navegador
- Limpia la caché del navegador
- Verifica que Plotly esté instalado: `pip install plotly`

### Los filtros no funcionan

**Solución**:
- Reinicia el servidor de Streamlit
- Limpia la caché de Streamlit: presiona `C` en la interfaz web
- Verifica que las columnas del CSV sean correctas

## Rendimiento y Optimización

- El dashboard utiliza `@st.cache_data` para optimizar la carga de datos
- El caché tiene un TTL (Time To Live) de 1 hora
- Para limpiar la caché manualmente: presiona `C` en la interfaz web o reinicia el servidor

## Tecnologías Utilizadas

- **Streamlit**: Framework para aplicaciones web de datos
- **Plotly**: Gráficos interactivos
- **Pandas**: Manipulación y análisis de datos
- **Python 3**: Lenguaje de programación

## Datos y Privacidad

Este dashboard procesa datos agregados de morbilidad. No contiene información personal identificable de pacientes. Todos los datos están anonimizados y agregados por código CIE-10, unidad, año, sexo y edad.

## Contacto y Soporte

Para soporte técnico o preguntas sobre el dashboard:
- Departamento de Epidemiología - IGSS Escuintla
- Email: [tu-email@igss.gob.gt]
- Teléfono: [tu-teléfono]

## Licencia

© 2025 Instituto Guatemalteco de Seguridad Social (IGSS)
Todos los derechos reservados.

Este dashboard es de uso interno del IGSS y no debe ser distribuido sin autorización.

## Changelog

### Versión 1.0.0 (2025-11)
- Lanzamiento inicial
- 7 módulos de análisis implementados
- Filtros interactivos globales
- Visualizaciones con paleta institucional
- Optimización de carga con caché
- Identificación automática de ENO y crónicas

---

Desarrollado con ❤️ para el IGSS Escuintla
