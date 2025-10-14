# Analizador de Vigas 🏗️

**Herramienta profesional para análisis estructural de vigas** — Calcula reacciones, cortante, momento, pendiente y deflexión con precisión ingenieril.

---

## 🎯 ¿Qué hace esta aplicación?

Analiza vigas con múltiples configuraciones de apoyos y cargas, resolviendo sistemas **isostáticos** (2 apoyos) e **hiperestáticos** (3+ apoyos) mediante:

### ✓ Reacciones en los apoyos
- **Isostáticos**: Equilibrio estático (ΣFy=0, ΣMA=0)
- **Hiperestáticos**: Método de compatibilidad de deflexiones con matriz de flexibilidad

### ✓ Diagramas estructurales
- **V(x)** — Cortante: Fuerza cortante a lo largo de la viga
- **M(x)** — Momento flector: Momento interno en cada sección
- **θ(x)** — Pendiente: Rotación de la sección transversal
- **y(x)** — Deflexión: Desplazamiento vertical (curva elástica)

### ✓ Método de cálculo robusto
**Integración por sub-tramos con nudos** (Octubre 2025):
- Identifica todos los puntos críticos (apoyos, cargas, cambios de intensidad)
- Integra numéricamente tramo por tramo con manejo explícito de discontinuidades
- Garantiza saltos correctos en V(x) y M(x) en puntos singulares
- Aplica correcciones para satisfacer condiciones de borde (M=0 en apoyos, y=0 en apoyos)

---

## 🚀 Inicio rápido

### 1. Instalar dependencias
```powershell
pip install -r requirements.txt
```

### 2. Ejecutar aplicación web
```powershell
streamlit run frontend/app.py
```

### 3. Usar la interfaz
1. **Barra lateral** → Define longitud L, módulo E, inercia I y sistema de unidades
2. **Configurar apoyos** → Elige predefinido o personalizado
3. **Agregar cargas** → Selecciona tipo (puntual, uniforme, triangular, trapezoidal, momento)
4. **Calcular** → Genera análisis completo
5. **Pestaña Resultados** → Visualiza diagramas y descarga datos (CSV/PNG/JSON)

---

## 📚 Tipos de carga soportados

| Tipo | Efecto en V(x) | Efecto en M(x) | Convención |
|------|----------------|----------------|------------|
| **Puntual** (P en x=a) | Salto de magnitud P | Cambio de pendiente | P>0 hacia abajo |
| **Uniforme** (w en [a,b]) | Variación lineal | Parábola | w>0 hacia abajo |
| **Triangular** | Parábola | Cúbica | w>0 hacia abajo |
| **Trapezoidal** | Parábola | Cúbica | w>0 hacia abajo |
| **Momento** (M₀ en x=a) | Sin cambio en V | Salto en M | Ver convención abajo |

### Convención de signos para momentos puntuales

#### **Momento Antihorario ↺ (Positivo, M > 0)**
- 🔄 Gira en sentido contrario a las manecillas del reloj
- ⬆️ Tiende a levantar el lado derecho de la viga
- 📈 Produce salto **positivo** (+M₀) en el diagrama M(x)
- 🎨 Color en interfaz: **morado**

**Ejemplo:**
```
Viga de 6m con M = +1000 N·m en x=3m
→ Levanta el centro de la viga
→ Diagrama M(x) salta +1000 N·m en x=3m
```

#### **Momento Horario ↻ (Negativo, M < 0)**
- 🔃 Gira en sentido de las manecillas del reloj
- ⬇️ Tiende a bajar el lado derecho de la viga
- 📉 Produce salto **negativo** (-M₀) en el diagrama M(x)
- 🎨 Color en interfaz: **naranja**

**Ejemplo:**
```
Viga de 6m con M = -1000 N·m en x=3m
→ Baja el centro de la viga
→ Diagrama M(x) salta -1000 N·m en x=3m
```

💡 **Nota:** Un momento puntual **NO afecta** V(x), solo produce salto en M(x).

---

## 🧮 Algoritmo de cálculo

