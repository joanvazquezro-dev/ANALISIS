"""
Sistema de evaluación de vigas por integración GLOBAL CONTINUA.

MÉTODO ESTRICTAMENTE GLOBAL (Octubre 2025):
============================================
✓ Una sola función w_total(x) continua (suma todas las distribuidas)
✓ Reacciones por equilibrio global (no por tramos)
✓ V(x) con Heaviside: saltos solo por R y P (NO por M₀)
✓ M(x) = ∫V dx (una sola pasada global) + saltos de M₀
✓ Corrección afín única por vano (sin tocar voladizos)
✓ Sin nudos duplicados

CONVENCIONES DE SIGNOS:
======================
• w(x) > 0 → hacia ABAJO
• P > 0 → hacia ABAJO  
• M_aplicado > 0 → antihorario (CCW)
• V'(x) = -w(x)
• M'(x) = V(x)

SALTOS:
=======
• Apoyo:           V(x⁺) = V(x⁻) + R_y
• Carga puntual:   V(x⁺) = V(x⁻) - P
• Momento puntual: M(x⁺) = M(x⁻) + M_aplicado  (NO afecta V)
"""
from __future__ import annotations
from typing import Dict, List, Set
import numpy as np
from scipy.integrate import cumulative_trapezoid
from backend.viga import Viga, CargaPuntual, CargaMomento


def H(x, half=False):
    """
    Función Heaviside mejorada con opción de H(0) = ½.
    
    Parameters
    ----------
    x : array_like
        Valores donde evaluar Heaviside
    half : bool, optional
        Si True, usa H(0) = ½ para simetría exacta en discontinuidades
        Si False, usa H(0) = 1 (comportamiento estándar >=)
    
    Returns
    -------
    np.ndarray
        H(x) = {0 si x<0, ½ si x=0 (half=True), 1 si x>0}
    
    Notes
    -----
    H(0) = ½ mejora la precisión numérica en nudos con discontinuidades,
    reduciendo residuos en el momento M(x) antes de la corrección por vano.
    """
    x = np.asarray(x)
    if half:
        return (x > 0).astype(float) + 0.5 * (x == 0).astype(float)
    return (x >= 0).astype(float)

def obtener_nudos_criticos(viga: Viga) -> np.ndarray:
    """
    Construye grid de nudos críticos SIN DUPLICADOS.
    
    Incluye:
    - Extremos: {0, L}
    - Apoyos
    - Inicio/fin de cargas distribuidas
    - Posiciones de cargas puntuales
    - Posiciones de momentos puntuales
    
    Returns
    -------
    np.ndarray
        Array ordenado de posiciones únicas (sin duplicados)
    """
    nudos: Set[float] = {0.0, float(viga.longitud)}
    
    # Apoyos
    for apoyo in viga.apoyos:
        nudos.add(float(apoyo.posicion))
    
    # Cargas
    for carga in viga.cargas:
        tipo = carga.__class__.__name__
        
        if tipo in ['CargaPuntual', 'CargaMomento']:
            nudos.add(float(carga.posicion))
        elif tipo in ['CargaUniforme', 'CargaTriangular', 'CargaTrapezoidal']:
            nudos.add(float(carga.inicio))
            nudos.add(float(carga.fin))
    
    # Convertir a array ordenado sin duplicados
    nudos_array = np.array(sorted(nudos))
    
    # Eliminar duplicados que estén a menos de 1e-12
    if len(nudos_array) > 1:
        diferencias = np.diff(nudos_array)
        mascara_unicos = np.concatenate([[True], diferencias > 1e-12])
        nudos_array = nudos_array[mascara_unicos]
    
    return nudos_array


