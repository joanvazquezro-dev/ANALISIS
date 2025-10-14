# Analizador de Vigas 🏗️# Analizador de Vigas 🏗️



**Herramienta para análisis estructural de vigas** — Calcula reacciones, cortante, momento, pendiente y deflexión sin programar.**Herramienta para análisis estructural de vigas** — Calcula reacciones, cortante, momento, pendiente y deflexión sin programar.



------



## 🎯 ¿Qué hace esta aplicación?## 🎯 ¿Qué hace esta aplicación?



Analiza vigas con múltiples configuraciones de apoyos y cargas, calculando:Analiza vigas con múltiples configuraciones de apoyos y cargas, calculando:



### **Reacciones en los apoyos**### **Reacciones en los apoyos**

Resuelve sistemas:Resuelve sistemas:

- **Isostáticos** (2 apoyos): Usa equilibrio estático- **Isostáticos** (2 apoyos): Usa equilibrio estático

- **Hiperestáticos** (3+ apoyos): Método de compatibilidad de deflexiones- **Hiperestáticos** (3+ apoyos): Método de compatibilidad de deflexiones



### **Diagramas estructurales**### **Diagramas estructurales**

- **V(x)** — Cortante: Suma de fuerzas verticales- **V(x)** — Cortante: Suma de fuerzas verticales

- **M(x)** — Momento flector: Integración del cortante- **M(x)** — Momento flector: Integración del cortante

- **θ(x)** — Pendiente: Derivada de la deflexión- **θ(x)** — Pendiente: Derivada de la deflexión

- **y(x)** — Deflexión: Curva elástica de la viga- **y(x)** — Deflexión: Curva elástica de la viga



### **Convenciones de signo**### **Convenciones de signo**

- Cargas hacia abajo → magnitud **positiva**- Cargas hacia abajo → magnitud **positiva**

- V(x) positivo → cortante hacia **arriba** a la izquierda- V(x) positivo → cortante hacia **arriba** a la izquierda

- M(x) positivo → fibras superiores en **compresión**- M(x) positivo → fibras superiores en **compresión**

- **Momento concentrado positivo → sentido antihorario ↺** (levanta lado derecho)- **Momento concentrado positivo → sentido antihorario ↺** (levanta lado derecho)

- **Momento concentrado negativo → sentido horario ↻** (baja lado derecho)- **Momento concentrado negativo → sentido horario ↻** (baja lado derecho)



------



## 🚀 Inicio rápido## 🚀 Inicio rápido



### 1. Instalar dependencias### 1. Instalar dependencias

```powershell```powershell

pip install -r requirements.txtpip install -r requirements.txt

``````



### 2. Ejecutar aplicación### 2. Ejecutar aplicación

```powershell```powershell

streamlit run frontend/app.pystreamlit run frontend/app.py

``````



### 3. Usar la interfaz### 3. Usar la interfaz

1. **Barra lateral** → Define propiedades (L, E, I) y sistema de unidades1. **Barra lateral** → Define propiedades (L, E, I) y sistema de unidades

2. **Configurar apoyos** → Elige configuración predefinida o personalizada2. **Configurar apoyos** → Elige configuración predefinida o personalizada

3. **Agregar cargas** → Selecciona tipo y parámetros3. **Agregar cargas** → Selecciona tipo y parámetros

   - **NOVEDAD:** Para momentos puntuales, selecciona dirección con selector visual   - **NOVEDAD:** Para momentos puntuales, selecciona dirección con selector visual

     - `Antihorario ↺` → Momento positivo (levanta lado derecho)     - `Antihorario ↺` → Momento positivo (levanta lado derecho)

     - `Horario ↻` → Momento negativo (baja lado derecho)     - `Horario ↻` → Momento negativo (baja lado derecho)

4. **Calcular** → Genera resultados4. **Calcular** → Genera resultados

5. **Pestaña Resultados** → Visualiza diagramas y descarga datos5. **Pestaña Resultados** → Visualiza diagramas y descarga datos



------



## 📚 Tipos de carga## 📚 Tipos de carga



