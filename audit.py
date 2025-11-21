
import pandas as pd
from pathlib import Path
import sys

# --- Configuración ---
# Asegurarse de que las rutas son correctas
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR.parent / 'bases_limpias'
DATA_FILE = DATA_DIR / 'Rangos_SIN_PROCEDENCIA.csv'
OUTPUT_FILE = BASE_DIR / 'audit_report.csv'

def run_audit():
    """
    Realiza una auditoría profunda de consistencia de datos en el archivo fuente,
    comparando los totales de 'General Escuintla' con la suma de sus unidades específicas.
    Guarda un informe detallado en CSV.
    """
    print("======================================================")
    print("      INICIANDO AUDITORÍA PROFUNDA DE DATOS")
    print("======================================================")

    try:
        df = pd.read_csv(DATA_FILE)
        print(f"[INFO] Archivo de datos '{DATA_FILE.name}' cargado exitosamente.")
    except FileNotFoundError:
        print(f"\n[ERROR] No se encontró el archivo de datos en: {DATA_FILE}")
        return

    # --- 1. Limpieza y preparación de datos ---
    df = df[~df['Unidad'].str.contains('Procedencia', case=False, na=False)]
    df['Año'] = pd.to_numeric(df['Año'], errors='coerce')
    df.dropna(subset=['Año'], inplace=True)
    df['Año'] = df['Año'].astype(int)
    df['Casos'] = pd.to_numeric(df['Casos'], errors='coerce').fillna(0).astype(int)
    df['CIE10'] = df['CIE10'].astype(str).str.strip().str.upper()
    print("[INFO] Limpieza de datos inicial completada.")

    # --- 2. Agrupar datos por 'General Escuintla' y 'Unidades Específicas' ---
    group_cols = ['CIE10', 'Año', 'Sexo', 'Edad']
    
    df_general = df[df['Unidad'] == 'General Escuintla'].groupby(group_cols, as_index=False)['Casos'].sum()
    df_general.rename(columns={'Casos': 'Casos_General'}, inplace=True)
    
    unidades_especificas_nombres = [
        'Hospital Escuintla', 'Hospital Santa Lucia Cotzumalguapa',
        'Consultorio Masagua', 'Consultorio la Democracia', 'Consultorio Siquinala'
    ]
    df_especificas = df[df['Unidad'].isin(unidades_especificas_nombres)]
    df_especificas_sum = df_especificas.groupby(group_cols, as_index=False)['Casos'].sum()
    df_especificas_sum.rename(columns={'Casos': 'Suma_Especificas'}, inplace=True)
    
    print("[INFO] Datos agrupados por 'General' y 'Específicas'.")

    # --- 3. Comparar los dos grupos ---
    df_audit = pd.merge(df_general, df_especificas_sum, on=group_cols, how='outer').fillna(0)
    
    # Calcular la diferencia. Una diferencia != 0 es una inconsistencia.
    df_audit['Diferencia'] = df_audit['Suma_Especificas'] - df_audit['Casos_General']
    
    # Filtrar solo las filas donde hay inconsistencia
    df_inconsistencias = df_audit[df_audit['Diferencia'] != 0].copy()
    
    print(f"[INFO] Se encontraron {len(df_inconsistencias)} grupos de datos con inconsistencias.")

    # --- 4. Generar y guardar el informe ---
    if not df_inconsistencias.empty:
        df_inconsistencias = df_inconsistencias.sort_values(by='Diferencia', ascending=False)
        
        try:
            df_inconsistencias.to_csv(OUTPUT_FILE, index=False)
            print(f"\n[ÉXITO] Se ha guardado un informe detallado de las inconsistencias en:")
            print(f"        -> {OUTPUT_FILE}")
            
            total_casos_faltantes = df_inconsistencias[df_inconsistencias['Diferencia'] < 0]['Diferencia'].sum()
            total_casos_sobrantes = df_inconsistencias[df_inconsistencias['Diferencia'] > 0]['Diferencia'].sum()
            
            print("\n--- RESUMEN DE LA AUDITORÍA ---")
            print(f"Casos SOBRANTES en Específicas (Específicas > General): {total_casos_sobrantes:,.0f}")
            print(f"Casos FALTANTES en Específicas (General > Específicas): {abs(total_casos_faltantes):,.0f}")
            print("---------------------------------")
            
        except Exception as e:
            print(f"\n[ERROR] No se pudo guardar el archivo de informe: {e}")
    else:
        print("\n[ÉXITO] No se encontraron inconsistencias. Los datos son consistentes.")
        
if __name__ == '__main__':
    run_audit()
