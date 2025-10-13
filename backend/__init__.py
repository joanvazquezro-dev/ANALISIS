"""Paquete backend para el analizador de vigas."""
from .viga import (
    Viga,
    Apoyo,
    Carga,
    CargaPuntual,
    CargaMomento,
    CargaUniforme,
    CargaTriangular,
    CargaTrapezoidal,
)
from . import calculos, menus, utils

__all__ = [
    "Viga",
    "Apoyo",
    "Carga",
    "CargaPuntual",
    "CargaMomento",
    "CargaUniforme",
    "CargaTriangular",
    "CargaTrapezoidal",
    "calculos",
    "menus",
    "utils",
]
