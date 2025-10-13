"""
============================================================
MODELADO DE VIGAS - ANÁLISIS ESTRUCTURAL
============================================================

Este archivo contiene el núcleo matemático del analizador de vigas.

CLASES PRINCIPALES:
-------------------
  Carga → Clase base para todos los tipos de carga
      ├── CargaPuntual → Fuerza concentrada (P en x=a)
      ├── CargaMomento → Par aplicado (M₀ en x=a)
      ├── CargaUniforme → w constante en [a,b]
      ├── CargaTriangular → w variable linealmente (caso especial trapezoidal)
      └── CargaTrapezoidal → w₁ → w₂ en [a,b]
  
  Apoyo → Representa un punto de soporte de la viga
  
  Viga → Modelo completo que calcula:
      • Reacciones en apoyos (equilibrio estático)
      • Cortante V(x)
      • Momento M(x)
      • Pendiente θ(x)
      • Deflexión y(x)

CONVENCIONES DE SIGNO:
---------------------
  • Cargas hacia ABAJO → magnitud POSITIVA
  • V(x) positivo → cortante hacia ARRIBA a la izquierda
  • M(x) positivo → fibras superiores en COMPRESIÓN
  • Momento concentrado POSITIVO → sentido ANTIHORARIO ↺
  • Momento concentrado NEGATIVO → sentido HORARIO ↻

MÉTODO DE CÁLCULO:
------------------
1. Reacciones:
   - Isostático (2 apoyos): ΣFy=0, ΣMA=0
   - Hiperestático (3+ apoyos): Método de flexibilidad

2. Cortante V(x):
   Se construye usando funciones de Heaviside/Macaulay
   V(x) = RA + Σ(efectos de cargas)

3. Momento M(x):
   M(x) = ∫ V(ξ)dξ + Σ(saltos por momentos)

4. Deflexión y(x):
   EI·y'' = M(x)
   θ(x) = ∫ M/(EI) dx
   y(x) = ∫ θ dx
   Con condiciones: y(apoyo_i) = 0

Si la integración simbólica falla, usa método numérico
(integración trapezoidal) como respaldo.

HIPÓTESIS DEL MODELO:
--------------------
  • Teoría de Euler-Bernoulli (vigas esbeltas)
  • Material lineal elástico (E constante)
  • Momento de inercia constante (I)
  • Pequeñas deformaciones
============================================================
"""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import sympy as sp

if TYPE_CHECKING:
    from backend.calculos import generar_dataframe

# Clases exportadas (disponibles cuando se importa este módulo)
__all__ = [
    'Carga',
    'CargaPuntual',
    'CargaMomento',
    'CargaUniforme',
    'CargaTriangular',
    'CargaTrapezoidal',
    'Apoyo',
    'Viga',
    'heaviside',
    'heaviside_half',
    'macaulay',
]

# Variable simbólica para posición a lo largo de la viga
x = sp.symbols("x", real=True, nonnegative=True)


# ============================================================
# FUNCIONES MATEMÁTICAS (Heaviside y Macaulay)
# ============================================================
# Estas funciones permiten construir expresiones matemáticas
# que cambian en puntos específicos, muy útil para vigas

def heaviside(val: sp.Expr) -> sp.Heaviside:
    """
    Función escalón de Heaviside: H(x-a)
    
    Retorna 0 si x < a, y 1 si x ≥ a
    Usado para "activar" efectos después de cierta posición
    
    Ejemplo: Una carga que empieza en x=2
             H(x-2) = 0 para x<2, H(x-2) = 1 para x≥2
    """
    return sp.Heaviside(val, 0)


def heaviside_half(val: sp.Expr) -> sp.Heaviside:
    """
    Función Heaviside con valor 1/2 en x=a
    
    Usada para momentos concentrados donde se evalúa
    exactamente en el punto de aplicación.
    """
    return sp.Heaviside(val, sp.Rational(1, 2))


def macaulay(variable: sp.Symbol, offset: float, exponent: int) -> sp.Expr:
    """
    Notación de Macaulay: <x - a>^n
    
    Representa (x - a)^n solo cuando x > a, y 0 cuando x ≤ a
    
    Muy útil para cargas distribuidas que empiezan en x=a
    
    Ejemplo:
        macaulay(x, 2, 1) = 0 si x<2, (x-2) si x≥2
        macaulay(x, 2, 2) = 0 si x<2, (x-2)² si x≥2
    """
    return sp.Pow(variable - offset, exponent) * heaviside(variable - offset)


def _import_generar_dataframe():
    """Importa función generar_dataframe cuando se necesita (evita problemas circulares)."""
    try:
        from backend.calculos import generar_dataframe
        return generar_dataframe
    except ImportError as e:
        raise ImportError(
            f"No se pudo importar generar_dataframe: {e}. "
            "Asegúrate de que backend/calculos.py esté disponible."
        )


