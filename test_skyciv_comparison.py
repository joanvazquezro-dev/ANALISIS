"""
Script de prueba para comparar con SkyCiv

Configuración exacta del caso:
- Longitud: 5.5 m
- Apoyos: A=0, B=4.0
- Voladizo: 4.0 a 5.5 (1.5m)
- Carga uniforme: 2200 N/m de 0 a 5.5
- Carga triangular: 3360→0 N/m de 0 a 4.0
- Carga triangular: 1200→0 N/m de 4.0 a 5.5
"""

import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

# Añadir backend al path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

from backend.viga import Viga, Apoyo, CargaUniforme, CargaTriangular
from backend.integracion_subtramos import evaluar_por_subtramos

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN EXACTA DEL CASO DE SKYCIV
# ═══════════════════════════════════════════════════════════════════════════

L = 5.5  # m
E = 200e9  # Pa (valor típico, ajustar si es diferente)
I = 1e-6   # m⁴ (valor típico, ajustar si es diferente)

print("=" * 70)
print("COMPARACIÓN CON SKYCIV")
print("=" * 70)
print(f"Longitud: {L} m")
print(f"E: {E/1e9:.0f} GPa")
print(f"I: {I*1e8:.2f} cm⁴")
print()

# Crear viga con apoyos especificados (NO usar apoyos por defecto)
apoyos_iniciales = [
    Apoyo(0.0, "A"),
    Apoyo(4.0, "B")
]
viga = Viga(L, E, I, apoyos=apoyos_iniciales)

print("Apoyos:")
print(f"  A en x=0.0 m")
print(f"  B en x=4.0 m")
print(f"  Voladizo: 4.0 → 5.5 m (1.5 m)")
print()

# Cargas
print("Cargas:")
print(f"  1. Uniforme: 2200 N/m de 0 a 5.5 m")
viga.agregar_carga(CargaUniforme(2200, 0, 5.5))

print(f"  2. Triangular: 3360→0 N/m de 0 a 4.0 m")
viga.agregar_carga(CargaTriangular(3360, 0, 0, 4.0))

print(f"  3. Triangular: 1200→0 N/m de 4.0 a 5.5 m")
viga.agregar_carga(CargaTriangular(1200, 0, 4.0, 5.5))
print()

# ═══════════════════════════════════════════════════════════════════════════
# CALCULAR REACCIONES
# ═══════════════════════════════════════════════════════════════════════════

print("Calculando reacciones...")
reacciones = viga.calcular_reacciones()

print("\nREACCIONES:")
for nombre, valor in reacciones.items():
    print(f"  R_{nombre} = {valor/1000:.2f} kN")

# Verificar equilibrio
suma_reacciones = sum(reacciones.values())
suma_cargas = sum(c.total_load() for c in viga.cargas)
print(f"\nVERIFICACIÓN DE EQUILIBRIO:")
print(f"  ΣR = {suma_reacciones/1000:.2f} kN")
print(f"  ΣF = {suma_cargas/1000:.2f} kN")
print(f"  Error = {abs(suma_reacciones - suma_cargas):.2e} N")
print()

# ═══════════════════════════════════════════════════════════════════════════
# EVALUAR MOMENTO
# ═══════════════════════════════════════════════════════════════════════════

print("Evaluando diagramas...")
resultados = evaluar_por_subtramos(viga, puntos_por_tramo=100)

x_vals = resultados['x']
M_vals = resultados['M']

# Convertir a kN·m
M_kNm = M_vals / 1000

# ═══════════════════════════════════════════════════════════════════════════
# VALORES CLAVE
# ═══════════════════════════════════════════════════════════════════════════

print("\nVALORES CLAVE DEL MOMENTO:")

# M en apoyos (debe ser ≈0)
idx_A = np.argmin(np.abs(x_vals - 0.0))
idx_B = np.argmin(np.abs(x_vals - 4.0))
print(f"  M(A=0) = {M_kNm[idx_A]:.3f} kN·m (esperado: ≈0)")
print(f"  M(B=4.0) = {M_kNm[idx_B]:.3f} kN·m (esperado: ≈0)")

# M máximo en el vano [0, 4]
idx_vano = (x_vals >= 0) & (x_vals <= 4.0)
M_vano = M_kNm[idx_vano]
x_vano = x_vals[idx_vano]

