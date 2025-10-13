# Analizador de vigas (simplemente apoyadas) – Guía para alumnos de Ing. Civil

Herramienta sencilla para calcular y graficar cortante V(x), momento M(x), pendiente θ(x) y deflexión y(x) en vigas simplemente apoyadas, sin necesidad de programar.

## Qué calcula (en pocas palabras)

- Equilibrio estático para reacciones en apoyos A (x=0) y B (x=L):
  - $\sum F_y=0 \Rightarrow R_A + R_B = \sum F_i$
  - $\sum M_A=0 \Rightarrow R_B\,L = \sum(F_i\,d_i) + \sum(M_{0j})$
- Cortante V(x): suma de aportes de reacciones y cargas (método de tramos con funciones de Heaviside/Macaulay).
- Momento M(x): integración de V(x) y saltos por momentos puntuales: $M(x)=\int_0^x V(\xi)\,d\xi + \sum M_{0j}\,H(x-a_j)$.
- Pendiente y deflexión: $\theta(x)=\int \frac{M(x)}{E I}\,dx$ y $y(x)=\int \theta(x)\,dx$, aplicando condiciones de borde $y(0)=y(L)=0$.
- Si el cálculo simbólico se complica, se usa un método numérico robusto (integración trapezoidal) que da resultados prácticos.

Convenciones de signo (usadas por la app):
- Las cargas hacia abajo se ingresan con magnitud positiva.
- V(x) positivo = reacción neta hacia arriba a la izquierda de la sección.
- M(x) positivo con la convención habitual de “fibras superiores en compresión”.
- Momentos puntuales introducen un salto en M(x); en el punto se toma $H(0)=\tfrac{1}{2}$.

## Cómo usar la app (sin programar)

1) Instalar dependencias (una sola vez):

```powershell
pip install -r requirements.txt
```

2) Ejecutar la interfaz:

```powershell
streamlit run frontend/app.py
```

3) En la barra lateral:
- Elige sistema de unidades y define L, E, I.
- Agrega cargas (puntual, uniforme, triangular, trapezoidal o momento puntual) y su posición/rango.
- Pulsa “Calcular”.

4) Pestaña “Resultados”:
- Verás RA y RB, tabla de valores y diagramas de q(x), V(x), M(x), y(x).
- Puedes descargar los datos como CSV y guardar la configuración en JSON.

Sugerencia: si aplicas un momento exactamente en un apoyo (x=0 o x=L), la app permite decidir si ese momento produce salto dentro del vano o sólo ajusta las reacciones.

## Tipos de carga soportados (qué hacen en V y M)

- Carga puntual P en x=a: salto en V(x) y cambio de pendiente en M(x).
- Carga uniforme w entre [a,b]: V(x) varía lineal; M(x) cuadrático en ese tramo.
- Carga triangular (0→w₀ o w₀→0): V(x) y M(x) varían como polinomios de orden 2 y 3 respectivamente.
- Carga trapezoidal (w₁→w₂): caso general lineal por tramo.
- Momento puntual M₀ en x=a: no cambia V(x), introduce salto M₀ en M(x).

## Cómo se calculan las cosas (un poco más de detalle)

1) Reacciones: con $\sum F=0$ y $\sum M_A=0$.
2) Cortante V(x):
	- Se arma con funciones de Heaviside/Macaulay para cada carga y las reacciones.
3) Momento M(x):
	- $M(x)=\int_0^x V(\xi)\,d\xi$.
	- Si hay momentos puntuales, se suman saltos $M_0\,H(x-a)$.
4) Pendiente y deflexión:
	- $\theta=\int M/(EI)$ y $y=\int \theta$.
	- Se imponen $y(0)=y(L)=0$ para determinar constantes.
5) Plan B numérico:
	- Si la integración simbólica se complica, se integra numéricamente (trapezoidal) y se ajusta $y(L)=0$.

Unidades: internamente todo en SI (m, N, Pa, m⁴). La app muestra/convierte unidades para entrada y salida (ej. m↔ft, N↔kN↔lb, etc.).

## Archivos y carpetas (para ubicarte, sin tocar código)

- `frontend/app.py`: Interfaz de usuario (Streamlit). Aquí “vives” como usuario.
- `backend/viga.py`: Núcleo de cálculo. Define la clase `Viga` y los tipos de carga (puntual, uniforme, triangular, trapezoidal, momento puntual). Construye V(x), M(x), θ(x), y(x).
- `backend/calculos.py`: Tareas de apoyo (discretizar y armar tablas de resultados, máximos, etc.).
- `backend/utils.py`: Guardar CSV/PNG/JSON y manejo de rutas.
- `backend/units.py`: Catálogo de unidades y factores de conversión.
- `backend/menus.py`: Menú de consola (opcional, no necesario para la app web).
- `backend/__init__.py`: Empaquetado interno del backend.
- `outputs/`: Carpeta de resultados (CSV, imágenes y configuraciones JSON exportadas).
- `requirements.txt`: Lista de librerías de Python que necesita la app.
- `README.md`: Este documento.

## Consejos rápidos para el reporte

- Verifica que el signo y la posición del máximo momento tengan sentido con tu diagrama de cargas.
- Con carga uniforme pura, compara la deflexión central con la fórmula $y_{max}=\tfrac{5 w L^4}{384 E I}$ como orden de magnitud.
- Saltos en V(x) ↔ cargas puntuales; saltos en M(x) ↔ momentos puntuales.

Listo. Con esto puedes levantar casos de estudio, exportar resultados y adjuntar el JSON de configuración como evidencia de datos usados, sin escribir código.

