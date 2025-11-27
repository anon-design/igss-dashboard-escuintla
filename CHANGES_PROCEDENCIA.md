# Modificaciones al Dashboard - Soporte para Datos de Procedencia

**Fecha:** 2025-11-25

## Resumen

Se agregó soporte para cargar y analizar datos de procedencia geográfica al dashboard epidemiológico.

## Archivos Modificados

### 1. `/claude/dashboard/config.py`

**Cambios:**
- Agregada nueva constante `PROCEDENCIA_FILE` (líneas 23-25)
- Ruta: `BASE_DIR.parent / "bases_limpias" / "Procedencia_CONSOLIDADA.csv"`
- Apunta al archivo consolidado de procedencia (68 MB, 855,445 registros)

```python
# Archivo de datos de PROCEDENCIA (nuevo)
# Ubicado en bases_limpias (nivel superior)
PROCEDENCIA_FILE = BASE_DIR.parent / "bases_limpias" / "Procedencia_CONSOLIDADA.csv"
```

### 2. `/claude/dashboard/utils/data_loader.py`

**Cambios:**

#### a) Import actualizado (línea 13)
```python
from config import DATA_FILE, CATALOGOS_DIR, PROCEDENCIA_FILE
```

#### b) Nueva función `load_procedencia_data()` (líneas 390-433)

**Características:**
- Decorador: `@st.cache_data(ttl=3600)` (caché de 1 hora)
- Carga CSV de procedencia con encoding UTF-8
- Valida columnas requeridas: `['CIE10', 'Unidad', 'Año', 'Departamento', 'Municipio', 'Sexo', 'Edad', 'Casos']`
- Convierte `Año` a `Int64` y `Casos` a `int`
- Estandariza texto: `Departamento`, `Municipio`, `Sexo` → uppercase y trim
- Limpia códigos CIE10: elimina caracteres no alfanuméricos
- Manejo robusto de errores con mensajes de Streamlit

**Retorna:**
- `pd.DataFrame` con datos de procedencia, o `None` si hay error

**Estructura de datos:**
```
CIE10 × Unidad × Año × Departamento × Municipio × Sexo × Edad → Casos
```

#### c) Nueva función `get_procedencia_stats()` (líneas 436-468)

**Características:**
- Calcula estadísticas básicas del dataset de procedencia
- Maneja casos de DataFrame vacío o None

**Retorna diccionario con:**
- `total_registros`: Número de filas
- `total_casos`: Suma total de casos
- `años`: Lista ordenada de años únicos
- `departamentos`: Número único de departamentos
- `municipios`: Número único de municipios
- `unidades`: Número único de unidades médicas
- `codigos_cie10`: Número único de códigos CIE-10
- `año_min`: Año mínimo
- `año_max`: Año máximo
- `casos_por_año`: Dict con casos por año

## Validación

**Archivo fuente:**
- Ubicación: `/claude/bases_limpias/Procedencia_CONSOLIDADA.csv`
- Tamaño: 68 MB
- Existencia: ✓ Verificado

**Pruebas realizadas:**

```python
df = load_procedencia_data()
stats = get_procedencia_stats(df)
```

**Resultados:**
- ✓ Data cargada exitosamente
- ✓ Shape: (855,445 registros × 8 columnas)
- ✓ Total casos: 3,578,013
- ✓ Años: 2018-2025
- ✓ Departamentos: 23
- ✓ Municipios: 238
- ✓ Unidades: 7
- ✓ Códigos CIE-10: 7,000

**Distribución por año:**
```
2018: 495,903 casos
2019: 506,587 casos
2020: 287,158 casos (reducción COVID-19)
2021: 336,056 casos
2022: 401,300 casos
2023: 485,047 casos
2024: 532,694 casos
2025: 533,268 casos
─────────────────────
TOTAL: 3,578,013 casos
```

## Compatibilidad

- ✓ No rompe funcionalidad existente
- ✓ Sigue mismos patrones de código del módulo
- ✓ Usa decorador `@st.cache_data` como otras funciones de carga
- ✓ Manejo de errores consistente con el resto del código
- ✓ Estilo de código idéntico al existente

## Uso

```python
# En páginas del dashboard
from utils.data_loader import load_procedencia_data, get_procedencia_stats

# Cargar datos
df_proc = load_procedencia_data()

# Obtener estadísticas
stats = get_procedencia_stats(df_proc)

# Usar datos
if df_proc is not None:
    # Filtrar por departamento
    df_escuintla = df_proc[df_proc['Departamento'] == 'ESCUINTLA']
    
    # Top municipios
    top_municipios = df_proc.groupby('Municipio')['Casos'].sum().sort_values(ascending=False).head(10)
```

## Notas

- Las funciones siguen el mismo patrón que `load_data()` y `get_data_summary()`
- El caché de 1 hora (ttl=3600) optimiza performance
- Los datos se validan y limpian automáticamente en la carga
- Compatible con filtros existentes del dashboard
