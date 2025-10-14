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
    # CORRECCIÓN: Solo aplicar si realmente no se cumplen las condiciones (error > 1%)
    if len(x_vals) > 1:
        L = x_vals[-1]
        y_max = np.max(np.abs(deflexion_num))
        umbral_error = 0.01 * y_max if y_max > 1e-9 else 1e-9
        
        # Verificar si necesitamos ajustar (si y(L) no es aproximadamente 0)
        if abs(deflexion_num[-1]) > umbral_error:
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


# ============================================================
# MUESTREO POR EVENTOS Y EVALUACIÓN EN MALLA PERSONALIZADA
# ============================================================

def get_event_positions(viga: Viga) -> Dict[str, np.ndarray]:
    """
    Retorna posiciones relevantes (eventos) a lo largo de la viga:
    - 0, L
    - posiciones de apoyos
    - inicios y fines de cargas distribuidas
    - posiciones de cargas puntuales y momentos puntuales

    Útil para construir una malla de muestreo que capture saltos.
    """
    eventos = set([0.0, float(viga.longitud)])
    # Apoyos
    for a in viga.apoyos:
        eventos.add(float(a.posicion))
    # Cargas
    for c in viga.cargas:
        if c.__class__.__name__ == 'CargaPuntual':
            eventos.add(float(getattr(c, 'posicion')))
        elif c.__class__.__name__ == 'CargaMomento':
            eventos.add(float(getattr(c, 'posicion')))
        else:
            # Tipos con tramo: Uniforme, Triangular, Trapezoidal
            for key in ('inicio', 'fin'):
                if hasattr(c, key):
                    eventos.add(float(getattr(c, key)))
    xs = np.array(sorted(eventos), dtype=float)
    return {
        'todos': xs,
        'apoyos': np.array(sorted({float(a.posicion) for a in viga.apoyos}), dtype=float),
        'puntuales': np.array(sorted({float(getattr(c, 'posicion')) for c in viga.cargas if c.__class__.__name__ == 'CargaPuntual'}), dtype=float),
        'momentos': np.array(sorted({float(getattr(c, 'posicion')) for c in viga.cargas if c.__class__.__name__ == 'CargaMomento'}), dtype=float),
        'tramos': np.array(sorted({float(getattr(c, k)) for c in viga.cargas for k in ('inicio','fin') if hasattr(c, k)}), dtype=float),
    }


def muestreo_eventos(viga: Viga, puntos_por_tramo: int = 40, delta_frac: float = 1e-6) -> np.ndarray:
    """
    Construye malla de x concentrando puntos cerca de discontinuidades.
    - Inserta x-δ y x+δ alrededor de eventos relevantes
    - Discretiza uniformemente entre eventos
    """
    ev = get_event_positions(viga)
    xs = ev['todos']
    L = float(viga.longitud)
    delta = max(1e-12, delta_frac * L)

    x_grid: list[float] = []
    for i in range(len(xs)):
        xi = xs[i]
        # Añadir puntos alrededor de discontinuidades de V y M
        # V salta en apoyos y cargas puntuales; M salta en momentos puntuales
        es_discontinuidad_V = (xi in set(ev['apoyos'])) or (xi in set(ev['puntuales']))
        es_discontinuidad_M = (xi in set(ev['momentos']))
        if es_discontinuidad_V or es_discontinuidad_M:
            x_grid.extend([max(0.0, xi - delta), xi, min(L, xi + delta)])
        else:
            x_grid.append(xi)
        # Puntos intermedios hasta el siguiente evento
        if i < len(xs) - 1:
            xj = xs[i+1]
            if xj - xi > 1e-12:
                internos = np.linspace(xi, xj, puntos_por_tramo, endpoint=False)[1:]
                x_grid.extend(internos.tolist())

    # Garantizar punto final L
    if x_grid[-1] < L:
        x_grid.append(L)
    return np.array(sorted(set(x_grid)), dtype=float)


