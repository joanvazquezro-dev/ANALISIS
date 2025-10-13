"""
============================================================
UTILIDADES DE EXPORTACIÓN
============================================================

¿Qué hace este archivo?
- Guarda resultados en archivos (CSV, PNG, JSON)
- Convierte datos entre diferentes unidades
- Crea carpetas de salida automáticamente

Funciones principales:
  - exportar_tabla(): Guarda DataFrame como CSV
  - exportar_grafica(): Guarda gráficas como PNG
  - exportar_configuracion(): Guarda configuración completa en JSON
  - convertir_dataframe_export(): Cambia unidades en resultados
============================================================
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any
import json
from datetime import datetime

from .viga import (
    CargaPuntual,
    CargaMomento,
    CargaUniforme,
    CargaTriangular,
    CargaTrapezoidal,
    Carga,
)

import pandas as pd

from .units import LENGTH_UNITS, FORCE_UNITS, DEFLEXION_DISPLAY

# Carpetas donde se guardan los resultados
OUTPUT_DIR = Path("outputs")
GRAFICAS_DIR = OUTPUT_DIR / "graficas"

# ============================================================
# FUNCIONES DE EXPORTACIÓN BÁSICAS
# ============================================================

def asegurar_directorios() -> None:
    """Crea las carpetas outputs/ y outputs/graficas/ si no existen."""
    OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
    GRAFICAS_DIR.mkdir(exist_ok=True, parents=True)


def exportar_tabla(dataframe: pd.DataFrame, nombre: str) -> Path:
    """
    Guarda un DataFrame como archivo CSV.
    
    Uso:
        ruta = exportar_tabla(df, "resultados_viga")
        → Crea: outputs/resultados_viga.csv
    """
    asegurar_directorios()
    ruta = OUTPUT_DIR / f"{nombre}.csv"
    dataframe.to_csv(ruta, index=False)
    return ruta


def exportar_grafica(figura, nombre: str) -> Path:
    """
    Guarda una figura de Matplotlib como PNG.
    
    Uso:
        ruta = exportar_grafica(fig, "diagrama_momento")
        → Crea: outputs/graficas/diagrama_momento.png
    """
    asegurar_directorios()
    ruta = GRAFICAS_DIR / f"{nombre}.png"
    figura.savefig(ruta, dpi=200, bbox_inches="tight")
    return ruta


def formatear_maximos(maximos: dict) -> str:
    """
    Convierte diccionario de máximos a texto legible.
    
    Ejemplo:
        {"cortante": (2.5, 1000), "momento": (3.0, 1500)}
        → "Cortante: 1.0000e+03 en x = 2.500 m\n
           Momento: 1.5000e+03 en x = 3.000 m"
    """
    lineas = []
    for clave, (posicion, valor) in maximos.items():
        lineas.append(
            f"{clave.capitalize()}: {valor: .4e} en x = {posicion: .3f} m"
        )
    return "\n".join(lineas)

# ============================================================
# CONVERSIÓN DE UNIDADES PARA EXPORTACIÓN
# ============================================================

def convertir_dataframe_export(
    df_si: pd.DataFrame, len_unit: str, force_unit: str, defl_unit: str
) -> pd.DataFrame:
    """
    Convierte un DataFrame desde SI a otras unidades.
    
    Los cálculos internos siempre usan SI (m, N, Pa).
    Esta función cambia las unidades solo para mostrar/exportar.
    
    Ejemplo:
        df_si tiene x en metros, cortante en Newtons
        convertir_dataframe_export(df_si, "ft", "kN", "mm")
        → df con x en pies, cortante en kilonewtons, deflexión en mm
    
    Parámetros:
        df_si: DataFrame con datos en SI
        len_unit: Unidad de longitud deseada ("m", "ft")
        force_unit: Unidad de fuerza ("N", "kN", "lb")
        defl_unit: Unidad de deflexión ("m", "mm")
    
    Retorna:
        Nuevo DataFrame con valores convertidos
    """
    df = df_si.copy()
    
    # Factores de conversión (de SI a unidad deseada)
    fL = LENGTH_UNITS[len_unit]
    fF = FORCE_UNITS[force_unit]
    fDef = DEFLEXION_DISPLAY[defl_unit]
    
    # Convertir cada columna según su magnitud física
    if "x" in df:
        df["x"] = df["x"] / fL  # Longitud
    if "cortante" in df:
        df["cortante"] = df["cortante"] / fF  # Fuerza
    if "momento" in df:
        df["momento"] = df["momento"] / (fF * fL)  # Fuerza × Longitud
    if "deflexion" in df:
        df["deflexion"] = df["deflexion"] / fDef  # Longitud (pequeña)
    
    return df

# ============================================================
# EXPORTACIÓN DE CONFIGURACIÓN (para reproducir análisis)
# ============================================================

def _serializar_carga(carga: Carga) -> Dict[str, Any]:
    """
    Convierte una carga a diccionario JSON para guardar.
    
    Esto permite guardar la configuración completa de un análisis
    y poder reproducirlo más tarde.
    """
    base: Dict[str, Any] = {"tipo": carga.__class__.__name__}
    
    if isinstance(carga, CargaPuntual):
        base.update({
            "magnitud_N": float(carga.magnitud),
            "posicion_m": float(carga.posicion)
        })
    elif isinstance(carga, CargaMomento):
        base.update({
            "momento_Nm": float(carga.magnitud),
            "posicion_m": float(carga.posicion),
            "en_vano": bool(carga.en_vano),
        })
    elif isinstance(carga, CargaUniforme):
        base.update({
            "intensidad_Nm": float(carga.intensidad),
            "inicio_m": float(carga.inicio),
            "fin_m": float(carga.fin),
        })
    elif isinstance(carga, CargaTrapezoidal):
        base.update({
            "intensidad_inicio_Nm": float(carga.intensidad_inicio),
            "intensidad_fin_Nm": float(carga.intensidad_fin),
            "inicio_m": float(carga.inicio),
            "fin_m": float(carga.fin),
        })
    else:
        # Para cualquier otra carga, guardar todos los atributos numéricos
        for k, v in carga.__dict__.items():
            if isinstance(v, (int, float)):
                base[k] = float(v)
    
    return base


def exportar_configuracion(
    L: float,
    E: float,
    I: float,
    cargas: List[Carga],
    nombre: str = "configuracion_viga",
    incluir_timestamp: bool = True,
) -> Path:
    """
    Guarda la configuración completa de la viga en un archivo JSON.
    
    Esto es útil para:
      - Documentar exactamente qué parámetros se usaron
      - Reproducir el mismo análisis más tarde
      - Compartir configuraciones con otros
    
    Uso:
        ruta = exportar_configuracion(L=6.0, E=210e9, I=8e-6, cargas=lista_cargas)
        → Crea: outputs/configuracion_viga_20250113_143052.json
    
    Parámetros:
        L, E, I: Propiedades de la viga (en unidades SI)
        cargas: Lista de objetos Carga
        nombre: Nombre base del archivo
        incluir_timestamp: Si True, agrega fecha y hora al nombre
    
    Retorna:
        Ruta del archivo JSON creado
    """
    asegurar_directorios()
    
    # Generar nombre de archivo
    if incluir_timestamp:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{nombre}_{stamp}.json"
    else:
        filename = f"{nombre}.json"
    
    ruta = OUTPUT_DIR / filename
    
    # Crear diccionario con toda la información
    data: Dict[str, Any] = {
        "tipo": "viga_simplemente_apoyada",
        "propiedades_SI": {
            "L_m": float(L),
            "E_Pa": float(E),
            "I_m4": float(I)
        },
        "cargas": [_serializar_carga(c) for c in cargas],
        "notas": "Valores en unidades SI. Carga este JSON para reproducir el análisis.",
        "version_schema": 1,
    }
    
    # Guardar JSON con formato legible
    with ruta.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return ruta
