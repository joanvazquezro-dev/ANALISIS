"""Funciones auxiliares para cálculos simbólicos y numéricos de vigas."""
from __future__ import annotations

from typing import Dict, Iterable, Tuple

import numpy as np
import pandas as pd
import sympy as sp
from scipy.integrate import cumulative_trapezoid

from .viga import Viga, x


def generar_dataframe(viga: Viga, num_puntos: int = 400) -> pd.DataFrame:
    """Evalúa las expresiones simbólicas de la viga y devuelve un DataFrame."""

    datos = viga.evaluar(num_puntos=num_puntos)
    df = pd.DataFrame(datos)
    columnas = {
        "V": "cortante",
        "M": "momento",
        "theta": "pendiente",
        "deflexion": "deflexion",
    }
    df = df.rename(columns=columnas)
    return df


def obtener_maximos(df: pd.DataFrame) -> Dict[str, Tuple[float, float]]:
    """Encuentra valores máximos absolutos y sus posiciones."""

    resultados: Dict[str, Tuple[float, float]] = {}
    for columna in ["cortante", "momento", "pendiente", "deflexion"]:
        if columna not in df:
            continue
        idx = df[columna].abs().idxmax()
        resultados[columna] = (float(df.loc[idx, "x"]), float(df.loc[idx, columna]))
    return resultados


def comparar_simbolico_numerico(viga: Viga, num_puntos: int = 400) -> pd.DataFrame:
    """Integra numéricamente para comparar con la solución simbólica."""

    df = generar_dataframe(viga, num_puntos=num_puntos)
    EI = viga.E * viga.I
    curvatura = df["momento"].to_numpy() / EI
    x_vals = df["x"].to_numpy()

    pendiente_num = cumulative_trapezoid(curvatura, x_vals, initial=0.0)
    deflexion_num = cumulative_trapezoid(pendiente_num, x_vals, initial=0.0)

    # Ajuste lineal para cumplir y(0)=y(L)=0
    if len(x_vals) > 1:
        L = x_vals[-1]
        deflexion_num -= (x_vals / L) * deflexion_num[-1]

    resultados = pd.DataFrame({
        "x": x_vals,
        "pendiente_simbolica": df["pendiente"],
        "pendiente_numerica": pendiente_num,
        "deflexion_simbolica": df["deflexion"],
        "deflexion_numerica": deflexion_num,
    })

    resultados["error_pendiente"] = (
        resultados["pendiente_numerica"] - resultados["pendiente_simbolica"]
    )
    resultados["error_deflexion"] = (
        resultados["deflexion_numerica"] - resultados["deflexion_simbolica"]
    )
    return resultados


def crear_funciones_lambdify(viga: Viga) -> Dict[str, sp.Lambda]:
    """Devuelve funciones listas para evaluación numérica rápida."""

    expresiones = viga.obtener_expresiones()
    return {nombre: sp.lambdify(x, expr, "numpy") for nombre, expr in expresiones.items()}


def discretizar(expr: sp.Expr, L: float, num_puntos: int = 400) -> Tuple[np.ndarray, np.ndarray]:
    """Discretiza cualquier expresión simbólica en [0, L]."""

    x_vals = np.linspace(0.0, L, num_puntos)
    func = sp.lambdify(x, expr, "numpy")
    valores = func(x_vals)
    return x_vals, valores
