"""Utilidades para exportación de resultados, manejo de rutas y guardado de configuración.

Funciones clave:
 - asegurar_directorios(): crea carpetas de salida.
 - exportar_tabla(): guarda un DataFrame como CSV en ``outputs/``.
 - exportar_grafica(): guarda una figura de Matplotlib en ``outputs/graficas``.
 - convertir_dataframe_export(): aplica factores de conversión a un DataFrame en SI
     para mostrar/exportar en unidades seleccionadas.
 - exportar_configuracion(): NUEVO. Serializa a JSON las propiedades de la viga
     y la lista de cargas para reproducir un análisis posteriormente.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Dict, Any
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

from .units import LENGTH_UNITS, FORCE_UNITS, DEFLEXION_DISPLAY  # nuevos imports

OUTPUT_DIR = Path("outputs")
GRAFICAS_DIR = OUTPUT_DIR / "graficas"


def asegurar_directorios() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
    GRAFICAS_DIR.mkdir(exist_ok=True, parents=True)


def exportar_tabla(dataframe: pd.DataFrame, nombre: str) -> Path:
    asegurar_directorios()
    ruta = OUTPUT_DIR / f"{nombre}.csv"
    dataframe.to_csv(ruta, index=False)
    return ruta


def exportar_grafica(figura, nombre: str) -> Path:
    asegurar_directorios()
    ruta = GRAFICAS_DIR / f"{nombre}.png"
    figura.savefig(ruta, dpi=200, bbox_inches="tight")
    return ruta


def formatear_maximos(maximos: dict) -> str:
    lineas = []
    for clave, (posicion, valor) in maximos.items():
        lineas.append(
            f"{clave.capitalize()}: {valor: .4e} en x = {posicion: .3f} m"
        )
    return "\n".join(lineas)


def convertir_dataframe_export(
    df_si: pd.DataFrame, len_unit: str, force_unit: str, defl_unit: str
) -> pd.DataFrame:
    """Convierte un DataFrame en SI a unidades solicitadas (solo columnas conocidas).

    Parámetros
    ---------
    df_si: DataFrame con columnas en SI (x, cortante [N], momento [N*m], deflexion [m])
    len_unit, force_unit, defl_unit: nombres de unidades destino.

    Retorna
    -------
    DataFrame convertido (copia) listo para exportar.
    """
    df = df_si.copy()
    fL = LENGTH_UNITS[len_unit]
    fF = FORCE_UNITS[force_unit]
    fDef = DEFLEXION_DISPLAY[defl_unit]
    if "x" in df:
        df["x"] = df["x"] / fL
    if "cortante" in df:
        df["cortante"] = df["cortante"] / fF
    if "momento" in df:
        df["momento"] = df["momento"] / (fF * fL)
    if "deflexion" in df:
        df["deflexion"] = df["deflexion"] / fDef
    return df


# ---------------------------------------------------------------------------
# Exportación de configuración / reproducibilidad
# ---------------------------------------------------------------------------

def _serializar_carga(carga: Carga) -> Dict[str, Any]:
    """Convierte una instancia de carga a un diccionario JSON-friendly.

    Se incluye sólo la información mínima necesaria para reconstruirla.
    """
    base: Dict[str, Any] = {"tipo": carga.__class__.__name__}
    if isinstance(carga, CargaPuntual):
        base.update({"magnitud_N": float(carga.magnitud), "posicion_m": float(carga.posicion)})
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
    elif isinstance(carga, CargaTrapezoidal):  # incluye triangular (herencia)
        base.update({
            "intensidad_inicio_Nm": float(carga.intensidad_inicio),
            "intensidad_fin_Nm": float(carga.intensidad_fin),
            "inicio_m": float(carga.inicio),
            "fin_m": float(carga.fin),
        })
    else:  # fallback genérico
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
    """Exporta a JSON las propiedades de la viga y la lista de cargas.

    Parámetros
    ----------
    L, E, I : float
        Propiedades en unidades SI (m, Pa, m^4).
    cargas : list[Carga]
        Instancias ya añadidas a la viga.
    nombre : str
        Prefijo del archivo JSON.
    incluir_timestamp : bool
        Si True, agrega sufijo fecha-hora para no sobrescribir.

    Devuelve
    --------
    Path al archivo creado dentro de ``outputs/``.
    """
    asegurar_directorios()
    if incluir_timestamp:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{nombre}_{stamp}.json"
    else:
        filename = f"{nombre}.json"
    ruta = OUTPUT_DIR / filename
    data: Dict[str, Any] = {
        "tipo": "viga_simplemente_apoyada",
        "propiedades_SI": {"L_m": float(L), "E_Pa": float(E), "I_m4": float(I)},
        "cargas": [_serializar_carga(c) for c in cargas],
        "notas": "Valores en unidades base SI. Cargar este JSON es suficiente para reconstruir el caso.",
        "version_schema": 1,
    }
    with ruta.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return ruta