def evaluar_con_malla(viga: Viga, x_grid: np.ndarray) -> Dict[str, np.ndarray]:
    """
    Evalúa V, M, θ, y sobre una malla arbitraria x_grid.
    - Usa construcción simbólica de V(x) y evaluación numérica vectorizada
    - Integra numéricamente para M, θ, y
    - Añade saltos de momentos puntuales en M
    - Ajusta y=0 en apoyos
    """
    import sympy as sp
    from scipy.integrate import cumulative_trapezoid
    import numpy as np
    from .viga import x as x_sym, CargaMomento

    # Cortante simbólico y evaluación numérica
    V_expr = viga._construir_cortante_expr()
    V_func = sp.lambdify(x_sym, V_expr, 'numpy')
    V_vals = np.asarray(V_func(x_grid), dtype=float)

    # Integra para M
    M_vals = cumulative_trapezoid(V_vals, x_grid, initial=0.0)

    # Añadir saltos de momentos puntuales
    # CORRECCIÓN: Aplicar salto directo (suma M0 donde x > a) en lugar de multiplicar por escalón
    if any(c.__class__.__name__ == 'CargaMomento' for c in viga.cargas):
        L = float(viga.longitud)
        tol = max(1e-12, 1e-9 * L)
        for c in viga.cargas:
            if c.__class__.__name__ != 'CargaMomento':
                continue
            a = float(getattr(c, 'posicion'))
            # Si momento en apoyo con en_vano=False, omitir salto
            esta_en_apoyo = any(abs(a - ap.posicion) < 1e-12 for ap in viga.apoyos)
            en_vano = bool(getattr(c, 'en_vano', True))
            if esta_en_apoyo and not en_vano:
                continue
            
            # Salto directo: sumar M0 donde x > a (implementación correcta de Heaviside)
            magnitud = float(getattr(c, 'magnitud'))
            M_vals[x_grid > (a + tol)] += magnitud
            
            # En x = a, sumar M0/2 (convención Heaviside con H(0)=1/2)
            idx_at_a = np.argmin(np.abs(x_grid - a))
            if abs(x_grid[idx_at_a] - a) < tol:
                M_vals[idx_at_a] += magnitud * 0.5

    # θ y y
    EI = float(viga.E * viga.I)
    theta_vals = cumulative_trapezoid(M_vals / EI, x_grid, initial=0.0)
    y_vals = cumulative_trapezoid(theta_vals, x_grid, initial=0.0)

    # Ajuste de condiciones de borde en apoyos
    # Ahora que aplicamos saltos de momentos puntuales ANTES de esta corrección,
    # es seguro aplicar siempre (solo evitamos si el error es despreciable < 1e-9)
    if len(viga.apoyos) >= 2:
        a1 = float(viga.apoyos[0].posicion)
        a2 = float(viga.apoyos[1].posicion)
        i1 = int(np.argmin(np.abs(x_grid - a1)))
        i2 = int(np.argmin(np.abs(x_grid - a2)))
        x1, x2 = x_grid[i1], x_grid[i2]
        y1, y2 = y_vals[i1], y_vals[i2]
        
        # Aplicar corrección si hay cualquier error medible
        if (abs(y1) > 1e-9 or abs(y2) > 1e-9) and abs(x2 - x1) > 1e-15:
            m = (y2 - y1) / (x2 - x1)
            y_vals = y_vals - (y1 + m * (x_grid - x1))
    elif len(viga.apoyos) == 1:
        a = float(viga.apoyos[0].posicion)
        i0 = int(np.argmin(np.abs(x_grid - a)))
        if abs(y_vals[i0]) > 1e-9:
            y_vals = y_vals - y_vals[i0]

    return {
        'x': x_grid,
        'V': V_vals,
        'M': M_vals,
        'theta': theta_vals,
        'deflexion': y_vals,
    }


def generar_dataframe_eventos(viga: Viga, puntos_por_tramo: int = 40) -> pd.DataFrame:
    """
    Genera DataFrame usando el nuevo método de integración por sub-tramos.
    
    ACTUALIZADO (Oct 2025): Ahora usa viga.evaluar() que implementa
    integración robusta por sub-tramos con nudos.
    
    Parameters
    ----------
    viga : Viga
        Objeto viga configurado con apoyos y cargas
    puntos_por_tramo : int
        Número de puntos por sub-tramo (default: 40)
    
    Returns
    -------
    pd.DataFrame
        DataFrame con columnas: x, cortante, momento, pendiente, deflexion
    """
    # Usar el nuevo método de integración por sub-tramos
    # viga.evaluar() automáticamente llama a evaluar_por_subtramos()
    num_puntos_aprox = puntos_por_tramo * max(2, len(viga.apoyos) + len(viga.cargas))
    datos = viga.evaluar(num_puntos=num_puntos_aprox)
    
    df = pd.DataFrame({
        'x': datos['x'],
        'cortante': datos['V'],
        'momento': datos['M'],
        'pendiente': datos['theta'],
        'deflexion': datos['deflexion'],
    })
    return df
