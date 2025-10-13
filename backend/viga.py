"""Modelado de vigas simplemente apoyadas (análisis elástico lineal).

Resumen
=======
Este módulo implementa:

1. Jerarquía de cargas (puntual, uniforme, triangular, trapezoidal).
2. Clase central :class:`Viga` que:
     - Calcula reacciones en apoyos por equilibrio estático.
     - Construye expresiones simbólicas de cortante V(x), momento M(x),
         pendiente θ(x) y deflexión y(x) usando SymPy.
     - Proporciona un *fallback* numérico robusto basado en integración
         trapezoidal acumulada cuando la integración simbólica falla
         (expresiones excesivamente complejas o combinaciones degeneradas).

Convenciones de Signo
---------------------
* Fuerzas hacia abajo se ingresan con magnitud positiva (las reacciones
    resultan positivas hacia arriba si el equilibrio lo requiere).
* V(x) positivo: respuesta neta *hacia arriba* a la izquierda de la sección.
    (Esto implica que una carga puntual descendente introduce un salto negativo
    en V.)
* M(x) positivo con la convención estándar (fibras superiores en compresión).

Hipótesis
---------
* Flexión esbelta (teoría de Euler-Bernoulli): se desprecia cortante en
    la deflexión (no se usa teoría de Timoshenko).
* Material lineal elástico: E constante.
* Momento de inercia constante a lo largo de la viga.
* Apoyos simples: y(0)=0, y(L)=0.

Notas de Implementación
-----------------------
* Se emplean funciones de Heaviside y notación de Macaulay para ensamblar
    piezas a trozos sin necesidad de condicionales complicados.
* Las integraciones simbólicas pueden lanzar excepciones; se prueban rutas
    alternativas antes de escalar el error.
* Cachés (_reacciones, _expresiones, _lambdas) se invalidan al agregar o
    limpiar cargas, evitando recomputación redundante.
* El fallback numérico garantiza siempre un resultado utilizable para la UI.

Esta documentación está pensada para que un estudiante pueda explicar al
profesor el flujo de cálculo sin entrar a detalles de SymPy.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

import numpy as np
import sympy as sp

x = sp.symbols("x", real=True, nonnegative=True)


def heaviside(val: sp.Expr) -> sp.Heaviside:
    """Conveniencia para usar Heaviside con valor en cero igual a 0."""
    return sp.Heaviside(val, 0)


def heaviside_half(val: sp.Expr) -> sp.Heaviside:
    """Heaviside con valor en el origen igual a 1/2.

    Se usa para representar saltos en M(x) por momentos concentrados
    cuando impacta evaluar exactamente en el punto de aplicación (x=a).
    """
    return sp.Heaviside(val, sp.Rational(1, 2))


def macaulay(variable: sp.Symbol, offset: float, exponent: int) -> sp.Expr:
    """Devuelve la expresión de Macaulay <x - a>^n."""
    return sp.Pow(variable - offset, exponent) * heaviside(variable - offset)


@dataclass
class Carga:
    """Clase base abstracta para cualquier tipo de carga.

    Cada subclase debe implementar:
    - :meth:`total_load`  (magnitud total equivalente en Newtons).
    - :meth:`moment_about` (momento respecto a un origen dado).
    - :meth:`shear_expression` (contribución simbólica a V(x)).
    - Opcionalmente :meth:`load_intensity` si es carga distribuida.
    """

    def total_load(self) -> float:
        raise NotImplementedError

    def moment_about(self, origen: float = 0.0) -> float:
        raise NotImplementedError

    def shear_expression(self, variable: sp.Symbol = x) -> sp.Expr:
        """Contribución al esfuerzo cortante."""
        raise NotImplementedError

    def load_intensity(self, variable: sp.Symbol = x) -> sp.Expr:
        """Intensidad de carga distribuida.

        Para cargas concentradas devolver 0.
        """

        return sp.Integer(0)

    def descripcion(self) -> str:
        return self.__class__.__name__


@dataclass
class CargaPuntual(Carga):
    magnitud: float
    posicion: float
    units: str | None = None  # opcional: 'kgf' o 'kg'

    def __post_init__(self) -> None:
        # Conversión de unidades opcional (mantener SI internamente)
        if self.units:
            u = self.units.lower()
            if u in {"kgf", "kg"}:  # tratar masa como kgf * g
                self.magnitud *= 9.81
        if self.posicion < 0:
            raise ValueError("La posición debe ser no negativa")
        if abs(self.magnitud) < 1e-12:
            raise ValueError("La magnitud debe ser significativa")

    def total_load(self) -> float:
        return float(self.magnitud)

    def moment_about(self, origen: float = 0.0) -> float:
        distancia = self.posicion - origen
        return float(self.magnitud * distancia)

    def shear_expression(self, variable: sp.Symbol = x) -> sp.Expr:
        return -self.magnitud * heaviside(variable - self.posicion)

    def descripcion(self) -> str:
        return f"Carga puntual P={self.magnitud:.3g} N en x={self.posicion:.3g} m"


@dataclass
class CargaMomento(Carga):
    """Momento concentrado (par) aplicado en una posición x=a.

    Convención: magnitud positiva produce un salto positivo en M(x).
    No introduce fuerza vertical neta, por lo que V(x) no cambia.
    """

    magnitud: float  # N·m
    posicion: float  # m
    en_vano: bool = True  # Si False y el momento está en un apoyo, no se aplica salto dentro del vano

    def __post_init__(self) -> None:
        if self.posicion < 0:
            raise ValueError("La posición debe ser no negativa")
        if abs(self.magnitud) < 1e-12:
            raise ValueError("La magnitud del momento debe ser significativa")

    def total_load(self) -> float:
        return 0.0

    def moment_about(self, origen: float = 0.0) -> float:
        # Un par es un vector libre: el momento respecto a cualquier origen es su magnitud.
        return float(self.magnitud)

    def shear_expression(self, variable: sp.Symbol = x) -> sp.Expr:
        # Un momento concentrado no altera V(x) en el modelo clásico (no usamos distribuciones).
        return sp.Integer(0)

    def descripcion(self) -> str:
        return f"Momento puntual M={self.magnitud:.3g} N·m en x={self.posicion:.3g} m"

@dataclass
class CargaUniforme(Carga):
    intensidad: float
    inicio: float
    fin: float
    units: str | None = None  # opcional: 'kg_per_m', 'kg/m'

    def __post_init__(self) -> None:
        if self.fin <= self.inicio:
            raise ValueError("'fin' debe ser mayor que 'inicio' en la carga uniforme")
        if self.units:
            u = self.units.lower().replace(" ", "")
            if u in {"kg_per_m", "kg/m", "kgm", "kgm-1"}:
                self.intensidad *= 9.81  # convertir masa lineal a N/m

    @property
    def longitud(self) -> float:
        return self.fin - self.inicio

    def total_load(self) -> float:
        return float(self.intensidad * self.longitud)

    def moment_about(self, origen: float = 0.0) -> float:
        distancia = (self.inicio + self.fin) / 2 - origen
        return float(self.total_load() * distancia)

    def shear_expression(self, variable: sp.Symbol = x) -> sp.Expr:
        return (
            -self.intensidad * macaulay(variable, self.inicio, 1)
            + self.intensidad * macaulay(variable, self.fin, 1)
        )

    def load_intensity(self, variable: sp.Symbol = x) -> sp.Expr:
        return self.intensidad * (heaviside(variable - self.inicio) - heaviside(variable - self.fin))

    def descripcion(self) -> str:
        return (
            f"Carga uniforme w={self.intensidad:.3g} N/m entre {self.inicio:.3g} y {self.fin:.3g} m"
        )


@dataclass
class CargaTrapezoidal(Carga):
    intensidad_inicio: float
    intensidad_fin: float
    inicio: float
    fin: float
    units: str | None = None  # opcional: 'kg_per_m'

    def __post_init__(self) -> None:
        if self.fin <= self.inicio:
            raise ValueError("'fin' debe ser mayor que 'inicio' en la carga trapezoidal")
        if self.units:
            u = self.units.lower().replace(" ", "")
            if u in {"kg_per_m", "kg/m", "kgm", "kgm-1"}:
                self.intensidad_inicio *= 9.81
                self.intensidad_fin *= 9.81

    @property
    def longitud(self) -> float:
        return self.fin - self.inicio

    @property
    def pendiente(self) -> float:
        return (self.intensidad_fin - self.intensidad_inicio) / self.longitud

    def total_load(self) -> float:
        return float((self.intensidad_inicio + self.intensidad_fin) * self.longitud / 2)

    def moment_about(self, origen: float = 0.0) -> float:
        if self.intensidad_inicio == self.intensidad_fin:
            distancia = (self.inicio + self.fin) / 2 - origen
            return float(self.total_load() * distancia)

        w1, w2 = self.intensidad_inicio, self.intensidad_fin
        L = self.longitud
        if (w1 + w2) == 0:
            return 0.0
        distancia_relativa = L * (w1 + 2 * w2) / (3 * (w1 + w2))
        distancia = self.inicio + distancia_relativa - origen
        return float(self.total_load() * distancia)

    def shear_expression(self, variable: sp.Symbol = x) -> sp.Expr:
        w1, w2 = self.intensidad_inicio, self.intensidad_fin
        a, b = self.inicio, self.fin
        k = (w2 - w1) / (b - a)
        expr = -(
            w1 * macaulay(variable, a, 1)
            + k / 2 * macaulay(variable, a, 2)
        )
        expr += (
            w1 * macaulay(variable, b, 1)
            + k / 2 * macaulay(variable, b, 2)
        )
        return sp.simplify(expr)

    def load_intensity(self, variable: sp.Symbol = x) -> sp.Expr:
        w1, w2 = self.intensidad_inicio, self.intensidad_fin
        a, b = self.inicio, self.fin
        if b == a:
            return sp.Integer(0)
        pendiente = (w2 - w1) / (b - a)
        segmento = w1 + pendiente * (variable - a)
        return sp.Piecewise(
            (0, variable < a),
            (segmento, sp.And(variable >= a, variable <= b)),
            (0, True),
        )

    def descripcion(self) -> str:
        return (
            "Carga trapezoidal de {w1:.3g} a {w2:.3g} N/m entre {a:.3g} y {b:.3g} m".format(
                w1=self.intensidad_inicio,
                w2=self.intensidad_fin,
                a=self.inicio,
                b=self.fin,
            )
        )


@dataclass
class CargaTriangular(CargaTrapezoidal):
    def __post_init__(self) -> None:
        super().__post_init__()
        if not (self.intensidad_inicio == 0.0 or self.intensidad_fin == 0.0):
            raise ValueError(
                "La carga triangular requiere que una de las intensidades sea cero;"
                " utilice CargaTrapezoidal para el caso general."
            )

    def descripcion(self) -> str:
        orientacion = "creciente" if self.intensidad_inicio == 0 else "decreciente"
        valor = self.intensidad_fin if orientacion == "creciente" else self.intensidad_inicio
        return (
            f"Carga triangular {orientacion} con w₀={valor:.3g} N/m entre {self.inicio:.3g} y {self.fin:.3g} m"
        )


@dataclass
class Viga:
    """Modelo de una viga simplemente apoyada.

    Aporta métodos para construir expresiones simbólicas de cortante, momento,
    pendiente y deflexión. Si el proceso simbólico falla, existe un *fallback*
    numérico vectorizado.
    """

    longitud: float
    E: float
    I: float
    cargas: List[Carga] = field(default_factory=list)
    debug: bool = False  # Permite activar mensajes de depuración controladamente
    _reacciones: Optional[Dict[str, float]] = field(default=None, init=False, repr=False)
    _expresiones: Optional[Dict[str, sp.Expr]] = field(default=None, init=False, repr=False)
    _lambdas: Optional[Dict[str, Callable]] = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.longitud <= 0:
            raise ValueError("La longitud de la viga debe ser positiva")
        if self.E <= 0:
            raise ValueError("El módulo de elasticidad debe ser positivo")
        if self.I <= 0:
            raise ValueError("El momento de inercia debe ser positivo")

    def agregar_carga(self, carga: Carga) -> None:
        """Agrega una carga verificando que esté dentro del dominio de la viga.

        Resetea las cachés de resultados para asegurar coherencia.
        """
        if isinstance(carga, CargaPuntual):
            if carga.posicion > self.longitud:
                raise ValueError(
                    f"La carga puntual en x={carga.posicion} está fuera de la viga (L={self.longitud})"
                )
        elif isinstance(carga, CargaMomento):
            if carga.posicion > self.longitud:
                raise ValueError(
                    f"El momento puntual en x={carga.posicion} está fuera de la viga (L={self.longitud})"
                )
        elif hasattr(carga, "fin"):
            if getattr(carga, "fin") > self.longitud:  # type: ignore[arg-type]
                raise ValueError(
                    f"La carga distribuida termina en x={getattr(carga,'fin')}, fuera de la viga (L={self.longitud})"
                )

        self.cargas.append(carga)
        # Invalidar cachés
        self._reacciones = None
        self._expresiones = None
        self._lambdas = None

    def limpiar_cargas(self) -> None:
        """Elimina todas las cargas e invalida cachés."""
        self.cargas.clear()
        self._reacciones = None
        self._expresiones = None
        self._lambdas = None

    def calcular_reacciones(self) -> Dict[str, float]:
        """Calcula y memoriza las reacciones en apoyos A (x=0) y B (x=L).

        Método: equilibrio estático en 2D (solo fuerzas verticales):
        RA + RB = ΣF
        RB * L = Σ( F_i * distancia_i_al_origen )

        Returns
        -------
        dict: {'RA': float, 'RB': float}
        """
        if self._reacciones is not None:
            return self._reacciones

        suma_cargas = sum(c.total_load() for c in self.cargas)
        momentos = sum(c.moment_about(0.0) for c in self.cargas)
        RB = momentos / self.longitud if self.longitud != 0 else 0.0
        RA = suma_cargas - RB
        self._reacciones = {"RA": RA, "RB": RB}
        return self._reacciones

    # ----------------------- Construcción simbólica -----------------------

    def _construir_cortante_expr(self) -> sp.Expr:
        """Construye únicamente la expresión simbólica del cortante V(x).

        Se separa para reutilizar tanto en el camino simbólico principal como
        en el *fallback* numérico (vectorizado) evitando recomputaciones.
        """
        reacciones = self.calcular_reacciones()
        V_expr = sp.Float(reacciones["RA"])
        for carga in self.cargas:
            V_expr += carga.shear_expression(x)
        # Reacción derecha: se activa sólo para x > L (Heaviside con valor 0 en x=L)
        V_expr += reacciones["RB"] * heaviside(x - self.longitud)
        return sp.simplify(V_expr)

    def _construir_expresiones(self) -> Dict[str, sp.Expr]:
        """Ensamblado simbólico completo de V, M, θ y y.

        Flujo general:
        1. Construir V(x).
        2. Integrar para M(x) (ruta principal y alternativa).
        3. Integrar M/EI para θ(x) y luego para y(x) (con fallback simplificado).
        4. Aplicar condiciones de borde y(0)=0, y(L)=0.
        """
        if self._expresiones is not None:
            return self._expresiones
        if self.debug:
            print(f"[Viga] Construyendo expresiones simbólicas (L={self.longitud}, cargas={len(self.cargas)})")

        try:
            V_expr = self._construir_cortante_expr()

            xi = sp.symbols("xi", real=True, nonnegative=True)
            try:
                M_expr = sp.integrate(V_expr.subs(x, xi), (xi, 0, x))
                M_expr = sp.simplify(M_expr)
            except Exception as e:
                if self.debug:
                    print(f"[Viga] Advertencia integración momento (método 1): {e}")
                    print("[Viga] Intentando método alternativo...")
                try:
                    M_expr = sp.integrate(V_expr, x)
                    M_expr = M_expr - M_expr.subs(x, 0)
                    M_expr = sp.simplify(M_expr)
                except Exception as e2:
                    if self.debug:
                        print(f"[Viga] Error también en método alternativo de momento: {e2}")
                    raise RuntimeError(f"No se pudo calcular la expresión del momento: {e}")

            # Aportar saltos en M(x) por momentos concentrados: M += M0 * H(x-a)
            # Usamos H(0)=1/2 para una convención explícita en el punto.
            if any(isinstance(c, CargaMomento) for c in self.cargas):
                for c in self.cargas:
                    if isinstance(c, CargaMomento):
                        a = float(c.posicion)
                        # Si el momento está exactamente en un apoyo y en_vano es False, no aplicar el salto dentro del vano
                        if (abs(a - 0.0) < 1e-12 or abs(a - float(self.longitud)) < 1e-12) and not c.en_vano:
                            continue
                        M_expr += sp.Float(c.magnitud) * heaviside_half(x - c.posicion)
                M_expr = sp.simplify(M_expr)

            EI = sp.Float(self.E * self.I)
            if EI == 0:
                raise ValueError("El producto EI no puede ser cero")

            C1, C2 = sp.symbols("C1 C2")
            try:
                theta_expr = sp.integrate(M_expr / EI, x) + C1
                y_expr = sp.integrate(theta_expr, x) + C2
            except Exception as e:
                if self.debug:
                    print(f"[Viga] Advertencia integración deflexión: {e}")
                try:
                    theta_expr = sp.simplify(M_expr / EI) * x + C1
                    y_expr = sp.integrate(theta_expr, x) + C2
                except Exception as e2:
                    if self.debug:
                        print(f"[Viga] Error en alternativa de deflexión: {e2}")
                    raise RuntimeError(f"No se pudo calcular las expresiones de deflexión: {e}")

            ecuaciones = [
                sp.Eq(y_expr.subs(x, 0), 0),
                sp.Eq(y_expr.subs(x, self.longitud), 0),
            ]
            try:
                solucion = sp.solve(ecuaciones, (C1, C2), simplify=True, dict=True)
                if not solucion:
                    raise RuntimeError("No fue posible determinar las constantes de integración")
                constants = solucion[0]
                theta_expr = sp.simplify(theta_expr.subs(constants))
                y_expr = sp.simplify(y_expr.subs(constants))
            except Exception as e:
                if self.debug:
                    print(f"[Viga] Error resolviendo constantes: {e}")
                raise RuntimeError(f"Error al determinar constantes de integración: {e}")

            self._expresiones = {"V": V_expr, "M": M_expr, "theta": theta_expr, "deflexion": y_expr}
            return self._expresiones

        except Exception as e:
            if self.debug:
                print(f"[Viga] Error general construyendo expresiones: {e}")
            raise

    def obtener_expresiones(self) -> Dict[str, sp.Expr]:
        return self._construir_expresiones()

    def evaluar(self, num_puntos: int = 200) -> Dict[str, List[float]]:
        """Evalúa las expresiones simbólicas (o recurre al fallback numérico).

        Devuelve un diccionario con listas (x, V, M, theta, deflexion).

        Parameters
        ----------
        num_puntos : int
            Número de puntos de discretización uniforme en [0, L].
        """
        try:
            expresiones = self._construir_expresiones()
            x_vals = np.linspace(0.0, float(self.longitud), num_puntos)
            if self._lambdas is None:
                self._lambdas = {k: sp.lambdify(x, expr, "numpy") for k, expr in expresiones.items()}
            resultados: Dict[str, List[float]] = {"x": [float(val) for val in x_vals]}
            for clave, func in self._lambdas.items():
                valores = func(x_vals)  # type: ignore[arg-type]
                resultados[clave] = [float(v) for v in np.asarray(valores)]
            return resultados
        except Exception as e:
            if self.debug:
                print(f"[Viga] Advertencia: cambio a fallback numérico ({e})")
            return self._evaluar_numerico(num_puntos)

    def resumen_cargas(self) -> List[str]:
        return [c.descripcion() for c in self.cargas]

    def intensidad_total(self) -> sp.Expr:
        expr = sp.Integer(0)
        for carga in self.cargas:
            expr += carga.load_intensity(x)
        return sp.simplify(expr)

    def _evaluar_numerico(self, num_puntos: int = 200) -> Dict[str, List[float]]:
        """Fallback usando integración numérica vectorizada.

        Construye V(x) simbólica pero sólo la evalúa numéricamente para evitar
        bucles anidados costosos.
        """
        if self.debug:
            print("[Viga] Usando fallback numérico vectorizado")
        from scipy.integrate import cumulative_trapezoid

        x_vals = np.linspace(0.0, float(self.longitud), num_puntos)

        try:
            V_expr = self._construir_cortante_expr()
            V_func = sp.lambdify(x, V_expr, "numpy")
            V_vals = np.asarray(V_func(x_vals), dtype=float)
        except Exception as e:
            # Último recurso: construir manualmente RA + sum(shear_i)
            if self.debug:
                print(f"[Viga] Falla construyendo V_expr ({e}), usando suma incremental")
            reacciones = self.calcular_reacciones()
            V_vals = np.full_like(x_vals, reacciones["RA"], dtype=float)
            for carga in self.cargas:
                try:
                    contrib = sp.lambdify(x, carga.shear_expression(x), "numpy")(x_vals)
                    V_vals += np.asarray(contrib, dtype=float)
                except Exception:
                    continue

        # Integraciones sucesivas
        M_vals = cumulative_trapezoid(V_vals, x_vals, initial=0.0)
        # Añadir saltos por momentos concentrados: M += M0 * H(x-a)
        if any(isinstance(c, CargaMomento) for c in self.cargas):
            for c in self.cargas:
                if isinstance(c, CargaMomento):
                    a = float(c.posicion)
                    # Si es en apoyo y en_vano=False, no afectar el vano
                    if (abs(a - 0.0) < 1e-12 or abs(a - float(self.longitud)) < 1e-12) and not c.en_vano:
                        continue
                    step = (x_vals > a).astype(float)
                    # Si existe un nodo exactamente en a, añadir 1/2 en ese punto para H(0)=1/2
                    eq_mask = np.isclose(x_vals, a)
                    step = step + 0.5 * eq_mask.astype(float)
                    M_vals = M_vals + float(c.magnitud) * step
        EI = self.E * self.I
        theta_vals = cumulative_trapezoid(M_vals / EI, x_vals, initial=0.0)
        y_vals = cumulative_trapezoid(theta_vals, x_vals, initial=0.0)

        # Ajustar condiciones de borde y(0)=y(L)=0
        if len(x_vals) > 1 and abs(y_vals[-1]) > 0:
            Ltot = x_vals[-1]
            y_vals -= (x_vals / Ltot) * y_vals[-1]

        return {
            "x": [float(v) for v in x_vals],
            "V": [float(v) for v in V_vals],
            "M": [float(v) for v in M_vals],
            "theta": [float(v) for v in theta_vals],
            "deflexion": [float(v) for v in y_vals],
        }

# Fin del módulo