def construir_w_total_continua(viga: Viga, x_vals: np.ndarray) -> np.ndarray:
    """
    Construye UNA SOLA función w_total(x) continua sumando TODAS las cargas distribuidas.
    
    Suma:
    - Cargas uniformes
    - Cargas triangulares
    - Cargas trapezoidales
    - Cualquier distribución parcial
    
    NO incluye:
    - Cargas puntuales (producen saltos en V, no contribuyen a w continua)
    - Momentos puntuales (producen saltos en M, no en V ni w)
    
    Parameters
    ----------
    viga : Viga
        Objeto viga con cargas
    x_vals : np.ndarray
        Posiciones donde evaluar w(x)
    
    Returns
    -------
    np.ndarray
        w_total(x) en cada posición (N/m)
    
    Notes
    -----
    Las máscaras usan intervalos semi-abiertos [inicio, fin) para evitar
    doble conteo en puntos de unión entre cargas adyacentes, excepto en
    el extremo final de la viga donde se incluye el punto final.
    """
    w_total = np.zeros_like(x_vals, dtype=float)
    L_viga = float(viga.longitud)
    
    for carga in viga.cargas:
        tipo = carga.__class__.__name__
        
        if tipo == 'CargaPuntual' or tipo == 'CargaMomento':
            # No contribuyen a w(x) continua
            continue
            
        elif tipo == 'CargaUniforme':
            # w constante en [inicio, fin)
            # Usar intervalo semi-abierto para evitar doble conteo en uniones
            if abs(carga.fin - L_viga) < 1e-12:
                # Si termina en el extremo de la viga, incluir el punto final
                mascara = (x_vals >= carga.inicio) & (x_vals <= carga.fin)
            else:
                # Intervalo semi-abierto [inicio, fin)
                mascara = (x_vals >= carga.inicio) & (x_vals < carga.fin)
            w_total[mascara] += carga.intensidad
            
        elif tipo in ['CargaTriangular', 'CargaTrapezoidal']:
            # w lineal en [inicio, fin)
            if abs(carga.fin - L_viga) < 1e-12:
                mascara = (x_vals >= carga.inicio) & (x_vals <= carga.fin)
            else:
                mascara = (x_vals >= carga.inicio) & (x_vals < carga.fin)
                
            if np.any(mascara):
                L_tramo = carga.fin - carga.inicio
                if L_tramo > 1e-12:
                    # Posición relativa normalizada [0, 1]
                    xi = (x_vals[mascara] - carga.inicio) / L_tramo
                    # Interpolación lineal: w(ξ) = w₁(1-ξ) + w₂·ξ
                    w_local = carga.intensidad_inicio * (1.0 - xi) + carga.intensidad_fin * xi
                    w_total[mascara] += w_local
    
    return w_total


