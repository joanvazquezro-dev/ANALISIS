# Analizador de Vigas 🏗️# Analizador de Vigas 🏗️# Analizador de vigas (simplemente apoyadas) – Guía para alumnos de Ing. Civil



**Herramienta para análisis estructural de vigas** — Calcula reacciones, cortante, momento, pendiente y deflexión sin programar.



---**Herramienta para análisis estructural de vigas** — Calcula reacciones, cortante, momento, pendiente y deflexión sin programar.Herramienta sencilla para calcular y graficar cortante V(x), momento M(x), pendiente θ(x) y deflexión y(x) en vigas simplemente apoyadas, sin necesidad de programar.



## 🎯 ¿Qué hace esta aplicación?



Analiza vigas con múltiples configuraciones de apoyos y cargas, calculando:---## Qué calcula (en pocas palabras)



### **Reacciones en los apoyos**

Resuelve sistemas:

- **Isostáticos** (2 apoyos): Usa equilibrio estático## 🎯 ¿Qué hace esta aplicación?- Equilibrio estático para reacciones en apoyos A (x=0) y B (x=L):

- **Hiperestáticos** (3+ apoyos): Método de compatibilidad de deflexiones

  - $\sum F_y=0 \Rightarrow R_A + R_B = \sum F_i$

### **Diagramas estructurales**

- **V(x)** — Cortante: Suma de fuerzas verticalesAnaliza vigas con múltiples configuraciones de apoyos y cargas, calculando:  - $\sum M_A=0 \Rightarrow R_B\,L = \sum(F_i\,d_i) + \sum(M_{0j})$

- **M(x)** — Momento flector: Integración del cortante

- **θ(x)** — Pendiente: Derivada de la deflexión- Cortante V(x): suma de aportes de reacciones y cargas (método de tramos con funciones de Heaviside/Macaulay).

- **y(x)** — Deflexión: Curva elástica de la viga

### **Reacciones en los apoyos**- Momento M(x): integración de V(x) y saltos por momentos puntuales: $M(x)=\int_0^x V(\xi)\,d\xi + \sum M_{0j}\,H(x-a_j)$.

### **Convenciones de signo**

- Cargas hacia abajo → magnitud **positiva**Resuelve sistemas:- Pendiente y deflexión: $\theta(x)=\int \frac{M(x)}{E I}\,dx$ y $y(x)=\int \theta(x)\,dx$, aplicando condiciones de borde $y(0)=y(L)=0$.

- V(x) positivo → cortante hacia **arriba** a la izquierda

- M(x) positivo → fibras superiores en **compresión**- **Isostáticos** (2 apoyos): Usa equilibrio estático- Si el cálculo simbólico se complica, se usa un método numérico robusto (integración trapezoidal) que da resultados prácticos.

- Momento concentrado positivo → sentido **antihorario** ↺

- Momento concentrado negativo → sentido **horario** ↻- **Hiperestáticos** (3+ apoyos): Método de compatibilidad de deflexiones



---Convenciones de signo (usadas por la app):



## 🚀 Inicio rápido### **Diagramas estructurales**- Las cargas hacia abajo se ingresan con magnitud positiva.



### 1. Instalar dependencias- **V(x)** — Cortante: Suma de fuerzas verticales- V(x) positivo = reacción neta hacia arriba a la izquierda de la sección.

```powershell

pip install -r requirements.txt- **M(x)** — Momento flector: Integración del cortante- M(x) positivo con la convención habitual de “fibras superiores en compresión”.

```

- **θ(x)** — Pendiente: Derivada de la deflexión- Momentos puntuales introducen un salto en M(x); en el punto se toma $H(0)=\tfrac{1}{2}$.

### 2. Ejecutar aplicación

```powershell- **y(x)** — Deflexión: Curva elástica de la viga

streamlit run frontend/app.py

```## Cómo usar la app (sin programar)



### 3. Usar la interfaz### **Convenciones de signo**

1. **Barra lateral** → Define propiedades (L, E, I) y sistema de unidades

2. **Configurar apoyos** → Elige configuración predefinida o personalizada- Cargas hacia abajo → magnitud **positiva**1) Instalar dependencias (una sola vez):

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