if len(M_vano) > 0:
    idx_max_vano = np.argmax(np.abs(M_vano))
    M_max_vano = M_vano[idx_max_vano]
    x_max_vano = x_vano[idx_max_vano]
    print(f"  M_max en vano [0,4]: {M_max_vano:.2f} kN·m en x={x_max_vano:.2f} m")

# M en el extremo del voladizo (x=5.5)
idx_extremo = np.argmin(np.abs(x_vals - 5.5))
M_extremo = M_kNm[idx_extremo]
print(f"  M(extremo=5.5) = {M_extremo:.2f} kN·m")

# M máximo en el voladizo [4, 5.5]
idx_volad = (x_vals >= 4.0) & (x_vals <= 5.5)
M_volad = M_kNm[idx_volad]
x_volad = x_vals[idx_volad]

if len(M_volad) > 0:
    idx_max_volad = np.argmax(np.abs(M_volad))
    M_max_volad = M_volad[idx_max_volad]
    x_max_volad = x_volad[idx_max_volad]
    print(f"  M_max en voladizo [4,5.5]: {M_max_volad:.2f} kN·m en x={x_max_volad:.2f} m")

print()

# ═══════════════════════════════════════════════════════════════════════════
# COMPARACIÓN CON SKYCIV (valores aproximados de la imagen)
# ═══════════════════════════════════════════════════════════════════════════

print("COMPARACIÓN CON VALORES ESPERADOS DE SKYCIV:")
print("(Valores aproximados de la imagen)")
print()

# De la imagen de SkyCiv (valores aproximados):
# - M en vano: +7000 a +8000 kN·m (hacia abajo en gráfico = sagging)
# - M en voladizo: pico de -3000 a -4000 kN·m (hacia arriba en gráfico = hogging)

print("Valores esperados (aproximados de imagen):")
print("  - M_max en vano: +7000 a +8000 kN·m (sagging)")
print("  - M_max en voladizo: -3000 a -4000 kN·m (hogging)")
print()

print("Valores calculados:")
if len(M_vano) > 0:
    print(f"  - M_max en vano: {M_max_vano:.2f} kN·m en x={x_max_vano:.2f} m")
if len(M_volad) > 0:
    print(f"  - M_max en voladizo: {M_max_volad:.2f} kN·m en x={x_max_volad:.2f} m")

print()
print("NOTA: Los valores de SkyCiv son aproximados de la imagen.")
print("Si hay diferencias grandes, verifica E e I en SkyCiv.")
print()

# ═══════════════════════════════════════════════════════════════════════════
# GRAFICAR (estilo SkyCiv)
# ═══════════════════════════════════════════════════════════════════════════

print("Generando gráfica estilo SkyCiv...")

fig, ax = plt.subplots(figsize=(12, 6))

# Graficar momento
ax.plot(x_vals, M_kNm, 'b-', linewidth=2, label='Momento M(x)')
ax.fill_between(x_vals, 0, M_kNm, alpha=0.3)

# Marcar apoyos
for apoyo in viga.apoyos:
    ax.axvline(x=apoyo.posicion, color='green', linestyle='--', alpha=0.5, linewidth=1)
    ax.plot(apoyo.posicion, 0, 'g^', markersize=12, label=f'Apoyo {apoyo.nombre}')

# Marcar zonas
ax.axvspan(0, 4, alpha=0.1, color='blue', label='Vano')
ax.axvspan(4, 5.5, alpha=0.1, color='red', label='Voladizo')

# Configuración del gráfico (estilo SkyCiv: eje Y invertido)
ax.set_xlabel('x [m]', fontsize=12)
ax.set_ylabel('M [kN·m]', fontsize=12)
ax.set_title('Diagrama de Momento Flector (Comparación con SkyCiv)', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)
ax.axhline(y=0, color='black', linewidth=0.8)
ax.legend()

# Invertir eje Y para convención SkyCiv (sagging hacia abajo)
ax.invert_yaxis()

plt.tight_layout()
plt.savefig('comparacion_skyciv.png', dpi=150, bbox_inches='tight')
print("Gráfica guardada como 'comparacion_skyciv.png'")
print()

print("=" * 70)
print("FIN DEL ANÁLISIS")
print("=" * 70)