| Tipo | Efecto en V(x) | Efecto en M(x) | Convención || Tipo | Efecto en V(x) | Efecto en M(x) | Convención |

|------|----------------|----------------|------------||------|----------------|----------------|------------|

| **Puntual** (P en x=a) | Salto de magnitud P | Cambio de pendiente | P>0 hacia abajo || **Puntual** (P en x=a) | Salto de magnitud P | Cambio de pendiente | P>0 hacia abajo |

| **Uniforme** (w en [a,b]) | Variación lineal | Parábola | w>0 hacia abajo || **Uniforme** (w en [a,b]) | Variación lineal | Parábola | w>0 hacia abajo |

| **Triangular** | Parábola | Cúbica | w>0 hacia abajo || **Triangular** | Parábola | Cúbica | w>0 hacia abajo |

| **Trapezoidal** | Parábola | Cúbica | w>0 hacia abajo || **Trapezoidal** | Parábola | Cúbica | w>0 hacia abajo |

| **Momento** (M₀ en x=a) | Sin cambio | Salto de M₀ | **Ver abajo** || **Momento** (M₀ en x=a) | Sin cambio | Salto de M₀ | **Ver abajo** |



### **Momentos puntuales — Convención de signos:**### **Momentos puntuales — Convención de signos:**



#### **Momento Antihorario ↺ (Positivo, M > 0)**#### **Momento Antihorario ↺ (Positivo, M > 0)**

- 🔄 Gira en sentido contrario a las manecillas del reloj- 🔄 Gira en sentido contrario a las manecillas del reloj

- ⬆️ Tiende a levantar el lado derecho de la viga- ⬆️ Tiende a levantar el lado derecho de la viga

- 📈 Produce salto **positivo** en el diagrama M(x)- 📈 Produce salto **positivo** en el diagrama M(x)

- 🎨 En la interfaz: **color morado**- 🎨 En la interfaz: **color morado**



**Ejemplo:****Ejemplo:**

``````

Viga de 6m con M = +1000 N·m en x=3mViga de 6m con M = +1000 N·m en x=3m

→ El momento levanta el centro de la viga→ El momento levanta el centro de la viga

→ Diagrama M(x) salta +1000 N·m en x=3m→ Diagrama M(x) salta +1000 N·m en x=3m

``````



#### **Momento Horario ↻ (Negativo, M < 0)**#### **Momento Horario ↻ (Negativo, M < 0)**

- 🔃 Gira en sentido de las manecillas del reloj- 🔃 Gira en sentido de las manecillas del reloj

- ⬇️ Tiende a bajar el lado derecho de la viga- ⬇️ Tiende a bajar el lado derecho de la viga

- 📉 Produce salto **negativo** en el diagrama M(x)- 📉 Produce salto **negativo** en el diagrama M(x)

- 🎨 En la interfaz: **color naranja**- 🎨 En la interfaz: **color naranja**



**Ejemplo:****Ejemplo:**

``````

Viga de 6m con M = -1000 N·m en x=3mViga de 6m con M = -1000 N·m en x=3m

→ El momento baja el centro de la viga→ El momento baja el centro de la viga

→ Diagrama M(x) salta -1000 N·m en x=3m→ Diagrama M(x) salta -1000 N·m en x=3m

``````



💡 **Nota importante:** Un momento puntual **NO afecta** el diagrama de cortante V(x), solo produce un salto en M(x).💡 **Nota importante:** Un momento puntual **NO afecta** el diagrama de cortante V(x), solo produce un salto en M(x).



⚙️ **Configuración especial:** Si el momento está exactamente en un apoyo (x=0 o x=L), puedes elegir si produce salto dentro del vano o solo afecta las reacciones.⚙️ **Configuración especial:** Si el momento está exactamente en un apoyo (x=0 o x=L), puedes elegir si produce salto dentro del vano o solo afecta las reacciones.

---

---

## 🧮 Cómo se calculan

## 🧮 Cómo se calculan los resultados1) Reacciones