# ============================================================
# CLASE BASE: CARGA
# ============================================================

@dataclass
class Carga:
    """
    Clase base para todos los tipos de carga.
    
    Cada tipo específico de carga (puntual, uniforme, etc.)
    hereda de esta clase e implementa:
      - total_load(): Fuerza total equivalente
      - moment_about(): Momento respecto a un punto
      - shear_expression(): Contribución al cortante V(x)
      - load_intensity(): Intensidad q(x) para cargas distribuidas
    """

    def total_load(self) -> float:
        """Retorna la carga total en Newtons."""
        raise NotImplementedError

    def moment_about(self, origen: float = 0.0) -> float:
        """Retorna el momento de la carga respecto a un punto dado."""
        raise NotImplementedError

    def shear_expression(self, variable: sp.Symbol = x) -> sp.Expr:
        """Retorna la expresión matemática de cómo afecta al cortante V(x)."""
        raise NotImplementedError

    def load_intensity(self, variable: sp.Symbol = x) -> sp.Expr:
        """
        Retorna la intensidad de carga q(x).
        Para cargas puntuales retorna 0 (no tienen distribución continua).
        """
        return sp.Integer(0)

    def descripcion(self) -> str:
        """Texto descriptivo de la carga para mostrar al usuario."""
        return self.__class__.__name__


# ============================================================
# CARGA PUNTUAL: Fuerza concentrada en un punto
# ============================================================

@dataclass
class CargaPuntual(Carga):
    """
    Carga puntual: Fuerza P aplicada en posición x=a
    
    Ejemplo: Una persona de 70 kg parada en x=2.5m
             P = 70 × 9.81 = 686.7 N en posición 2.5 m
    
    Efectos:
      • Introduce salto en V(x) de magnitud P
      • Cambia pendiente de M(x)
    """
    magnitud: float      # Fuerza en Newtons (positivo = hacia abajo)
    posicion: float      # Posición en metros
    units: str | None = None  # Opcional: conversión automática desde 'kgf' o 'kg'

    def __post_init__(self) -> None:
        # Conversión automática de masa a fuerza (kg → N)
        if self.units:
            u = self.units.lower()
            if u in {"kgf", "kg"}:
                self.magnitud *= 9.81  # Convertir a Newtons
        
        # Validaciones
        if self.posicion < 0:
            raise ValueError("La posición debe ser no negativa")
        if abs(self.magnitud) < 1e-12:
            raise ValueError("La magnitud debe ser significativa")

    def total_load(self) -> float:
        return float(self.magnitud)

    def moment_about(self, origen: float = 0.0) -> float:
        """Momento = Fuerza × distancia al origen"""
        distancia = self.posicion - origen
        return float(self.magnitud * distancia)

    def shear_expression(self, variable: sp.Symbol = x) -> sp.Expr:
        """
        La carga introduce salto negativo en V(x).
        Usa Heaviside para activar después de x=posicion
        """
        return -self.magnitud * heaviside(variable - self.posicion)

    def descripcion(self) -> str:
        return f"Carga puntual P={self.magnitud:.3g} N en x={self.posicion:.3g} m"


# ============================================================
# MOMENTO PUNTUAL: Par concentrado
# ============================================================

@dataclass
class CargaMomento(Carga):
    """
    Momento concentrado (par) aplicado en x=a
    
    CONVENCIÓN DE SIGNO:
      • Magnitud POSITIVA → Sentido ANTIHORARIO ↺ (levanta lado derecho)
      • Magnitud NEGATIVA → Sentido HORARIO ↻ (baja lado derecho)
    
    Ejemplo:
      M = +500 N·m en x=3m → Momento antihorario que levanta la viga a la derecha
      M = -500 N·m en x=3m → Momento horario que baja la viga a la derecha
    
    Efectos estructurales:
      • NO cambia V(x) (no hay fuerza vertical)
      • Introduce salto POSITIVO en M(x) si M > 0
      • Introduce salto NEGATIVO en M(x) si M < 0
    
    Nota: Si el momento está exactamente en un apoyo,
    'en_vano' determina si afecta dentro del vano o solo las reacciones
    """
    magnitud: float      # Momento en N·m (positivo=↺, negativo=↻)
    posicion: float      # Posición en metros
    en_vano: bool = True  # Si False en apoyo, no produce salto en M(x)

    def __post_init__(self) -> None:
        if self.posicion < 0:
            raise ValueError("La posición debe ser no negativa")
        if abs(self.magnitud) < 1e-12:
            raise ValueError("La magnitud del momento debe ser significativa")

    def total_load(self) -> float:
        """Un momento puro no tiene fuerza vertical neta."""
        return 0.0

    def moment_about(self, origen: float = 0.0) -> float:
        """
        Un par es un vector libre: su efecto es el mismo
        sin importar el punto de referencia.
        
        Para equilibrio de momentos:
          ΣM = 0 → El momento entra con su signo
          Positivo contribuye antihorario
          Negativo contribuye horario
        """
        return float(self.magnitud)

    def shear_expression(self, variable: sp.Symbol = x) -> sp.Expr:
        """Un momento concentrado no altera V(x)."""
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
class Apoyo:
    """Representa un apoyo simple en una posición específica de la viga.
    
    Attributes
    ----------
    posicion : float
        Posición del apoyo en metros desde el origen.
    nombre : str
        Identificador del apoyo (ej: 'A', 'B', 'C').
    """
    posicion: float
    nombre: str = ""
    
    def __post_init__(self) -> None:
        if self.posicion < 0:
            raise ValueError("La posición del apoyo debe ser no negativa")
        if not self.nombre:
            self.nombre = f"R_{self.posicion:.2f}"


