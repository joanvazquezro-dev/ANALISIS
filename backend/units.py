"""Definiciones centralizadas de sistemas y factores de unidades.

Todos los cálculos internos del backend se realizan en SI:
- Longitud: m
- Fuerza: N
- Módulo: Pa
- Momento de inercia: m^4

Este módulo provee los diccionarios de factores para convertir valores
introducidos por el usuario a SI (multiplicar por el factor) y para
presentar resultados en otras unidades (dividir por el factor).
"""
from __future__ import annotations

from typing import Dict

# Factores a SI (multiplicar valor en unidad elegida * factor -> SI)
LENGTH_UNITS: Dict[str, float] = {"m": 1.0, "ft": 0.3048}
FORCE_UNITS: Dict[str, float] = {"N": 1.0, "kN": 1e3, "lb": 4.4482216153, "kgf": 9.81}
DIST_LOAD_UNITS: Dict[str, float] = {
    "N/m": 1.0,
    "kN/m": 1e3,
    "lb/ft": FORCE_UNITS["lb"] / LENGTH_UNITS["ft"],
    "kg/m": 9.81,  # masa lineal * g -> N/m
}
E_UNITS: Dict[str, float] = {"Pa": 1.0, "GPa": 1e9, "MPa": 1e6}
INERCIA_UNITS: Dict[str, float] = {"m^4": 1.0, "cm^4": (1e-2) ** 4}
DEFLEXION_DISPLAY: Dict[str, float] = {"m": 1.0, "mm": 1e-3}

# Sistemas de unidades predefinidos (para UI). Se mantienen E e I métricos en imperial para simplificar.
UNIT_SYSTEMS = {
    "SI (N, m)": {"len": "m", "force": "N", "w": "N/m", "E": "Pa", "I": "m^4", "defl": "m"},
    "SI mixto (kN, m)": {"len": "m", "force": "kN", "w": "kN/m", "E": "GPa", "I": "m^4", "defl": "mm"},
    "Entrada masa (kg/m)": {"len": "m", "force": "N", "w": "kg/m", "E": "Pa", "I": "m^4", "defl": "mm"},
    "Imperial simplificado (lb, ft)": {"len": "ft", "force": "lb", "w": "lb/ft", "E": "GPa", "I": "m^4", "defl": "mm"},
}


def factor(units_map: Dict[str, float], key: str) -> float:
    """Devuelve el factor de conversión a SI para una clave, con validación simple."""
    if key not in units_map:
        raise KeyError(f"Unidad desconocida: {key}")
    return units_map[key]