- Isostático (2 apoyos): ΣFy=0 y ΣMA=0.

### 1. Reacciones- Hiperestático (≥3 apoyos): compatibilidad de deflexiones (método de flexibilidad) con superposición.

**Sistema isostático (2 apoyos):**

```2) Cortante V(x)

ΣFy = 0 → RA + RB = ΣFi- Se construye con funciones de Heaviside/Macaulay a partir de reacciones y cargas.

ΣMA = 0 → RB·L = Σ(Fi·di) + Σ(Mj)

```3) Momento M(x)

- M(x)=∫0^x V(ξ)dξ + Σ M0·H(x−a). En x=a, H(0)=1/2.

**Sistema hiperestático (3+ apoyos):**

- Método de compatibilidad de deflexiones4) Pendiente y deflexión

- Matriz de flexibilidad + superposición- θ(x)=∫ M/(EI) dx y y(x)=∫ θ dx, imponiendo y=0 en los apoyos.

- Condición: deflexión = 0 en todos los apoyos

5) Plan B numérico

### 2. Cortante V(x)- Si el camino simbólico falla, se integra numéricamente (trapezoidal) y se ajusta y=0 en apoyos.

```

V(x) = RA + Σ(cargas a la izquierda de x)---

```## 📂 Estructura del proyecto

Construido con funciones de Heaviside/Macaulay

ANALISIS/

### 3. Momento M(x)- frontend/

```  - app.py  — Interfaz (Streamlit)

M(x) = ∫₀ˣ V(ξ)dξ + Σ(M₀·H(x-a))- backend/

```  - viga.py      — Núcleo de cálculo (Viga, Cargas, Apoyo)

Donde H(x-a) es la función Heaviside (saltos por momentos puntuales)  - calculos.py  — Discretización y DataFrames

  - units.py     — Conversión de unidades

### 4. Pendiente y Deflexión  - utils.py     — Exportación CSV/PNG/JSON

```- outputs/       — Resultados (csv, gráficas, configs)

θ(x) = ∫ M(x)/(EI) dx- requirements.txt

y(x) = ∫ θ(x) dx- README.md

```

**Condiciones de borde:** y = 0 en todos los apoyos---

## 📤 Exportación y unidades

### 5. Método numérico alternativo

Si la integración simbólica se complica, se usa integración trapezoidal numérica con ajuste de condiciones de borde.- CSV: x, V, M, θ, y

- PNG: diagramas

---- JSON: configuración completa para reproducir casos



## 📂 Estructura del proyectoInternamente se usa SI (m, N, Pa, m⁴); la app convierte a/desde otras unidades en la interfaz.

---

```

ANALISIS/## ✅ Consejos para tu reporte

├── frontend/

│   └── app.py          # Interfaz web (Streamlit)- Verifica signos y posiciones de máximos.

├── backend/- Compara deflexión central con la fórmula de referencia: ymax = 5 w L^4 / (384 E I) para viga simplemente apoyada con carga uniforme.

│   ├── viga.py         # Clases: Viga, Carga, Apoyo- Adjunta el JSON exportado como evidencia de configuración.

│   ├── calculos.py     # Generación de DataFrames y máximos- Explica si el sistema es isostático o hiperestático y cómo se resolvió.

│   ├── units.py        # Conversiones de unidades

│   └── utils.py        # Exportación (CSV, PNG, JSON)---

├── outputs/            # Resultados exportados¿Dudas? Lee los comentarios en `backend/viga.py` para detalles de implementación.

├── requirements.txt    # Dependencias# Analizador de Vigas 🏗️# Analizador de Vigas 🏗️# Analizador de vigas (simplemente apoyadas) – Guía para alumnos de Ing. Civil

└── README.md          # Este archivo

```



**Archivos clave:****Herramienta para análisis estructural de vigas** — Calcula reacciones, cortante, momento, pendiente y deflexión sin programar.

- `viga.py` — Núcleo matemático (define tipos de carga, construye ecuaciones)

- `calculos.py` — Discretización y evaluación numérica

- `units.py` — Sistema de conversión entre unidades

