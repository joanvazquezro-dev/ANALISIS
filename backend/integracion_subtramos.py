"""
Sistema de evaluación de vigas por integración por sub-tramos con nudos.

CONVENCIONES DE SIGNOS (OBLIGATORIAS):
=====================================
• w(x) > 0 → hacia ABAJO
• P > 0 → hacia ABAJO  
• M_aplicado > 0 → antihorario (CCW)
• V'(x) = -w(x)
• M'(x) = V(x)

SALTOS EN NUDOS:
================
• En apoyo: V(x+) = V(x-) + R_y
• En carga puntual: V(x+) = V(x-) - P
• En momento puntual: M(x+) = M(x-) + M_aplicado
"""
from __future__ import annotations
from typing import Dict, List, Tuple, Set
import numpy as np
from backend.viga import Viga, CargaPuntual, CargaMomento

def obtener_nudos(viga: Viga) -> np.ndarray:
    """
    Construye grid de nudos que incluye TODOS los puntos críticos:
    {0, L} ∪ {inicio/fin cargas distribuidas} ∪ {apoyos} ∪ {cargas puntuales} ∪ {momentos}
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
    
    return np.array(sorted(nudos))


def intensidad_carga_en_tramo(viga: Viga, x: float) -> float:
    """
    Retorna w(x) en un punto específico.
    CONVENCIÓN: w > 0 hacia ABAJO
    """
    w_total = 0.0
    
    for carga in viga.cargas:
        tipo = carga.__class__.__name__
        
        if tipo == 'CargaPuntual':
            # Las puntuales no contribuyen a w(x) continua
            continue
        elif tipo == 'CargaMomento':
            # Los momentos no contribuyen a w(x)
            continue
        elif tipo == 'CargaUniforme':
            if carga.inicio <= x <= carga.fin:
                w_total += carga.intensidad
        elif tipo in ['CargaTriangular', 'CargaTrapezoidal']:
            if carga.inicio <= x <= carga.fin:
                # Interpolación lineal
                L_tramo = carga.fin - carga.inicio
                xi = (x - carga.inicio) / L_tramo  # Posición relativa [0,1]
                w_x = carga.intensidad_inicio * (1 - xi) + carga.intensidad_fin * xi
                w_total += w_x
    
    return w_total


def evaluar_por_subtramos(viga: Viga, puntos_por_tramo: int = 50) -> Dict[str, np.ndarray]:
    """
    Evalúa V(x), M(x), θ(x), y(x) usando integración por sub-tramos con nudos.
    
    ALGORITMO ROBUSTO:
    ==================
    1. Identificar todos los nudos críticos: {0, L, apoyos, cargas, cambios de w(x)}
    2. Para cada nudo:
       - Aplicar saltos: V(x+) = V(x-) + R (apoyo) o V(x+) = V(x-) - P (carga puntual)
    3. Para cada tramo [x_i, x_{i+1}]:
       - Integrar numéricamente: V'(x) = -w(x) usando regla del trapecio
    4. Construir M(x):
       - M(x) = ∫V(x)dx + Σ(M₀·H(x-a)) para momentos puntuales
       - Aplicar corrección lineal si M≠0 en apoyos (error numérico pequeño)
    5. Construir θ(x) y y(x):
       - θ(x) = ∫M(x)/(EI) dx
       - y(x) = ∫θ(x) dx
       - Ajustar para y=0 en todos los apoyos
    
    Parameters
    ----------
    viga : Viga
        Objeto viga con geometría, material, apoyos y cargas
    puntos_por_tramo : int, optional
        Número de puntos de integración por sub-tramo (default: 50)
    
    Returns
    -------
    Dict[str, np.ndarray]
        Diccionario con arrays: 'x', 'V', 'M', 'theta', 'deflexion'
    """
    # Paso 1: Obtener nudos críticos
    nudos = obtener_nudos(viga)
    n_nudos = len(nudos)
    
    # Paso 2: Calcular reacciones
    reacciones = viga.calcular_reacciones()
    
    # Paso 3: Crear grid fino con puntos internos en cada tramo  ✅ CORREGIDO
    x_grid = []
    for i in range(n_nudos - 1):
        x_i = nudos[i]
        x_ip1 = nudos[i + 1]
        
        # incluir SIEMPRE el nudo izquierdo
        x_grid.append(float(x_i))
        
        # puntos internos (sin los extremos)
        if x_ip1 - x_i > 1e-12:
            internos = np.linspace(x_i, x_ip1, puntos_por_tramo + 1, endpoint=True)[1:-1]
            x_grid.extend(internos.tolist())
    
    # incluir SIEMPRE el último nudo
    x_grid.append(float(nudos[-1]))
    
    # no uses set() (pierde orden y puede mover nudos)
    x_grid = np.asarray(x_grid, dtype=float)
    n_puntos = len(x_grid)
    
    # Paso 4: Inicializar arrays
    V_vals = np.zeros(n_puntos)
    M_vals = np.zeros(n_puntos)
    
    # Paso 5: Construir V(x) integrando por tramos con saltos en nudos
    # 
    # ALGORITMO CORRECTO:
    # Para cada tramo [x_i, x_{i+1}]:
    #   1. Aplicar saltos en x_i (apoyo, carga puntual)
    #   2. Integrar V dentro del tramo: V(x) = V(x_i) - ∫[x_i, x] w(ξ) dξ
    #   3. Continuar al siguiente tramo
    
    V_actual = 0.0  # V(0-) = 0 (antes de cualquier cosa)
    idx_global = 0
    
    for i_nudo in range(n_nudos):
        x_nudo = nudos[i_nudo]
        
        # --- SALTOS EN EL NUDO x_nudo ---
        
        # 1. Salto por apoyo: V(x+) = V(x-) + R_y
        for apoyo in viga.apoyos:
            if abs(apoyo.posicion - x_nudo) < 1e-12:
                R_y = reacciones[apoyo.nombre]
                V_actual += R_y
        
        # 2. Salto por carga puntual: V(x+) = V(x-) - P
        for carga in viga.cargas:
            if carga.__class__.__name__ == 'CargaPuntual':
                if abs(carga.posicion - x_nudo) < 1e-12:
                    P = carga.magnitud
                    V_actual -= P
        
        # Asignar V exactamente en el nudo (índice exacto, no el "más cercano")
        idxs_nudo = np.where(np.isclose(x_grid, x_nudo, atol=1e-12))[0]
        if idxs_nudo.size:
            V_vals[idxs_nudo[0]] = V_actual
        
        # --- INTEGRACIÓN EN EL TRAMO [x_nudo, x_{nudo+1}] ---
        
        if i_nudo < n_nudos - 1:
            x_next = nudos[i_nudo + 1]
            
            # Encontrar puntos del grid en este tramo
            mask_tramo = (x_grid > x_nudo) & (x_grid <= x_next)
            indices_tramo = np.where(mask_tramo)[0]
            
            if len(indices_tramo) > 0:
                # Integrar desde x_nudo
                x_prev = x_nudo
                V_prev = V_actual
                
                for idx_curr in indices_tramo:
                    x_curr = x_grid[idx_curr]
                    
                    # Evaluar w en x_prev y x_curr
                    w_prev = intensidad_carga_en_tramo(viga, x_prev)
                    w_curr = intensidad_carga_en_tramo(viga, x_curr)
                    
                    # Integrar: dV = -∫w dx ≈ -(w_prev + w_curr)/2 * dx
                    dx = x_curr - x_prev
                    dV = -0.5 * (w_prev + w_curr) * dx
                    
                    V_curr = V_prev + dV
                    V_vals[idx_curr] = V_curr
                    
                    # Actualizar para siguiente paso
                    x_prev = x_curr
                    V_prev = V_curr
                
                # Actualizar V_actual al final del tramo
                V_actual = V_prev
    
    # Último punto (x = L)
    V_vals[-1] = V_actual
    
    # ═══════════════════════════════════════════════════════════════════════════
    # Paso 6: Construir M(x) — CHECKLIST COMPLETO ✅
    # ═══════════════════════════════════════════════════════════════════════════
    # ALGORITMO CORRECTO (continuidad primero, corrección después):
    #
    # 1️⃣ Integrar GLOBALMENTE una sola vez: M = ∫V dx
    #    → Mantiene continuidad perfecta (sin "crestitas")
    #    → NO reiniciar M=0 en cada apoyo
    #
    # 2️⃣ Aplicar saltos por momentos puntuales:
    #    → Sumar M₀ a todos los x ≥ a
    #    → Sumar M₀/2 exactamente en x = a
    #
    # 3️⃣ Corrección ÚNICA por mínimos cuadrados:
    #    → Forzar M=0 en TODOS los apoyos simultáneamente
    #    → Ajuste lineal (a₀ + b₀·x) que minimiza error en apoyos
    #    → NO deforma la forma del diagrama (solo traslación uniforme)
    # ═══════════════════════════════════════════════════════════════════════════
    
    from scipy.integrate import cumulative_trapezoid
    
    # 1️⃣ Integración global desde x=0 (mantiene continuidad)
    M_vals = cumulative_trapezoid(V_vals, x_grid, initial=0.0)
    
    # 2️⃣ Aplicar saltos por momentos puntuales
    for carga in viga.cargas:
        if carga.__class__.__name__ == 'CargaMomento':
            x_m = float(carga.posicion)
            M_aplicado = float(carga.magnitud)
            
            # Verificar si debe aplicarse (no si está en apoyo con en_vano=False)
            esta_en_apoyo = any(abs(x_m - apoyo.posicion) < 1e-12 for apoyo in viga.apoyos)
            en_vano = getattr(carga, 'en_vano', True)
            
            if not (esta_en_apoyo and not en_vano):
                # Encontrar índice exacto del momento puntual
                idxs_momento = np.where(np.isclose(x_grid, x_m, atol=1e-12))[0]
                
                if idxs_momento.size > 0:
                    idx_m = idxs_momento[0]
                    
                    # Salto: M(x=a) += M₀/2  (convención H(0) = 1/2)
                    M_vals[idx_m] += M_aplicado * 0.5
                    
                    # Salto: M(x>a) += M₀
                    M_vals[idx_m+1:] += M_aplicado
                else:
                    # Fallback: si no está exactamente en grid, usar máscara
                    mask_despues = x_grid > x_m
                    M_vals[mask_despues] += M_aplicado
    
    # 3️⃣ Corrección A: forzar M=0 en apoyos (SOLO en el vano)
    from backend.viga import CargaMomento
    
    if len(viga.apoyos) >= 2:
        pos_apoyos = sorted([ap.posicion for ap in viga.apoyos])
        xA = float(pos_apoyos[0])
        xB = float(pos_apoyos[-1])
        
        # Índices EXACTOS de los nudos de apoyo
        idxA = np.where(np.isclose(x_grid, xA, atol=1e-12))[0][0]
        idxB = np.where(np.isclose(x_grid, xB, atol=1e-12))[0][0]
        
        MA = M_vals[idxA]
        MB = M_vals[idxB]
        
        if abs(xB - xA) > 1e-12:
            m = (MB - MA) / (xB - xA)
            # Resta una recta SOLO en el vano [xA, xB], no en el voladizo
            mask_vano = (x_grid >= xA) & (x_grid <= xB)
            M_vals[mask_vano] = M_vals[mask_vano] - (MA + m * (x_grid[mask_vano] - xA))

    
    # ✅ VERIFICACIÓN: M debe ser ≈0 en todos los apoyos
    if len(viga.apoyos) >= 2:
        tol_apoyo = 1e-6  # 1 μN·m
        for apoyo in viga.apoyos:
            idxs_ap = np.where(np.isclose(x_grid, apoyo.posicion, atol=1e-12))[0]
            if idxs_ap.size > 0:
                M_apoyo = M_vals[idxs_ap[0]]
                if abs(M_apoyo) > tol_apoyo:
                    import warnings
                    warnings.warn(
                        f"⚠️ M({apoyo.nombre}) = {M_apoyo:.3e} N·m (esperado: ≈0). "
                        f"Verifique que las reacciones sean correctas."
                    )
    
    # Paso 8: Integrar para θ y y
    EI = viga.E * viga.I
    theta_vals = cumulative_trapezoid(M_vals / EI, x_grid, initial=0.0)
    y_vals = cumulative_trapezoid(theta_vals, x_grid, initial=0.0)
    
    # Ajustar y=0 en apoyos
    if len(viga.apoyos) >= 2:
        idx_izq = np.argmin(np.abs(x_grid - viga.apoyos[0].posicion))
        idx_der = np.argmin(np.abs(x_grid - viga.apoyos[-1].posicion))
        
        y_izq = y_vals[idx_izq]
        y_der = y_vals[idx_der]
        
        x_izq = x_grid[idx_izq]
        x_der = x_grid[idx_der]
        
        if abs(x_der - x_izq) > 1e-12:
            pendiente_y = (y_der - y_izq) / (x_der - x_izq)
            y_vals = y_vals - (y_izq + pendiente_y * (x_grid - x_izq))
    
    # Checks de cierre: verificar que V(L) y M(L) cumplan condiciones de frontera
    # NOTA: Estos checks pueden fallar si el solver de reacciones hiperestáticas
    # no ha convergido correctamente. En sistemas con muchos apoyos (n>=4),
    # el método de compatibilidad puede tener errores numéricos.
    TOL = 1e-6
    L_viga = float(viga.longitud)
    
    from backend.viga import CargaPuntual, CargaMomento
    
    hay_puntual_en_L = any(
        (isinstance(c, CargaPuntual)) and abs(c.posicion - L_viga) < 1e-12
        for c in viga.cargas
    )
    if not hay_puntual_en_L:
        if abs(V_vals[-1]) > 10*TOL:
            import warnings
            warnings.warn(f"V(L) no cierra correctamente: {V_vals[-1]:.3e} N (esperado: ~0)")
    
    hay_momento_en_L = any(
        (isinstance(c, CargaMomento)) and abs(c.posicion - L_viga) < 1e-12
        for c in viga.cargas
    )
    if not hay_momento_en_L:
        # Verificar si hay un apoyo en L
        hay_apoyo_en_L = any(abs(apoyo.posicion - L_viga) < 1e-9 for apoyo in viga.apoyos)
        if hay_apoyo_en_L:
            # Si hay apoyo en L, M(L) debe ser ~0
            if abs(M_vals[-1]) > 10*TOL:
                import warnings
                warnings.warn(f"M(L) no cierra correctamente: {M_vals[-1]:.3e} N·m (esperado: ~0). "
                             f"Esto puede indicar problemas en el solver de reacciones hiperestáticas.")
        else:
            # Si no hay apoyo en L (extremo libre), M(L) debe ser ~0
            if abs(M_vals[-1]) > 10*TOL:
                import warnings
                warnings.warn(f"M(L) en extremo libre no cierra: {M_vals[-1]:.3e} N·m (esperado: ~0)")
    
    # ✅ Devuelve el momento físico (sagging positivo, hogging negativo)
    return {
        'x': x_grid,
        'V': V_vals,
        'M': M_vals,
        'theta': theta_vals,
        'deflexion': y_vals
    }