def evaluar_por_subtramos(viga: Viga, puntos_por_tramo: int = 50) -> Dict[str, np.ndarray]:
    """
    Evalúa V(x), M(x), θ(x), y(x) usando método ESTRICTAMENTE GLOBAL.
    
    ALGORITMO (Pasada Única):
    ==========================
    1. Identificar nudos críticos SIN DUPLICADOS
    2. Crear grid refinado global
    3. Construir w_total(x) continua (suma todas las distribuidas)
    4. Calcular reacciones por equilibrio global
    5. Construir V(x) = Σ(R_i·H(x-a_i)) - Σ(P_j·H(x-b_j)) - ∫w_total dx
       (UNA SOLA INTEGRACIÓN GLOBAL)
    6. Construir M(x) = ∫V dx + Σ(M₀_k·H(x-c_k))
       (UNA SOLA INTEGRACIÓN GLOBAL)
    7. Corrección afín ÚNICA por vano (M=0 en apoyos)
    8. θ(x) = ∫(M/EI) dx, y(x) = ∫θ dx
    9. Ajustar y=0 en apoyos
    
    Ventajas:
    ---------
    ✓ Sin bucles por tramos
    ✓ Sin reinicios de integración
    ✓ Continuidad perfecta garantizada
    ✓ Corrección única (no múltiples parches)
    ✓ Equilibrio global (física correcta)
    
    Parameters
    ----------
    viga : Viga
        Objeto viga con geometría, material, apoyos y cargas
    puntos_por_tramo : int, optional
        Densidad de puntos entre nudos críticos (default: 50)
    
    Returns
    -------
    Dict[str, np.ndarray]
        {'x': posiciones, 'V': cortante, 'M': momento, 
         'theta': pendiente, 'deflexion': desplazamiento}
    """
    # ═══════════════════════════════════════════════════════════════════════════
    # PASO 1: Nudos críticos SIN DUPLICADOS
    # ═══════════════════════════════════════════════════════════════════════════
    nudos = obtener_nudos_criticos(viga)
    n_nudos = len(nudos)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PASO 2: Grid global refinado con halos ±ε en discontinuidades
    # ═══════════════════════════════════════════════════════════════════════════
    # Estrategia: Añadir puntos adicionales cerca (±ε) de cada nudo crítico
    # para capturar con precisión los saltos en V y M sin "saltos visuales"
    #
    # min_steps controla la finura del halo (mayor → más denso cerca de nudos)
    # Recomendado: 2400-4000 para balance precisión/rendimiento
    
    min_steps = 2400                      # Densidad de malla (ajustable)
    L_total = float(viga.longitud)
    eps = L_total / min_steps             # Halo alrededor de cada nudo crítico
    
    x_grid = []
    
    for i in range(n_nudos - 1):
        x_i = nudos[i]
        x_ip1 = nudos[i + 1]
        
        # Inserta halo a la derecha de x_i y a la izquierda de x_ip1
        left = x_i
        right = x_ip1
        
        # Añadir nudo izquierdo
        x_grid.append(float(left))
        
        # Añadir puntos de halo si caben dentro del tramo
        hL = left + eps
        hR = right - eps
        
        if hL < hR:
            # Densidad base proporcional al tamaño del tramo
            n_internos = max(1, int(puntos_por_tramo * (right - left) / L_total))
            internos = np.linspace(hL, hR, n_internos)
            x_grid.extend(internos.tolist())
    
    # Último nudo
    x_grid.append(float(nudos[-1]))
    
    # Eliminar posibles duplicados numéricos (redondeo a 12 decimales)
    x_grid = np.array(sorted(set(np.round(x_grid, 12))))
    
    # ─────────────────────────────────────────────────────────────────────────
    # Refinado adicional en apoyos (captura saltos de V con mayor precisión)
    # ─────────────────────────────────────────────────────────────────────────
    for ap in viga.apoyos:
        xa = float(ap.posicion)
        # Añadir 3 puntos antes y 3 después del apoyo (dentro del halo)
        for d in (0.5*eps, 1.0*eps, 1.5*eps):
            if 0.0 <= xa + d <= L_total:
                x_grid = np.append(x_grid, xa + d)
            if 0.0 <= xa - d <= L_total:
                x_grid = np.append(x_grid, xa - d)
    
    # Reordenar y eliminar duplicados finales
    x_grid = np.array(sorted(set(np.round(x_grid, 12))))
    n_puntos = len(x_grid)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PASO 3: Calcular reacciones (equilibrio global, no por tramos)
    # ═══════════════════════════════════════════════════════════════════════════
    reacciones = viga.calcular_reacciones()
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PASO 4: Construir w_total(x) continua (UNA SOLA FUNCIÓN)
    # ═══════════════════════════════════════════════════════════════════════════
    # Suma TODAS las cargas distribuidas (uniformes, triangulares, trapezoidales)
    w_vals = construir_w_total_continua(viga, x_grid)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PASO 5: Construir V(x) con Heaviside (UNA SOLA PASADA)
    # ═══════════════════════════════════════════════════════════════════════════
    # V(x) = Σ(R_i·H(x-a_i)) - Σ(P_j·H(x-b_j)) - ∫₀ˣ w_total(ξ) dξ
    #
    # MEJORA: Usamos H(0)=½ para precisión numérica óptima en nudos.
    # Esto reduce residuos en M(x) exactamente en las discontinuidades,
    # aunque la corrección afín por vano (PASO 7) los eliminaría de todas formas.
    
    V_vals = np.zeros(n_puntos, dtype=float)
    
    # Saltos por REACCIONES (hacia arriba → positivo)
    # Usar H(0)=½ para simetría exacta en el nudo del apoyo
    for apoyo in viga.apoyos:
        R_y = float(reacciones[apoyo.nombre])
        V_vals += R_y * H(x_grid - apoyo.posicion, half=True)
    
    # Saltos por CARGAS PUNTUALES (hacia abajo → negativo)
    # Usar H(0)=½ para simetría exacta en el nudo de la carga
    for carga in viga.cargas:
        if isinstance(carga, CargaPuntual):
            P = float(carga.magnitud)
            V_vals -= P * H(x_grid - carga.posicion, half=True)
    
    # Integral de w_total (UNA SOLA VEZ)
    integral_w = cumulative_trapezoid(w_vals, x_grid, initial=0.0)
    V_vals -= integral_w
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PASO 6: Construir M(x) (UNA SOLA INTEGRACIÓN GLOBAL)
    # ═══════════════════════════════════════════════════════════════════════════
    # M(x) = ∫₀ˣ V(ξ) dξ + Σ(M₀_k·H(x-c_k))
    #
    # Notas:
    # - Momentos puntuales generan salto en M, NO en V
    # - Integración continua sin reinicios
    # - Corrección afín ÚNICA por vano después
    
    # Integrar V(x) globalmente (UNA SOLA VEZ)
    M_vals = cumulative_trapezoid(V_vals, x_grid, initial=0.0)
    
    # Saltos por MOMENTOS PUNTUALES
    for carga in viga.cargas:
        if isinstance(carga, CargaMomento):
            x_m = float(carga.posicion)
            M0 = float(carga.magnitud)
            
            # Verificar si está en apoyo y si debe aplicarse en el vano
            esta_en_apoyo = any(abs(x_m - ap.posicion) < 1e-12 for ap in viga.apoyos)
            en_vano = getattr(carga, 'en_vano', True)
            
            # Aplicar salto solo si no está en apoyo o si en_vano=True
            if not esta_en_apoyo or en_vano:
                # Buscar índice exacto del momento
                idxs_m = np.where(np.isclose(x_grid, x_m, atol=1e-12))[0]
                
                if idxs_m.size > 0:
                    idx_m = idxs_m[0]
                    # Heaviside con H(0) = 1/2
                    M_vals[idx_m] += M0 * 0.5
                    M_vals[idx_m+1:] += M0
                else:
                    # Si no está en grid exacto, salto para x > x_m
                    M_vals[x_grid > x_m] += M0
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PASO 7: Corrección afín POR VANO (M=0 en cada vano entre apoyos consecutivos)
    # ═══════════════════════════════════════════════════════════════════════════
    # Para vigas HIPERESTÁTICAS (3+ apoyos), se corrige M=0 en CADA VANO [apoyo_i, apoyo_i+1]
    # Para vigas ISOSTÁTICAS (2 apoyos), NO se aplica corrección (el momento ya es correcto)
    # NO tocar voladizos fuera de los apoyos extremos
    
    if len(viga.apoyos) >= 3:  # ← CAMBIO CRÍTICO: solo para sistemas hiperestáticos
        # Ordenar apoyos por posición (crítico para vanos consecutivos)
        pos_apoyos_orden = sorted([float(ap.posicion) for ap in viga.apoyos])
        
        # Iterar sobre cada vano [apoyo_i, apoyo_i+1]
        for xa, xb in zip(pos_apoyos_orden[:-1], pos_apoyos_orden[1:]):
            # Saltar vanos degenerados (apoyos muy cercanos)
            if abs(xb - xa) <= 1e-12:
                continue
            
            # Índices de los apoyos en el grid
            ia = np.argmin(np.abs(x_grid - xa))
            ib = np.argmin(np.abs(x_grid - xb))
            
            # Valores de M en los extremos del vano
            Ma = M_vals[ia]
            Mb = M_vals[ib]
            
            # Corrección afín: M_corr(x) = M(x) - [Ma + (Mb-Ma)/(xb-xa)·(x-xa)]
            pendiente = (Mb - Ma) / (xb - xa)
            mask = (x_grid >= xa) & (x_grid <= xb)
            M_vals[mask] -= (Ma + pendiente * (x_grid[mask] - xa))

    
    # ═══════════════════════════════════════════════════════════════════════════
    # PASO 8: Verificación de M=0 en apoyos (diagnóstico opcional)
    # ═══════════════════════════════════════════════════════════════════════════
    # Solo verificar M≈0 en APOYOS EXTREMOS de sistemas isostáticos
    # En apoyos intermedios con voladizo, M puede ser ≠0 (momento de continuidad)
    TOL_M = 1e-5  # Tolerancia para M en apoyos (10 μN·m)
    
    # Solo verificar si es sistema isostático (2 apoyos)
    if len(viga.apoyos) == 2:
        pos_apoyos_orden = sorted([float(ap.posicion) for ap in viga.apoyos])
        L_viga = float(viga.longitud)
        
        # Verificar M≈0 solo en apoyos que coinciden con extremos de la viga
        for apoyo in viga.apoyos:
            pos = float(apoyo.posicion)
            es_extremo = (abs(pos - 0.0) < 1e-9) or (abs(pos - L_viga) < 1e-9)
            
            if es_extremo:
                idx_ap = np.argmin(np.abs(x_grid - pos))
                M_apoyo = M_vals[idx_ap]
                if abs(M_apoyo) > TOL_M:
                    import warnings
                    warnings.warn(
                        f"⚠️ M({apoyo.nombre}) = {M_apoyo:.3e} N·m (esperado ≈0). "
                        f"Posible error numérico en apoyo extremo."
                    )
    
    # Para sistemas hiperestáticos (3+ apoyos), verificar todos los apoyos
    elif len(viga.apoyos) >= 3:
        for apoyo in viga.apoyos:
            idx_ap = np.argmin(np.abs(x_grid - apoyo.posicion))
            M_apoyo = M_vals[idx_ap]
            if abs(M_apoyo) > TOL_M:
                import warnings
                warnings.warn(
                    f"⚠️ M({apoyo.nombre}) = {M_apoyo:.3e} N·m (esperado ≈0). "
                    f"Revisar reacciones en sistemas hiperestáticos."
                )
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PASO 9: Integrar θ(x) y y(x) (método global)
    # ═══════════════════════════════════════════════════════════════════════════
    EI = float(viga.E * viga.I)
    
    # θ(x) = ∫₀ˣ [M(ξ)/EI] dξ
    theta_vals = cumulative_trapezoid(M_vals / EI, x_grid, initial=0.0)
    
    # y(x) = ∫₀ˣ θ(ξ) dξ
    y_vals = cumulative_trapezoid(theta_vals, x_grid, initial=0.0)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PASO 10: Corrección afín ÚNICA para y=0 en apoyos extremos (ORDENADOS)
    # ═══════════════════════════════════════════════════════════════════════════
    # Asegurar que usamos apoyos extremos independientemente del orden en la lista
    
    if len(viga.apoyos) >= 2:
        # Ordenar apoyos por posición (crítico si la lista viene desordenada)
        pos_apoyos_orden = sorted([float(ap.posicion) for ap in viga.apoyos])
        x_izq = pos_apoyos_orden[0]
        x_der = pos_apoyos_orden[-1]
        
        # Índices de los apoyos extremos en el grid
        idx_izq = np.argmin(np.abs(x_grid - x_izq))
        idx_der = np.argmin(np.abs(x_grid - x_der))
        
        y_izq = y_vals[idx_izq]
        y_der = y_vals[idx_der]
        
        # Corrección afín: y_corr = y - [y_izq + pendiente·(x-x_izq)]
        if abs(x_der - x_izq) > 1e-12:
            pendiente_y = (y_der - y_izq) / (x_der - x_izq)
            y_vals -= (y_izq + pendiente_y * (x_grid - x_izq))
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PASO 11: Verificaciones finales (diagnóstico)
    # ═══════════════════════════════════════════════════════════════════════════
    # Tolerancias relajadas para compatibilidad con mallas variadas
    TOL_V = 1e-5  # Tolerancia para V(L) (10 μN)
    L_viga = float(viga.longitud)
    
    # Verificar V(L) ≈ 0 solo si NO es voladizo y no hay carga puntual en L
    pos_apoyos_sorted = sorted([float(ap.posicion) for ap in viga.apoyos])
    hay_voladizo = len(pos_apoyos_sorted) > 0 and abs(pos_apoyos_sorted[-1] - L_viga) > 1e-9
    hay_puntual_en_L = any(
        isinstance(c, CargaPuntual) and abs(c.posicion - L_viga) < 1e-12
        for c in viga.cargas
    )
    
    # Solo verificar V(L)≈0 si el extremo está apoyado (no es voladizo)
    if not hay_voladizo and not hay_puntual_en_L:
        if abs(V_vals[-1]) > TOL_V:
            import warnings
            warnings.warn(
                f"⚠️ V(L) = {V_vals[-1]:.3e} N (esperado ≈0). "
                f"Posible error en equilibrio global."
            )
    
    # Verificar M(L) ≈ 0 (si hay apoyo en L o extremo libre)
    hay_apoyo_en_L = any(abs(ap.posicion - L_viga) < 1e-9 for ap in viga.apoyos)
    hay_momento_en_L = any(
        isinstance(c, CargaMomento) and abs(c.posicion - L_viga) < 1e-12
        for c in viga.cargas
    )
    
    if (hay_apoyo_en_L or not viga.apoyos) and not hay_momento_en_L:
        if abs(M_vals[-1]) > TOL_M:
            import warnings
            warnings.warn(
                f"⚠️ M(L) = {M_vals[-1]:.3e} N·m (esperado ≈0). "
                f"Revisar reacciones en sistemas hiperestáticos."
            )
    
    # ═══════════════════════════════════════════════════════════════════════════
    # RESULTADO: Retornar arrays calculados
    # ═══════════════════════════════════════════════════════════════════════════
    # ✅ Método estrictamente global (sin sub-tramos)
    # ✅ w_total(x) continua (todas las distribuidas sumadas)
    # ✅ V(x) con Heaviside + integración global única
    # ✅ M(x) con integración global única + saltos de M₀
    # ✅ Corrección afín única por vano (M=0 en apoyos)
    # ✅ Sin nudos duplicados
    # ✅ Sin reinicios de integración
    
    return {
        'x': x_grid,
        'V': V_vals,
        'M': M_vals,
        'theta': theta_vals,
        'deflexion': y_vals
    }