- `app.py` — Interfaz gráfica con Streamlit---**Herramienta para análisis estructural de vigas** — Calcula reacciones, cortante, momento, pendiente y deflexión sin programar.Herramienta sencilla para calcular y graficar cortante V(x), momento M(x), pendiente θ(x) y deflexión y(x) en vigas simplemente apoyadas, sin necesidad de programar.



---



## 💡 Verificación de resultados## 🎯 ¿Qué hace esta aplicación?



### Fórmula de referencia (viga biapoyada con carga uniforme)

```

ymax = (5·w·L⁴)/(384·E·I)    [deflexión máxima en el centro]Analiza vigas con múltiples configuraciones de apoyos y cargas, calculando:---## Qué calcula (en pocas palabras)

```



### Saltos característicos a verificar

- **V(x)**: Salto en posiciones de cargas puntuales y apoyos### **Reacciones en los apoyos**

- **M(x)**: Salto en posiciones de momentos concentrados

- **y(x)**: Debe ser cero en todos los apoyosResuelve sistemas:



### Verificar momentos puntuales- **Isostáticos** (2 apoyos): Usa equilibrio estático## 🎯 ¿Qué hace esta aplicación?- Equilibrio estático para reacciones en apoyos A (x=0) y B (x=L):

✓ **Momento positivo** → Diagrama M(x) **sube** en ese punto  

✓ **Momento negativo** → Diagrama M(x) **baja** en ese punto  - **Hiperestáticos** (3+ apoyos): Método de compatibilidad de deflexiones

✓ **No afecta V(x)** → Cortante permanece continuo

  - $\sum F_y=0 \Rightarrow R_A + R_B = \sum F_i$

---

### **Diagramas estructurales**

## 📤 Exportación y unidades

- **V(x)** — Cortante: Suma de fuerzas verticalesAnaliza vigas con múltiples configuraciones de apoyos y cargas, calculando:  - $\sum M_A=0 \Rightarrow R_B\,L = \sum(F_i\,d_i) + \sum(M_{0j})$

### Formatos disponibles

- **CSV**: Tabla completa (x, V, M, θ, y)- **M(x)** — Momento flector: Integración del cortante

- **PNG**: Gráficas de todos los diagramas

- **JSON**: Configuración completa para reproducir el análisis- **θ(x)** — Pendiente: Derivada de la deflexión- Cortante V(x): suma de aportes de reacciones y cargas (método de tramos con funciones de Heaviside/Macaulay).



### Sistema de unidades- **y(x)** — Deflexión: Curva elástica de la viga

**Internamente:** Todo en SI (m, N, Pa, m⁴)  

**Interfaz:** Conversión automática entre:### **Reacciones en los apoyos**- Momento M(x): integración de V(x) y saltos por momentos puntuales: $M(x)=\int_0^x V(\xi)\,d\xi + \sum M_{0j}\,H(x-a_j)$.

- SI puro (N, m)

- SI mixto (kN, m)### **Convenciones de signo**

- Imperial simplificado (lb, ft)

- Entrada de masa (kg/m)- Cargas hacia abajo → magnitud **positiva**Resuelve sistemas:- Pendiente y deflexión: $\theta(x)=\int \frac{M(x)}{E I}\,dx$ y $y(x)=\int \theta(x)\,dx$, aplicando condiciones de borde $y(0)=y(L)=0$.



💡 **IMPORTANTE:** Al cambiar el sistema de unidades, los apoyos y cargas se resetean automáticamente para evitar inconsistencias.- V(x) positivo → cortante hacia **arriba** a la izquierda



---- M(x) positivo → fibras superiores en **compresión**- **Isostáticos** (2 apoyos): Usa equilibrio estático- Si el cálculo simbólico se complica, se usa un método numérico robusto (integración trapezoidal) que da resultados prácticos.



## 🎓 Consejos para tu reporte académico- Momento concentrado positivo → sentido **antihorario** ↺



✅ **Verifica coherencia:**- Momento concentrado negativo → sentido **horario** ↻- **Hiperestáticos** (3+ apoyos): Método de compatibilidad de deflexiones