### 1. Reacciones
**Sistema isostático (2 apoyos):**
```
ΣFy = 0 → RA + RB = ΣFi
ΣMA = 0 → RB·L = Σ(Fi·di) + Σ(Mj)
```

**Sistema hiperestático (3+ apoyos):**
- Apoyos extremos = sistema primario
- Apoyos intermedios = redundantes
- Matriz de flexibilidad: [f]·{R_redundantes} = -{δ_cargas}
- Superposición de efectos

### 2. Integración por sub-tramos (método actual)
```
1. Identificar nudos: {0, L, apoyos, inicios/fines de cargas, cargas puntuales}
2. Para cada nudo:
   - Aplicar saltos: V(x+) = V(x-) + R (apoyo) o V(x+) = V(x-) - P (carga puntual)
3. Entre nudos:
   - Integrar: V'(x) = -w(x) mediante regla del trapecio
4. Calcular M(x):
   - M(x) = ∫V(x)dx + Σ(M₀·H(x-a))
   - Aplicar corrección lineal si M≠0 en apoyos (error numérico)
5. Calcular θ(x) y y(x):
   - θ(x) = ∫M(x)/(EI) dx
   - y(x) = ∫θ(x) dx
   - Ajustar para y=0 en todos los apoyos
```

**Ventajas del método de sub-tramos:**
- ✓ Saltos precisos en discontinuidades
- ✓ No depende de integración simbólica compleja
- ✓ Manejo robusto de sistemas hiperestáticos
- ✓ Sin valores espurios fuera del dominio [0, L]

### 3. Fallback numérico
Si la integración por sub-tramos falla, se usa método anterior con integración trapezoidal continua.

---

## 📂 Estructura del proyecto

```
ANALISIS/
├── frontend/
│   └── app.py              # Interfaz web (Streamlit)
├── backend/
│   ├── viga.py             # Clases principales: Viga, Carga, Apoyo
│   ├── integracion_subtramos.py  # Método de sub-tramos (NUEVO)
│   ├── calculos.py         # Generación de DataFrames y valores máximos
│   ├── units.py            # Sistema de conversión de unidades
│   ├── utils.py            # Exportación CSV/PNG/JSON
│   └── menus.py            # Interfaz de consola (opcional)
├── outputs/                # Resultados exportados (auto-generados)
├── tests.py                # Suite de pruebas unitarias
├── requirements.txt        # Dependencias de Python
└── README.md               # Este archivo
```

**Archivos clave:**
- `viga.py` — Núcleo matemático (ecuaciones, tipos de carga, convenciones)
- `integracion_subtramos.py` — Algoritmo de integración por sub-tramos
- `app.py` — Interfaz gráfica web con Streamlit

---

## 📤 Exportación y unidades

### Formatos de exportación
- **CSV**: Tabla completa con columnas [x, V, M, θ, y]
- **PNG**: Gráficas de todos los diagramas con alta resolución
- **JSON**: Configuración completa para reproducir el análisis

### Sistema de unidades
**Internamente:** Todo en SI estricto (m, N, Pa, m⁴)  
**Interfaz:** Conversión automática entre:
- SI puro (N, m, Pa)
- SI mixto (kN, m, GPa)
- Imperial simplificado (lb, ft, psi)
- Entrada de masa (kg, kg/m) → conversión automática a fuerza

💡 **IMPORTANTE:** Al cambiar sistema de unidades, apoyos y cargas se resetean automáticamente para evitar inconsistencias dimensionales.

---

## 💡 Verificación de resultados

### Fórmula de referencia (viga biapoyada con carga uniforme)
```
ymax = (5·w·L⁴)/(384·E·I)    [deflexión máxima en el centro]
```

### Verificaciones automáticas
- ✓ **ΣR = ΣF** → Equilibrio de fuerzas verticales
- ✓ **V(L) ≈ 0** → Cortante nulo al final de voladizo
- ✓ **M(apoyos) = 0** → Momento nulo en apoyos simples
- ✓ **y(apoyos) = 0** → Deflexión nula en apoyos

