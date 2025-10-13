"""Paquete backend para el analizador de vigas."""
from .viga import (
    Viga,
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