- Los signos de V(x) y M(x) deben ser consistentes con las cargas aplicadas

- Posiciones de máximos deben tener sentido físico



✅ **Compara con teoría:**---Convenciones de signo (usadas por la app):

- Usa fórmulas de referencia para validar deflexiones

- Para momentos puntuales, verifica que el salto coincida con la dirección del giro



✅ **Documentación:**## 🚀 Inicio rápido### **Diagramas estructurales**- Las cargas hacia abajo se ingresan con magnitud positiva.

- Adjunta el archivo JSON exportado como evidencia de la configuración usada

- Explica si el sistema es isostático o hiperestático y cómo se resolvió

- Incluye capturas de los diagramas con anotaciones de momentos

### 1. Instalar dependencias- **V(x)** — Cortante: Suma de fuerzas verticales- V(x) positivo = reacción neta hacia arriba a la izquierda de la sección.

✅ **Para momentos puntuales específicamente:**

- Verifica que el símbolo visual (↺ o ↻) coincida con el efecto esperado```powershell

- Comprueba que M(x) tenga el salto correcto (positivo o negativo)

- Confirma que V(x) no cambia en esa posiciónpip install -r requirements.txt- **M(x)** — Momento flector: Integración del cortante- M(x) positivo con la convención habitual de “fibras superiores en compresión”.



---```



## 🆕 Actualizaciones recientes- **θ(x)** — Pendiente: Derivada de la deflexión- Momentos puntuales introducen un salto en M(x); en el punto se toma $H(0)=\tfrac{1}{2}$.



### Mejoras en momentos puntuales (v1.1)### 2. Ejecutar aplicación

- ✨ Selector visual de dirección (Antihorario ↺ / Horario ↻)

- 🎨 Código de colores: morado (antihorario) y naranja (horario)```powershell- **y(x)** — Deflexión: Curva elástica de la viga

- 📊 Anotaciones mejoradas en diagramas con símbolos de dirección

- 📝 Lista de cargas muestra claramente la dirección del momentostreamlit run frontend/app.py

- ℹ️ Panel de ayuda contextual con convenciones de signo

```## Cómo usar la app (sin programar)

### Sistema de unidades automático

- 🔄 Reseteo automático de configuración al cambiar unidades

- ✅ Previene errores de apoyos fuera de rango

- 🌐 Soporte para sistemas SI, Imperial y mixtos### 3. Usar la interfaz### **Convenciones de signo**



---1. **Barra lateral** → Define propiedades (L, E, I) y sistema de unidades



**¿Dudas técnicas?** Lee los comentarios detallados en `backend/viga.py` para comprender la implementación matemática.2. **Configurar apoyos** → Elige configuración predefinida o personalizada- Cargas hacia abajo → magnitud **positiva**1) Instalar dependencias (una sola vez):


3. **Agregar cargas** → Selecciona tipo y parámetros

4. **Calcular** → Genera resultados- V(x) positivo → cortante hacia **arriba** a la izquierda

5. **Pestaña Resultados** → Visualiza diagramas y descarga datos

- M(x) positivo → fibras superiores en **compresión**```powershell

---

pip install -r requirements.txt

## 📚 Tipos de carga

---```

| Tipo | Efecto en V(x) | Efecto en M(x) | Convención |

|------|----------------|----------------|------------|

| **Puntual** (P en x=a) | Salto de magnitud P | Cambio de pendiente | P>0 hacia abajo |

| **Uniforme** (w en [a,b]) | Variación lineal | Parábola | w>0 hacia abajo |## 🚀 Inicio rápido2) Ejecutar la interfaz:

| **Triangular** | Parábola | Cúbica | w>0 hacia abajo |

| **Trapezoidal** | Parábola | Cúbica | w>0 hacia abajo |

| **Momento** (M₀ en x=a) | Sin cambio | Salto de M₀ | **Ver abajo** |

### 1. Instalar dependencias```powershell

### **Convención de momentos puntuales:**

