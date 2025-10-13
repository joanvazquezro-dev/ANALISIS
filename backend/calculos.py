"""
============================================================
FUNCIONES AUXILIARES DE CÁLCULO
============================================================

¿Qué hace este archivo?
- Convierte resultados de la viga a tablas (DataFrames)
- Encuentra valores máximos en los resultados
- Compara resultados simbólicos vs numéricos
- Crea funciones numéricas desde expresiones matemáticas

Funciones principales:
  - generar_dataframe(): Crea tabla con x, V, M, θ, y
  - obtener_maximos(): Encuentra valores máximos y sus posiciones
  - discretizar(): Evalúa una expresión en puntos específicos
============================================================
"""
from __future__ import annotations

from typing import Dict, Tuple

import numpy as np
import pandas as pd
import sympy as sp
from scipy.integrate import cumulative_trapezoid

from .viga import Viga, x

# ============================================================
# GENERACIÓN DE TABLAS DE RESULTADOS
# ============================================================

def generar_dataframe(viga: Viga, num_puntos: int = 400) -> pd.DataFrame:
    """
    Evalúa la viga y retorna una tabla con todos los resultados.
    
    Uso:
        df = generar_dataframe(mi_viga, num_puntos=500)
        df contiene columnas: x, cortante, momento, pendiente, deflexion
    
    Parámetros:
        viga: Objeto Viga con cargas ya agregadas
        num_puntos: Cantidad de puntos para evaluar a lo largo de la viga
    
    Retorna:
        DataFrame con resultados evaluados
    """
    datos = viga.evaluar(num_puntos=num_puntos)
    df = pd.DataFrame(datos)
    
    # Renombrar columnas para claridad
    columnas = {
        "V": "cortante",
        "M": "momento",
        "theta": "pendiente",
        "deflexion": "deflexion",
    }
    df = df.rename(columns=columnas)
    return df


def obtener_maximos(df: pd.DataFrame) -> Dict[str, Tuple[float, float]]:
    """
    Encuentra los valores máximos (en valor absoluto) y dónde ocurren.
    
    Uso:
        maximos = obtener_maximos(df)
        maximos["momento"] → (x_donde_ocurre, valor_maximo)
    
    Ejemplo de resultado:
        {
            "cortante": (2.5, 1500.0),    # Máximo |V| = 1500 N en x=2.5 m
            "momento": (3.0, -2250.0),     # Máximo |M| = 2250 N·m en x=3.0 m
            "deflexion": (3.0, -0.0025)    # Máxima |y| = 2.5 mm en x=3.0 m
        }
    
    Retorna:
        Diccionario con (posición, valor) del máximo absoluto de cada magnitud
    """
    resultados: Dict[str, Tuple[float, float]] = {}
    
    for columna in ["cortante", "momento", "pendiente", "deflexion"]:
        if columna not in df:
            continue
        
        # Encontrar índice del valor máximo absoluto
        idx = df[columna].abs().idxmax()
        
        # Guardar posición x y valor
        resultados[columna] = (
            float(df.loc[idx, "x"]),
            float(df.loc[idx, columna])
        )
    
    return resultados


# ============================================================
# FUNCIONES AUXILIARES AVANZADAS
# ============================================================

def comparar_simbolico_numerico(viga: Viga, num_puntos: int = 400) -> pd.DataFrame:
    """
    Compara resultados simbólicos vs integración numérica pura.
    
    Útil para verificar la precisión de los cálculos.
    Integra numéricamente desde M(x) para obtener θ y y,
    luego compara con los valores simbólicos.
    
    Retorna DataFrame con ambos resultados y el error.
    """
    df = generar_dataframe(viga, num_puntos=num_puntos)
    EI = viga.E * viga.I
    curvatura = df["momento"].to_numpy() / EI
    x_vals = df["x"].to_numpy()

    # Integración numérica usando método del trapecio
    pendiente_num = cumulative_trapezoid(curvatura, x_vals, initial=0.0)
    deflexion_num = cumulative_trapezoid(pendiente_num, x_vals, initial=0.0)

    # Ajuste lineal para cumplir condiciones de borde y(0)=y(L)=0
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
    """
    Crea funciones numéricas desde expresiones simbólicas.
    
    Útil para evaluación rápida de puntos específicos sin
    tener que trabajar con expresiones matemáticas complejas.
    
    Retorna diccionario de funciones que pueden ser llamadas
    directamente con valores numéricos.
    """
    expresiones = viga.obtener_expresiones()
    return {nombre: sp.lambdify(x, expr, "numpy") for nombre, expr in expresiones.items()}


def discretizar(expr: sp.Expr, L: float, num_puntos: int = 400) -> Tuple[np.ndarray, np.ndarray]:
    """
    Evalúa una expresión matemática en puntos equiespaciados.
    
    Uso:
        # expr es una expresión simbólica de SymPy
        x_valores, y_valores = discretizar(expr, L=6.0, num_puntos=100)
    
    Parámetros:
        expr: Expresión simbólica de SymPy
        L: Longitud del dominio [0, L]
        num_puntos: Cantidad de puntos a evaluar
    
    Retorna:
        Tupla (array_x, array_y) con coordenadas evaluadas
    """
    x_vals = np.linspace(0.0, L, num_puntos)
    func = sp.lambdify(x, expr, "numpy")
    valores = func(x_vals)
    return x_vals, valores
