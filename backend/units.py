"""
============================================================
CONVERSIÓN DE UNIDADES
============================================================

¿Qué hace este archivo?
- Define factores de conversión entre diferentes sistemas de unidades
- Todo el cálculo interno usa SI (Sistema Internacional)
- La interfaz puede mostrar resultados en otras unidades

Unidades SI utilizadas:
  - Longitud → metros (m)
  - Fuerza → Newtons (N)
  - Presión → Pascales (Pa)
  - Inercia → metros⁴ (m⁴)
============================================================
"""
from functools import lru_cache
from typing import Dict

# ============================================================
# FACTORES DE CONVERSIÓN A SI
# ============================================================
# Para convertir a SI: valor_usuario × factor = valor_SI
# Para mostrar desde SI: valor_SI ÷ factor = valor_mostrado

LENGTH_UNITS: Dict[str, float] = {
    "m": 1.0,        # Metro (base SI)
    "ft": 0.3048     # Pie = 0.3048 metros
}

FORCE_UNITS: Dict[str, float] = {
    "N": 1.0,                    # Newton (base SI)
    "kN": 1e3,                   # Kilonewton = 1000 N
    "lb": 4.4482216153,          # Libra-fuerza
    "kgf": 9.81                  # Kilogramo-fuerza (masa × g)
}

DIST_LOAD_UNITS: Dict[str, float] = {
    "N/m": 1.0,
    "kN/m": 1e3,
    "lb/ft": FORCE_UNITS["lb"] / LENGTH_UNITS["ft"],
    "kg/m": 9.81,  # Masa lineal × gravedad = Fuerza/longitud
}

E_UNITS: Dict[str, float] = {
    "Pa": 1.0,       # Pascal (base SI)
    "GPa": 1e9,      # Gigapascal
    "MPa": 1e6       # Megapascal
}

INERCIA_UNITS: Dict[str, float] = {
    "m^4": 1.0,             # Metro^4 (base SI)
    "cm^4": (1e-2) ** 4     # Centímetro^4
}

DEFLEXION_DISPLAY: Dict[str, float] = {
    "m": 1.0,        # Metro
    "mm": 1e-3       # Milímetro
}

# ============================================================
# SISTEMAS PREDEFINIDOS (para selección en interfaz)
# ============================================================
UNIT_SYSTEMS = {
    "SI (N, m)": {
        "len": "m", 
        "force": "N", 
        "w": "N/m", 
        "E": "Pa", 
        "I": "m^4", 
        "defl": "m"
    },
    "SI mixto (kN, m)": {
        "len": "m", 
        "force": "kN", 
        "w": "kN/m", 
        "E": "GPa", 
        "I": "m^4", 
        "defl": "mm"
    },
    "Entrada masa (kg/m)": {
        "len": "m", 
        "force": "kgf", 
        "w": "kg/m",  # La app convierte automáticamente kg/m → N/m
        "E": "Pa", 
        "I": "m^4", 
        "defl": "mm"
    },
    "Imperial simplificado (lb, ft)": {
        "len": "ft", 
        "force": "lb", 
        "w": "lb/ft", 
        "E": "GPa",  # Módulo E se mantiene en GPa por conveniencia
        "I": "m^4",  # Inercia se mantiene en m^4
        "defl": "mm"
    },
}

# ============================================================
# FUNCIÓN DE CONVERSIÓN CON CACHÉ
# ============================================================

@lru_cache(maxsize=128)
def factor(units_map_key: str, key: str) -> float:
    """
    Obtiene el factor de conversión a SI para una unidad específica.
    
    Ejemplo de uso:
        factor('LENGTH', 'm') → 1.0
        factor('LENGTH', 'ft') → 0.3048
        factor('FORCE', 'kN') → 1000.0
    
    El decorador @lru_cache guarda resultados previos para mayor velocidad.
    
    Parámetros:
        units_map_key: Tipo de magnitud ('LENGTH', 'FORCE', 'E', etc.)
        key: Unidad específica ('m', 'kN', 'GPa', etc.)
    
    Retorna:
        Factor de conversión a SI
    """
    units_maps = {
        'LENGTH': LENGTH_UNITS,
        'FORCE': FORCE_UNITS,
        'DIST_LOAD': DIST_LOAD_UNITS,
        'E': E_UNITS,
        'INERCIA': INERCIA_UNITS,
        'DEFLEXION': DEFLEXION_DISPLAY,
    }
    
    if units_map_key not in units_maps:
        raise KeyError(f"Tipo de unidad desconocido: {units_map_key}")
    
    units_map = units_maps[units_map_key]
    
    if key not in units_map:
        raise KeyError(f"Unidad '{key}' desconocida en {units_map_key}")
    
    return units_map[key]