- **M > 0 (positivo)** → Giro **antihorario** ↺```powershellstreamlit run frontend/app.py

  - Tiende a levantar el lado derecho de la viga

  - Produce salto positivo en diagrama de momentopip install -r requirements.txt```

  

- **M < 0 (negativo)** → Giro **horario** ↻```

  - Tiende a bajar el lado derecho de la viga

  - Produce salto negativo en diagrama de momento3) En la barra lateral:



**Ejemplo práctico:**### 2. Ejecutar aplicación- Elige sistema de unidades y define L, E, I.

```

Viga de 6m con momento M=+1000 N·m en x=3m```powershell- Agrega cargas (puntual, uniforme, triangular, trapezoidal o momento puntual) y su posición/rango.

→ Antihorario: levanta centro, comprime fibras superiores

→ Diagrama M(x) salta +1000 N·m en x=3mstreamlit run frontend/app.py- Pulsa “Calcular”.



Viga de 6m con momento M=-1000 N·m en x=3m  ```

→ Horario: baja centro, comprime fibras inferiores

→ Diagrama M(x) salta -1000 N·m en x=3m4) Pestaña “Resultados”:

```

### 3. Usar la interfaz- Verás RA y RB, tabla de valores y diagramas de q(x), V(x), M(x), y(x).

---

1. **Barra lateral** → Define propiedades (L, E, I) y sistema de unidades- Puedes descargar los datos como CSV y guardar la configuración en JSON.

## 🔧 Tipos de sistemas

2. **Configurar apoyos** → Elige configuración predefinida o personalizada

### Isostático (2 apoyos)

```3. **Agregar cargas** → Selecciona tipo y parámetrosSugerencia: si aplicas un momento exactamente en un apoyo (x=0 o x=L), la app permite decidir si ese momento produce salto dentro del vano o sólo ajusta las reacciones.

Ecuaciones: ΣFy=0, ΣMA=0

Reacciones: RA + RB = ΣF4. **Calcular** → Genera resultados

```

5. **Pestaña Resultados** → Visualiza diagramas y descarga datos## Tipos de carga soportados (qué hacen en V y M)

### Hiperestático (3+ apoyos)

```

Método: Compatibilidad de deflexiones

1. Sistema primario: 2 apoyos extremos---- Carga puntual P en x=a: salto en V(x) y cambio de pendiente en M(x).

2. Apoyos intermedios = redundantes

3. Resolver: [f]·{R} = -{δcargas}- Carga uniforme w entre [a,b]: V(x) varía lineal; M(x) cuadrático en ese tramo.

```

## 📚 Tipos de carga- Carga triangular (0→w₀ o w₀→0): V(x) y M(x) varían como polinomios de orden 2 y 3 respectivamente.

---

- Carga trapezoidal (w₁→w₂): caso general lineal por tramo.

## 📂 Estructura del proyecto

| Tipo | Efecto en V(x) | Efecto en M(x) |- Momento puntual M₀ en x=a: no cambia V(x), introduce salto M₀ en M(x).

```

ANALISIS/|------|----------------|----------------|

├── frontend/

│   └── app.py          # Interfaz web (Streamlit)| **Puntual** (P en x=a) | Salto de magnitud P | Cambio de pendiente |## Cómo se calculan las cosas (un poco más de detalle)

├── backend/

│   ├── viga.py         # Clases: Viga, Carga, Apoyo| **Uniforme** (w en [a,b]) | Variación lineal | Parábola |

│   ├── calculos.py     # Generación de DataFrames y máximos

│   ├── units.py        # Conversiones de unidades| **Triangular** | Parábola | Cúbica |1) Reacciones: con $\sum F=0$ y $\sum M_A=0$.

│   └── utils.py        # Exportación (CSV, PNG, JSON)

├── outputs/            # Resultados exportados| **Trapezoidal** | Parábola | Cúbica |2) Cortante V(x):

├── requirements.txt    # Dependencias

└── README.md          # Este archivo| **Momento** (M₀ en x=a) | Sin cambio | Salto de M₀ |	- Se arma con funciones de Heaviside/Macaulay para cada carga y las reacciones.