### Saltos característicos a verificar
- **V(x)**: Salto en posiciones de cargas puntuales y apoyos
- **M(x)**: Salto en posiciones de momentos concentrados
- **M(x)**: Cero en apoyos simples (no empotrados)
- **y(x)**: Cero en todos los apoyos

---

## 🎓 Para tu reporte académico

✅ **Verifica coherencia:**
- Los signos de V(x) y M(x) deben ser consistentes con las cargas aplicadas
- Posiciones de máximos deben tener sentido físico

✅ **Compara con teoría:**
- Usa fórmulas de referencia para validar deflexiones
- Para momentos puntuales, verifica dirección del giro y signo del salto

✅ **Documentación:**
- Adjunta el archivo JSON exportado como evidencia de configuración
- Explica si el sistema es isostático o hiperestático y el método de solución
- Incluye capturas de diagramas con anotaciones

✅ **Validaciones específicas:**
- Verifica ΣR = ΣF (equilibrio)
- Confirma M=0 en apoyos simples
- Verifica que V(x) tenga saltos correctos en apoyos y cargas puntuales

---

## 🆕 Mejoras recientes (Octubre 2025)

### ✨ Integración por sub-tramos
- Algoritmo robusto que maneja correctamente discontinuidades
- Saltos explícitos en nudos críticos
- Corrección automática de errores numéricos acumulados
- Garantiza condiciones de borde exactas

### 🎨 Interfaz mejorada
- Selector visual de dirección para momentos (↺ / ↻)
- Código de colores (morado=antihorario, naranja=horario)
- Anotaciones claras en diagramas
- Panel de ayuda contextual

### 🔄 Sistema de unidades robusto
- Reseteo automático al cambiar unidades
- Prevención de errores dimensionales
- Soporte para múltiples sistemas (SI, Imperial, mixto)

---

## 🐛 Solución de problemas

**¿El diagrama V(x) tiene valores extraños después del último apoyo?**
→ Versión actual usa sub-tramos que limitan al dominio [0, L]

**¿M(x) no es cero en los apoyos?**
→ El método aplica corrección automática para errores numéricos < 0.1 N·m

**¿La deflexión no es cero en los apoyos?**
→ Se aplica ajuste lineal o de mínimos cuadrados según el número de apoyos

**¿Falla con sistema hiperestático?**
→ Verifica que los apoyos no estén duplicados (distancia mínima 1mm)

---

## 📝 Convenciones de signo (resumen)

| Magnitud | Signo positivo | Signo negativo |
|----------|----------------|----------------|
| **Carga distribuida w** | Hacia abajo ↓ | Hacia arriba ↑ |
| **Carga puntual P** | Hacia abajo ↓ | Hacia arriba ↑ |
| **Cortante V** | Reacción neta ↑ a la izquierda | Reacción neta ↓ a la izquierda |
| **Momento M** | Fibras superiores en compresión | Fibras inferiores en compresión |
| **Momento concentrado M₀** | Antihorario ↺ (levanta derecha) | Horario ↻ (baja derecha) |
| **Deflexión y** | Hacia abajo ↓ | Hacia arriba ↑ |

---

## 🔬 Detalles técnicos

### Dependencias principales
- **SymPy**: Matemática simbólica (construcción de expresiones)
- **NumPy**: Cálculo numérico vectorizado
- **SciPy**: Integración numérica (cumulative_trapezoid)
- **Pandas**: Estructuras de datos tabulares
- **Matplotlib**: Generación de gráficas
- **Streamlit**: Interfaz web interactiva

### Hipótesis del modelo
- Teoría de Euler-Bernoulli (vigas esbeltas)
- Material lineal elástico (E constante)
- Momento de inercia constante (I)
- Pequeñas deformaciones (y << L)
- Secciones planas permanecen planas

---

**¿Dudas técnicas?** Revisa los comentarios detallados en `backend/viga.py` y `backend/integracion_subtramos.py` para entender la implementación matemática completa.

**Versión:** 2.0 (Octubre 2025) con integración por sub-tramos