@dataclass
class Viga:
    """Modelo de una viga simplemente apoyada con apoyos configurables.

    Aporta métodos para construir expresiones simbólicas de cortante, momento,
    pendiente y deflexión. Si el proceso simbólico falla, existe un *fallback*
    numérico vectorizado.
    
    Attributes
    ----------
    longitud : float
        Longitud total de la viga en metros.
    E : float
        Módulo de elasticidad en Pa.
    I : float
        Momento de inercia en m⁴.
    apoyos : List[Apoyo]
        Lista de apoyos. Por defecto se crean en x=0 y x=L.
    cargas : List[Carga]
        Lista de cargas aplicadas.
    debug : bool
        Activar mensajes de depuración.
    """

    longitud: float
    E: float
    I: float
    apoyos: List[Apoyo] = field(default_factory=list)
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
        
        # Si no se especifican apoyos, crear apoyos por defecto en extremos
        if not self.apoyos:
            self.apoyos = [
                Apoyo(posicion=0.0, nombre="A"),
                Apoyo(posicion=self.longitud, nombre="B")
            ]
        else:
            # Validar que los apoyos estén dentro de la viga
            for apoyo in self.apoyos:
                if apoyo.posicion > self.longitud:
                    raise ValueError(
                        f"El apoyo '{apoyo.nombre}' en x={apoyo.posicion} está fuera de la viga (L={self.longitud})"
                    )
            
            # Validar duplicados en apoyos iniciales
            for i, apoyo in enumerate(self.apoyos):
                for otro in self.apoyos[i+1:]:
                    if abs(apoyo.posicion - otro.posicion) < 1e-3:
                        raise ValueError(
                            f"Los apoyos '{apoyo.nombre}' y '{otro.nombre}' están muy cercanos "
                            f"(distancia={abs(apoyo.posicion - otro.posicion)*1000:.3f} mm, mínimo=1.0 mm)"
                        )
            
            # Ordenar apoyos por posición
            self.apoyos.sort(key=lambda a: a.posicion)
    
    def _validar_apoyo_duplicado(self, nueva_posicion: float, nuevo_nombre: str = "") -> None:
        """Verifica que no haya apoyos muy cercanos (< 1mm).
        
        Parameters
        ----------
        nueva_posicion : float
            Posición del nuevo apoyo a validar.
        nuevo_nombre : str, optional
            Nombre del nuevo apoyo (para mensajes de error).
        
        Raises
        ------
        ValueError
            Si ya existe un apoyo muy cercano a la posición dada.
        """
        for apoyo_existente in self.apoyos:
            distancia_mm = abs(apoyo_existente.posicion - nueva_posicion) * 1000
            if distancia_mm < 1.0:
                nombre_info = f"'{nuevo_nombre}' " if nuevo_nombre else ""
                raise ValueError(
                    f"Ya existe el apoyo '{apoyo_existente.nombre}' muy cercano a la posición {nombre_info}"
                    f"x={nueva_posicion:.6f} m (distancia={distancia_mm:.3f} mm, mínimo=1.0 mm)"
                )
    
    def agregar_apoyo(self, apoyo: Apoyo) -> None:
        """Agrega un apoyo verificando que esté dentro del dominio de la viga.
        
        Resetea las cachés de resultados para asegurar coherencia.
        """
        if apoyo.posicion > self.longitud:
            raise ValueError(
                f"El apoyo '{apoyo.nombre}' en x={apoyo.posicion} está fuera de la viga (L={self.longitud})"
            )
        
        # Verificar que no haya un apoyo muy cercano usando método unificado
        self._validar_apoyo_duplicado(apoyo.posicion, apoyo.nombre)
        
        self.apoyos.append(apoyo)
        self.apoyos.sort(key=lambda a: a.posicion)
        
        # Invalidar cachés
        self._reacciones = None
        self._expresiones = None
        self._lambdas = None
    
    def limpiar_apoyos(self) -> None:
        """Elimina todos los apoyos e invalida cachés."""
        self.apoyos.clear()
        self._reacciones = None
        self._expresiones = None
        self._lambdas = None

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

    def tipo_sistema(self) -> str:
        """Determina el tipo de sistema estructural.
        
        Returns
        -------
        str: 'hipostatico', 'isostatico', o 'hiperestatico'
        """
        n_apoyos = len(self.apoyos)
        n_ecuaciones = 2  # Equilibrio vertical y momento
        n_incognitas = n_apoyos  # Reacciones verticales
        
        if n_incognitas < n_ecuaciones:
            return "hipostatico"  # Inestable, insuficientes apoyos
        elif n_incognitas == n_ecuaciones:
            return "isostatico"  # Estáticamente determinado
        else:
            return "hiperestatico"  # Estáticamente indeterminado
    
    def grado_hiperestaticidad(self) -> int:
        """Retorna el grado de hiperestaticidad del sistema.
        
        Returns
        -------
        int: 0 para isostático, <0 para hipostático, >0 para hiperestático
        """
        n_apoyos = len(self.apoyos)
        n_ecuaciones = 2  # Equilibrio para viga en 2D
        return n_apoyos - n_ecuaciones
    
    def validar_sistema(self) -> Dict[str, Any]:
        """Valida el sistema estructural y retorna información de diagnóstico.
        
        Returns
        -------
        dict: {
            'valido': bool,
            'tipo': str,
            'grado': int,
            'mensajes': List[str],
            'advertencias': List[str]
        }
        """
        resultado = {
            'valido': True,
            'tipo': self.tipo_sistema(),
            'grado': self.grado_hiperestaticidad(),
            'mensajes': [],
            'advertencias': []
        }
        
        n_apoyos = len(self.apoyos)
        
        if n_apoyos == 0:
            resultado['valido'] = False
            resultado['mensajes'].append("❌ No hay apoyos definidos")
            return resultado
        
        if n_apoyos == 1:
            resultado['advertencias'].append("⚠️ Sistema hipostático (1 apoyo). Solo se puede analizar como ménsula si hay empotramiento")
        
        if resultado['tipo'] == 'hipostatico':
            resultado['valido'] = False
            resultado['mensajes'].append(f"❌ Sistema hipostático: insuficientes apoyos ({n_apoyos} < 2)")
        elif resultado['tipo'] == 'isostatico':
            resultado['mensajes'].append(f"✓ Sistema isostático: {n_apoyos} apoyos (estáticamente determinado)")
        else:  # hiperestatico
            grado = resultado['grado']
            resultado['mensajes'].append(f"✓ Sistema hiperestático de grado {grado}: {n_apoyos} apoyos")
            resultado['advertencias'].append(f"ℹ️ Se resolverá por método de compatibilidad de deflexiones")
        
        # Verificar separación mínima entre apoyos
        for i in range(len(self.apoyos) - 1):
            dist = self.apoyos[i+1].posicion - self.apoyos[i].posicion
            if dist < 1e-3:
                resultado['advertencias'].append(
                    f"⚠️ Apoyos '{self.apoyos[i].nombre}' y '{self.apoyos[i+1].nombre}' muy cercanos (d={dist*1000:.2f} mm)"
                )
        
        # Verificar que haya cargas
        if not self.cargas:
            resultado['advertencias'].append("⚠️ No hay cargas aplicadas")
        
        return resultado
    
    def calcular_reacciones(self) -> Dict[str, float]:
        """Calcula y memoriza las reacciones en todos los apoyos.

        Para 1 apoyo: ménsula (hipostático sin empotramiento)
        Para 2 apoyos: equilibrio estático (isostático)
        Para n>2 apoyos: método de flexibilidad con compatibilidad de deflexiones
        
        El método general para sistemas hiperestáticos:
        1. Selecciona apoyos extremos como primarios (isostático base)
        2. Los apoyos intermedios son redundantes
        3. Calcula deflexiones en apoyos redundantes debido a cargas
        4. Aplica fuerzas unitarias en redundantes y calcula coeficientes de flexibilidad
        5. Resuelve sistema: [δ] = [f]·{R_redundantes} + {δ_cargas}
        6. Impone δ = 0 en apoyos reales

        Returns
        -------
        dict: {nombre_apoyo: reaccion_en_N, ...}
        """
        if self._reacciones is not None:
            return self._reacciones
        
        n_apoyos = len(self.apoyos)
        if n_apoyos == 0:
            raise ValueError("La viga debe tener al menos un apoyo")
        
        tipo = self.tipo_sistema()
        
        if n_apoyos == 1:
            # Caso especial: un solo apoyo (sistema hipostático sin momento)
            # Solo puede equilibrar si todas las cargas pasan por el apoyo
            suma_cargas = sum(c.total_load() for c in self.cargas)
            self._reacciones = {self.apoyos[0].nombre: suma_cargas}
            
            if self.debug:
                print(f"[Viga] Sistema con 1 apoyo (hipostático): R={suma_cargas:.3f} N")
            return self._reacciones
        
        if n_apoyos == 2:
            # Caso simple: dos apoyos (estáticamente determinado)
            apoyo_izq = self.apoyos[0]
            apoyo_der = self.apoyos[1]
            
            suma_cargas = sum(c.total_load() for c in self.cargas)
            
            # Momentos respecto al apoyo izquierdo
            momentos = sum(c.moment_about(apoyo_izq.posicion) for c in self.cargas)
            
            distancia = apoyo_der.posicion - apoyo_izq.posicion
            if abs(distancia) < 1e-12:
                raise ValueError("Los apoyos están demasiado cerca")
            
            R_der = momentos / distancia
            R_izq = suma_cargas - R_der
            
            self._reacciones = {
                apoyo_izq.nombre: R_izq,
                apoyo_der.nombre: R_der
            }
            
            if self.debug:
                print(f"[Viga] Sistema isostático: R_{apoyo_izq.nombre}={R_izq:.3f} N, R_{apoyo_der.nombre}={R_der:.3f} N")
            
            return self._reacciones
        
        # Caso general: n apoyos (n >= 3) - estáticamente indeterminado (hiperestático)
        # Método de compatibilidad: usar apoyos extremos como sistema primario
        
        if self.debug:
            print(f"[Viga] Sistema hiperestático con {n_apoyos} apoyos (grado {n_apoyos - 2})")
        
        try:
            import numpy as np
            from scipy.integrate import quad
            
            # Identificar apoyos primarios (extremos) y redundantes (intermedios)
            apoyo_izq = self.apoyos[0]
            apoyo_der = self.apoyos[-1]
            apoyos_redundantes = self.apoyos[1:-1]  # Apoyos intermedios
            n_redundantes = len(apoyos_redundantes)
            
            if self.debug:
                print(f"[Viga] Apoyos primarios: {apoyo_izq.nombre} (x={apoyo_izq.posicion}), {apoyo_der.nombre} (x={apoyo_der.posicion})")
                print(f"[Viga] Apoyos redundantes: {[f'{a.nombre} (x={a.posicion})' for a in apoyos_redundantes]}")
            
            # Paso 1: Calcular reacciones del sistema primario (solo extremos) con todas las cargas
            viga_primaria = Viga(self.longitud, self.E, self.I, 
                               apoyos=[apoyo_izq, apoyo_der],
                               debug=False)
            for carga in self.cargas:
                viga_primaria.agregar_carga(carga)
            
            reacciones_primarias = viga_primaria.calcular_reacciones()
            
            # Paso 2: Calcular deflexiones en posiciones de apoyos redundantes (sistema primario con cargas)
            try:
                generar_dataframe = _import_generar_dataframe()
                df_primario = generar_dataframe(viga_primaria, num_puntos=1000)
            except (ImportError, Exception):
                # Fallback: evaluar numéricamente
                resultados_primarios = viga_primaria._evaluar_numerico(1000)
                df_primario = pd.DataFrame(resultados_primarios)
            
            # Interpolar deflexiones en posiciones de apoyos redundantes
            deflexiones_cargas = np.zeros(n_redundantes)
            for i, apoyo_red in enumerate(apoyos_redundantes):
                # Encontrar deflexión en la posición del apoyo redundante
                idx = np.argmin(np.abs(df_primario['x'].to_numpy() - apoyo_red.posicion))
                deflexiones_cargas[i] = df_primario.iloc[idx]['deflexion']
            
            if self.debug:
                print(f"[Viga] Deflexiones por cargas en redundantes: {deflexiones_cargas}")
            
            # Paso 3: Calcular coeficientes de flexibilidad
            # f_ij = deflexión en apoyo i debido a reacción unitaria hacia arriba en apoyo j
            matriz_flexibilidad = np.zeros((n_redundantes, n_redundantes))
            
            for j, apoyo_j in enumerate(apoyos_redundantes):
                # Aplicar reacción unitaria hacia arriba en apoyo j
                # (carga hacia abajo negativa equivale a reacción hacia arriba)
                viga_unitaria = Viga(self.longitud, self.E, self.I,
                                   apoyos=[apoyo_izq, apoyo_der],
                                   debug=False)
                carga_unitaria = CargaPuntual(magnitud=-1.0, posicion=apoyo_j.posicion)
                viga_unitaria.agregar_carga(carga_unitaria)
                
                try:
                    generar_dataframe = _import_generar_dataframe()
                    df_unit = generar_dataframe(viga_unitaria, num_puntos=1000)
                except (ImportError, Exception):
                    resultados_unit = viga_unitaria._evaluar_numerico(1000)
                    df_unit = pd.DataFrame(resultados_unit)
                
                # Calcular deflexiones en todos los apoyos redundantes
                for i, apoyo_i in enumerate(apoyos_redundantes):
                    idx = np.argmin(np.abs(df_unit['x'].to_numpy() - apoyo_i.posicion))
                    matriz_flexibilidad[i, j] = df_unit.iloc[idx]['deflexion']
            
            if self.debug:
                print(f"[Viga] Matriz de flexibilidad:\n{matriz_flexibilidad}")
            
            # Paso 4: Resolver sistema [f]·{R_redundantes} = -{δ_cargas}
            # (negativo porque queremos que la suma dé cero)
            reacciones_redundantes = np.linalg.solve(matriz_flexibilidad, -deflexiones_cargas)
            
            if self.debug:
                print(f"[Viga] Reacciones redundantes: {reacciones_redundantes}")
            
            # Paso 5: Calcular reacciones finales en apoyos primarios
            # Superposición: reacciones totales = reacciones_primarias + efecto de redundantes
            
            # Las reacciones redundantes son positivas hacia arriba
            # Necesitamos calcular su efecto en los apoyos extremos
            # Creamos cargas hacia abajo que representan estas reacciones
            viga_redundantes = Viga(self.longitud, self.E, self.I,
                                  apoyos=[apoyo_izq, apoyo_der],
                                  debug=False)
            for i, apoyo_red in enumerate(apoyos_redundantes):
                # Convertir reacción (hacia arriba, positiva) en carga equivalente (hacia abajo, negativa)
                # Magnitud negativa en CargaPuntual equivale a reacción hacia arriba
                carga_equivalente = CargaPuntual(magnitud=-reacciones_redundantes[i], 
                                               posicion=apoyo_red.posicion)
                viga_redundantes.agregar_carga(carga_equivalente)
            
            reacciones_por_redundantes = viga_redundantes.calcular_reacciones()
            
            # Superposición final: 
            # R_extremos_total = R_por_cargas_externas + R_por_reacciones_internas
            # (sumamos porque ya aplicamos signo negativo en las cargas equivalentes)
            R_izq_total = reacciones_primarias[apoyo_izq.nombre] + reacciones_por_redundantes[apoyo_izq.nombre]
            R_der_total = reacciones_primarias[apoyo_der.nombre] + reacciones_por_redundantes[apoyo_der.nombre]
            
            # Construir diccionario de reacciones completo
            self._reacciones = {
                apoyo_izq.nombre: R_izq_total,
                apoyo_der.nombre: R_der_total
            }
            
            # Las reacciones redundantes son positivas (hacia arriba)
            for i, apoyo_red in enumerate(apoyos_redundantes):
                self._reacciones[apoyo_red.nombre] = float(reacciones_redundantes[i])
            
            if self.debug:
                print(f"[Viga] Reacciones finales: {self._reacciones}")
                suma_reacciones = sum(self._reacciones.values())
                suma_cargas_total = sum(c.total_load() for c in self.cargas)
                print(f"[Viga] Verificación: ΣR={suma_reacciones:.6f} N, ΣF={suma_cargas_total:.6f} N, error={abs(suma_reacciones - suma_cargas_total):.6e} N")
            
            return self._reacciones
            
        except Exception as e:
            if self.debug:
                import traceback
                print(f"[Viga] Error calculando reacciones hiperestáticas: {e}")
                traceback.print_exc()
            raise RuntimeError(f"No se pudieron calcular las reacciones hiperestáticas: {e}")

    # ----------------------- Construcción simbólica -----------------------

    def _construir_cortante_expr(self) -> sp.Expr:
        """Construye únicamente la expresión simbólica del cortante V(x).

        Se separa para reutilizar tanto en el camino simbólico principal como
        en el *fallback* numérico (vectorizado) evitando recomputaciones.
        """
        reacciones = self.calcular_reacciones()
        
        # Comenzar con la primera reacción (apoyo más a la izquierda)
        if self.apoyos:
            primer_apoyo = self.apoyos[0]
            V_expr = sp.Float(reacciones[primer_apoyo.nombre])
        else:
            V_expr = sp.Float(0.0)
        
        # Agregar contribuciones de las cargas
        for carga in self.cargas:
            V_expr += carga.shear_expression(x)
        
        # Agregar reacciones de los demás apoyos (activan con Heaviside)
        for apoyo in self.apoyos[1:]:
            V_expr += reacciones[apoyo.nombre] * heaviside(x - apoyo.posicion)
        
        return sp.simplify(V_expr)

    def _construir_expresiones(self) -> Dict[str, sp.Expr]:
        """Ensamblado simbólico completo de V, M, θ y y.

        Flujo general:
        1. Construir V(x).
        2. Integrar para M(x) (ruta principal y alternativa).
        3. Integrar M/EI para θ(x) y luego para y(x) (con fallback simplificado).
        4. Aplicar condiciones de borde y(x_apoyo_i)=0 para todos los apoyos.
        """
        if self._expresiones is not None:
            return self._expresiones
        if self.debug:
            print(f"[Viga] Construyendo expresiones simbólicas (L={self.longitud}, cargas={len(self.cargas)}, apoyos={len(self.apoyos)})")

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

            # ============================================================
            # SALTOS EN M(x) POR MOMENTOS CONCENTRADOS
            # ============================================================
            # Relación: M(x) = ∫V(x)dx + Σ[M₀·H(x-a)]
            #
            # CONVENCIÓN DE SIGNOS (según mecánica de materiales):
            #   M₀ > 0 (antihorario ↺):
            #     • A la IZQUIERDA de x=a: M(x) no cambia
            #     • A la DERECHA de x=a: M(x) aumenta en +M₀
            #     • Efecto: Salta hacia ARRIBA en diagrama
            #
            #   M₀ < 0 (horario ↻):
            #     • A la IZQUIERDA de x=a: M(x) no cambia  
            #     • A la DERECHA de x=a: M(x) disminuye en M₀
            #     • Efecto: Salta hacia ABAJO en diagrama
            #
            # Usamos H(0)=1/2 para evaluar correctamente en x=a
            # ============================================================
            if any(isinstance(c, CargaMomento) for c in self.cargas):
                for c in self.cargas:
                    if isinstance(c, CargaMomento):
                        a = float(c.posicion)
                        # Si el momento está exactamente en un apoyo y en_vano es False, no aplicar el salto dentro del vano
                        esta_en_apoyo = any(abs(a - apoyo.posicion) < 1e-12 for apoyo in self.apoyos)
                        if esta_en_apoyo and not c.en_vano:
                            continue
                        M_expr += sp.Float(c.magnitud) * heaviside_half(x - c.posicion)
                M_expr = sp.simplify(M_expr)

            EI = sp.Float(self.E * self.I)
            if EI == 0:
                raise ValueError("El producto EI no puede ser cero")

            # Para 2 apoyos: usar C1, C2 y resolver con y(apoyo1)=0, y(apoyo2)=0
            # Para n>2 apoyos: necesitamos n constantes o usar método simplificado
            
            n_apoyos = len(self.apoyos)
            
            if n_apoyos <= 2:
                # Caso clásico con 2 constantes
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

                # Aplicar condiciones de borde en los apoyos disponibles
                ecuaciones = []
                for apoyo in self.apoyos[:2]:  # Usar los primeros 2 apoyos
                    ecuaciones.append(sp.Eq(y_expr.subs(x, apoyo.posicion), 0))
                
                # Si solo hay 1 apoyo, agregar condición de momento nulo ahí
                if n_apoyos == 1:
                    ecuaciones.append(sp.Eq(M_expr.subs(x, self.apoyos[0].posicion), 0))
                
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
            
            else:
                # Para n>2 apoyos: resolver sistema con más constantes o usar método numérico
                # Por simplicidad, usamos método numérico directo
                if self.debug:
                    print("[Viga] Sistema con >2 apoyos: usando integración numérica directa")
                raise RuntimeError("Sistema con >2 apoyos: se requiere método numérico")

            self._expresiones = {"V": V_expr, "M": M_expr, "theta": theta_expr, "deflexion": y_expr}
            return self._expresiones

        except Exception as e:
            if self.debug:
                print(f"[Viga] Error general construyendo expresiones: {e}")
            raise

    def obtener_expresiones(self) -> Dict[str, sp.Expr]:
        return self._construir_expresiones()

    def evaluar(self, num_puntos: int = 400) -> Dict[str, List[float]]:
        """Evalúa las expresiones simbólicas (o recurre al fallback numérico).

        Devuelve un diccionario con listas (x, V, M, theta, deflexion).

        Parameters
        ----------
        num_puntos : int
            Número de puntos de discretización uniforme en [0, L].
            Por defecto 400 (suficiente precisión para momentos concentrados).
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

    def _evaluar_numerico(self, num_puntos: int = 400) -> Dict[str, List[float]]:
        """Fallback usando integración numérica vectorizada.

        Construye V(x) simbólica pero sólo la evalúa numéricamente para evitar
        bucles anidados costosos.
        
        Parameters
        ----------
        num_puntos : int
            Número de puntos de discretización. Por defecto 400 para
            precisión adecuada en discontinuidades (momentos concentrados).
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
            # Último recurso: construir manualmente R_primer_apoyo + sum(shear_i) + otras reacciones
            if self.debug:
                print(f"[Viga] Falla construyendo V_expr ({e}), usando suma incremental")
            reacciones = self.calcular_reacciones()
            
            if self.apoyos:
                V_vals = np.full_like(x_vals, reacciones[self.apoyos[0].nombre], dtype=float)
            else:
                V_vals = np.zeros_like(x_vals, dtype=float)
            
            for carga in self.cargas:
                try:
                    contrib = sp.lambdify(x, carga.shear_expression(x), "numpy")(x_vals)
                    V_vals += np.asarray(contrib, dtype=float)
                except Exception:
                    continue
            
            # Agregar reacciones de apoyos restantes
            for apoyo in self.apoyos[1:]:
                step = (x_vals >= apoyo.posicion).astype(float)
                V_vals += reacciones[apoyo.nombre] * step

        # Integraciones sucesivas: M(x) = ∫V(x)dx
        M_vals = cumulative_trapezoid(V_vals, x_vals, initial=0.0)
        
        # ============================================================
        # AÑADIR SALTOS POR MOMENTOS CONCENTRADOS (método numérico)
        # ============================================================
        # Mismo principio que el método simbólico:
        #   M(x) = M_base(x) + M₀·H(x-a)
        #
        # Para x < a: H(x-a) = 0 → sin cambio
        # Para x = a: H(x-a) = 0.5 → mitad del salto
        # Para x > a: H(x-a) = 1 → salto completo
        #
        # Resultado visual en diagrama:
        #   M₀ > 0 → Salto hacia ARRIBA
        #   M₀ < 0 → Salto hacia ABAJO
        # ============================================================
        if any(isinstance(c, CargaMomento) for c in self.cargas):
            for c in self.cargas:
                if isinstance(c, CargaMomento):
                    a = float(c.posicion)
                    # Si es en apoyo y en_vano=False, no afectar el vano
                    esta_en_apoyo = any(abs(a - apoyo.posicion) < 1e-12 for apoyo in self.apoyos)
                    if esta_en_apoyo and not c.en_vano:
                        continue
                    
                    # Función escalón de Heaviside: H(x-a)
                    # = 0 si x < a
                    # = 0.5 si x = a (dentro de tolerancia)
                    # = 1 si x > a
                    step = np.zeros_like(x_vals, dtype=float)
                    
                    # Identificar regiones
                    mask_antes = x_vals < (a - 1e-9)  # Antes del momento
                    mask_exacto = np.abs(x_vals - a) <= 1e-9  # En el momento (tolerancia muy pequeña)
                    mask_despues = x_vals > (a + 1e-9)  # Después del momento
                    
                    # Asignar valores de Heaviside
                    step[mask_antes] = 0.0
                    step[mask_exacto] = 0.5
                    step[mask_despues] = 1.0
                    
                    # Aplicar salto con el signo del momento
                    M_vals = M_vals + float(c.magnitud) * step
        
        EI = self.E * self.I
        theta_vals = cumulative_trapezoid(M_vals / EI, x_vals, initial=0.0)
        y_vals = cumulative_trapezoid(theta_vals, x_vals, initial=0.0)

        # Ajustar condiciones de borde y(x_apoyo_i)=0 para todos los apoyos
        if len(self.apoyos) >= 2:
            # Para 2 apoyos: ajuste lineal
            apoyo1 = self.apoyos[0]
            apoyo2 = self.apoyos[1]
            
            # Encontrar índices más cercanos a los apoyos
            idx1 = np.argmin(np.abs(x_vals - apoyo1.posicion))
            idx2 = np.argmin(np.abs(x_vals - apoyo2.posicion))
            
            # Corrección lineal para forzar y=0 en ambos apoyos
            y1 = y_vals[idx1]
            y2 = y_vals[idx2]
            
            x1 = x_vals[idx1]
            x2 = x_vals[idx2]
            
            if abs(x2 - x1) > 1e-12:
                # Ajuste lineal: y_corregido = y - (y1 + (y2-y1)/(x2-x1) * (x-x1))
                pendiente = (y2 - y1) / (x2 - x1)
                y_vals = y_vals - (y1 + pendiente * (x_vals - x1))
        elif len(self.apoyos) == 1:
            # Un solo apoyo: ajustar para y=0 en ese apoyo
            idx = np.argmin(np.abs(x_vals - self.apoyos[0].posicion))
            y_vals = y_vals - y_vals[idx]

        return {
            "x": [float(v) for v in x_vals],
            "V": [float(v) for v in V_vals],
            "M": [float(v) for v in M_vals],
            "theta": [float(v) for v in theta_vals],
            "deflexion": [float(v) for v in y_vals],
        }

# Fin del módulo