```

3) Momento M(x):

---

---	- $M(x)=\int_0^x V(\xi)\,d\xi$.

## 🧮 Proceso de cálculo

	- Si hay momentos puntuales, se suman saltos $M_0\,H(x-a)$.

### 1. Reacciones

```## 🔧 Tipos de sistemas4) Pendiente y deflexión:

Sistema isostático:

  ΣFy = 0 → RA + RB = ΣFi	- $\theta=\int M/(EI)$ y $y=\int \theta$.

  ΣMA = 0 → RB·L = Σ(Fi·di) + Σ(Mj)

### Isostático (2 apoyos)	- Se imponen $y(0)=y(L)=0$ para determinar constantes.

Sistema hiperestático:

  Matriz de flexibilidad + superposición```5) Plan B numérico:

```

Ecuaciones: ΣFy=0, ΣMA=0	- Si la integración simbólica se complica, se integra numéricamente (trapezoidal) y se ajusta $y(L)=0$.

### 2. Cortante V(x)

```Reacciones: RA + RB = ΣF

V(x) = RA + Σ(cargas a la izquierda de x)

``````Unidades: internamente todo en SI (m, N, Pa, m⁴). La app muestra/convierte unidades para entrada y salida (ej. m↔ft, N↔kN↔lb, etc.).



### 3. Momento M(x)

```

M(x) = ∫₀ˣ V(ξ)dξ + Σ(saltos por momentos)### Hiperestático (3+ apoyos)## Archivos y carpetas (para ubicarte, sin tocar código)



Para momentos concentrados:```

  M(x) = M_base(x) + M₀·H(x-a)

  donde H(x-a) = función Heaviside (0 si x<a, 1 si x≥a)Método: Compatibilidad de deflexiones- `frontend/app.py`: Interfaz de usuario (Streamlit). Aquí “vives” como usuario.

```

1. Sistema primario: 2 apoyos extremos- `backend/viga.py`: Núcleo de cálculo. Define la clase `Viga` y los tipos de carga (puntual, uniforme, triangular, trapezoidal, momento puntual). Construye V(x), M(x), θ(x), y(x).

### 4. Deflexión y(x)

```2. Apoyos intermedios = redundantes- `backend/calculos.py`: Tareas de apoyo (discretizar y armar tablas de resultados, máximos, etc.).

EI·d²y/dx² = M(x)

θ(x) = ∫ M/(EI) dx3. Resolver: [f]·{R} = -{δcargas}- `backend/utils.py`: Guardar CSV/PNG/JSON y manejo de rutas.

y(x) = ∫ θ dx

``````- `backend/units.py`: Catálogo de unidades y factores de conversión.



**Condiciones de borde:** `y(apoyo_i) = 0` para todos los apoyos- `backend/menus.py`: Menú de consola (opcional, no necesario para la app web).



------- `backend/__init__.py`: Empaquetado interno del backend.



## 💡 Verificación de resultados- `outputs/`: Carpeta de resultados (CSV, imágenes y configuraciones JSON exportadas).



### Fórmula de referencia (viga con carga uniforme)## 📂 Estructura del proyecto- `requirements.txt`: Lista de librerías de Python que necesita la app.

```

ymax = (5·w·L⁴)/(384·E·I)    [en el centro]- `README.md`: Este documento.

```

```

### Saltos característicos

- **V(x)**: Salto en cargas puntualesANALISIS/## Consejos rápidos para el reporte

- **M(x)**: Salto en momentos puntuales

- **y(x)**: Cero en todos los apoyos├── frontend/



### Verificar momentos puntuales│   └── app.py          # Interfaz web (Streamlit)- Verifica que el signo y la posición del máximo momento tengan sentido con tu diagrama de cargas.

```

✓ Momento positivo → Diagrama M(x) sube├── backend/- Con carga uniforme pura, compara la deflexión central con la fórmula $y_{max}=\tfrac{5 w L^4}{384 E I}$ como orden de magnitud.

✓ Momento negativo → Diagrama M(x) baja

✓ No afecta a V(x) (solo M cambia)│   ├── viga.py         # Clases: Viga, Carga, Apoyo- Saltos en V(x) ↔ cargas puntuales; saltos en M(x) ↔ momentos puntuales.

```

│   ├── calculos.py     # Generación de DataFrames y máximos

---

│   ├── units.py        # Conversiones de unidadesListo. Con esto puedes levantar casos de estudio, exportar resultados y adjuntar el JSON de configuración como evidencia de datos usados, sin escribir código.

## 📤 Exportación

│   └── utils.py        # Exportación (CSV, PNG, JSON)

- **CSV**: Tabla de valores (x, V, M, θ, y)

- **PNG**: Gráficas de diagramas├── outputs/            # Resultados exportados

- **JSON**: Configuración completa para reproducir el análisis├── requirements.txt    # Dependencias

└── README.md          # Este archivo

---```



## 🎓 Para tu reporte---



✅ Verifica signos y posiciones de máximos  ## 🧮 Proceso de cálculo

✅ Compara deflexión con fórmula teórica  

✅ Adjunta JSON como evidencia de configuración  ### 1. Reacciones

✅ Explica tipo de sistema (isostático/hiperestático)  ```

✅ Para momentos: verifica que el signo del salto coincida con la dirección del giro  Sistema isostático:

  ΣFy = 0 → RA + RB = ΣFi

---  ΣMA = 0 → RB·L = Σ(Fi·di)



## 📊 UnidadesSistema hiperestático:

  Matriz de flexibilidad + superposición

**Internamente:** Todo en SI (m, N, Pa, m⁴)  ```

**Interfaz:** Conversión automática entre sistemas (SI, Imperial, Mixto)

### 2. Cortante V(x)

---```

V(x) = RA + Σ(cargas a la izquierda de x)

## ⚠️ Notas importantes sobre momentos```



1. **Signo del momento es crítico:**### 3. Momento M(x)

   - Ingresa valores **positivos** para momentos antihorarios ↺```

   - Ingresa valores **negativos** para momentos horarios ↻M(x) = ∫₀ˣ V(ξ)dξ + Σ(saltos por momentos)

```

2. **En interfaz gráfica:**

   - El programa interpreta el signo según la convención estándar### 4. Deflexión y(x)

   - Si el diagrama M(x) salta en dirección inesperada, verifica el signo del momento```

EI·d²y/dx² = M(x)

3. **Equilibrio de momentos:**θ(x) = ∫ M/(EI) dx

   ```y(x) = ∫ θ dx

   ΣMA = 0```

   RB·L = Σ(P·d) + Σ(M_concentrados)

   ```**Condiciones de borde:** `y(apoyo_i) = 0` para todos los apoyos

   Los momentos concentrados entran directamente con su signo

---

---

## 💡 Verificación de resultados

**¿Dudas?** Revisa los comentarios en `backend/viga.py` para detalles de implementación.

### Fórmula de referencia (viga con carga uniforme)
```
ymax = (5·w·L⁴)/(384·E·I)    [en el centro]
```

### Saltos característicos
- **V(x)**: Salto en cargas puntuales
- **M(x)**: Salto en momentos puntuales
- **y(x)**: Cero en todos los apoyos

---

## 📤 Exportación

- **CSV**: Tabla de valores (x, V, M, θ, y)
- **PNG**: Gráficas de diagramas
- **JSON**: Configuración completa para reproducir el análisis

---

## 🎓 Para tu reporte

✅ Verifica signos y posiciones de máximos  
✅ Compara deflexión con fórmula teórica  
✅ Adjunta JSON como evidencia de configuración  
✅ Explica tipo de sistema (isostático/hiperestático)  

---

## 📊 Unidades

**Internamente:** Todo en SI (m, N, Pa, m⁴)  
**Interfaz:** Conversión automática entre sistemas (SI, Imperial, Mixto)

---

**¿Dudas?** Revisa los comentarios en `backend/viga.py` para detalles de implementación.
