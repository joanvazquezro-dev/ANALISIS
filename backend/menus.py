"""Interfaces interactivas para el módulo de vigas."""
from __future__ import annotations

import textwrap
from typing import Callable, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import pandas as pd

from . import calculos, utils
from .viga import (
    Carga,
    CargaPuntual,
    CargaTriangular,
    CargaTrapezoidal,
    CargaUniforme,
    Viga,
)

try:  # Widgets son opcionales
    import ipywidgets as widgets
    from IPython.display import clear_output, display

    _WIDGETS_DISPONIBLES = True
except Exception:  # pragma: no cover - Spyder u otros entornos sin widgets
    widgets = None  # type: ignore
    display = None  # type: ignore
    clear_output = None  # type: ignore
    _WIDGETS_DISPONIBLES = False


def _solicitar_float(mensaje: str, minimo: Optional[float] = None, maximo: Optional[float] = None) -> float:
    while True:
        valor_str = input(mensaje)
        try:
            valor = float(valor_str)
        except ValueError:
            print("⚠️ Ingrese un número válido.")
            continue
        if minimo is not None and valor < minimo:
            print(f"⚠️ El valor debe ser mayor o igual que {minimo}.")
            continue
        if maximo is not None and valor > maximo:
            print(f"⚠️ El valor debe ser menor o igual que {maximo}.")
            continue
        return valor


def _solicitar_opcion(mensaje: str, opciones_validas: Tuple[str, ...]) -> str:
    while True:
        respuesta = input(mensaje).strip()
        if respuesta in opciones_validas:
            return respuesta
        print(f"⚠️ Opción inválida. Elija entre {', '.join(opciones_validas)}")


def _crear_viga_cli() -> Viga:
    print("\n➡️ Defina las propiedades de la viga")
    longitud = _solicitar_float("Longitud L (m): ", minimo=0.1)
    E = _solicitar_float("Módulo de elasticidad E (Pa): ", minimo=1e3)
    I = _solicitar_float("Momento de inercia I (m^4): ", minimo=1e-12)
    return Viga(longitud=longitud, E=E, I=I)


def _crear_carga_cli(viga: Viga) -> Optional[Carga]:
    print(
        textwrap.dedent(
            """
            Seleccione el tipo de carga:
              1) Carga puntual
              2) Carga distribuida uniforme
              3) Carga triangular (0 → w0)
              4) Carga triangular (w0 → 0)
              5) Carga trapezoidal general
              0) Terminar
            """
        )
    )
    opcion = _solicitar_opcion("Opción: ", ("0", "1", "2", "3", "4", "5"))
    if opcion == "0":
        return None

    if opcion == "1":
        P = _solicitar_float("Magnitud P (N): ")
        a = _solicitar_float("Posición a (m): ", minimo=0.0, maximo=viga.longitud)
        return CargaPuntual(P, a)

    inicio = _solicitar_float("Inicio de la carga (m): ", minimo=0.0, maximo=viga.longitud)
    fin = _solicitar_float("Fin de la carga (m): ", minimo=inicio, maximo=viga.longitud)

    if opcion == "2":
        w = _solicitar_float("Intensidad w (N/m): ")
        return CargaUniforme(w, inicio, fin)

    if opcion == "3":
        w0 = _solicitar_float("Intensidad máxima w0 (N/m) en el extremo derecho: ")
        return CargaTriangular(0.0, w0, inicio, fin)

    if opcion == "4":
        w0 = _solicitar_float("Intensidad máxima w0 (N/m) en el extremo izquierdo: ")
        return CargaTriangular(w0, 0.0, inicio, fin)

    w1 = _solicitar_float("Intensidad en el inicio w1 (N/m): ")
    w2 = _solicitar_float("Intensidad en el fin w2 (N/m): ")
    return CargaTrapezoidal(w1, w2, inicio, fin)


def _mostrar_resumen(viga: Viga) -> None:
    print("\n📌 Resumen de cargas: ")
    for linea in viga.resumen_cargas():
        print(f"  - {linea}")


def _generar_graficas(viga: Viga, df: pd.DataFrame) -> Dict[str, plt.Figure]:
    figuras: Dict[str, plt.Figure] = {}

    # Diagrama de carga
    fig_carga, ax_carga = plt.subplots(figsize=(7, 3))
    expr = viga.intensidad_total()
    try:
        x_vals, q_vals = calculos.discretizar(expr, viga.longitud)
        ax_carga.plot(x_vals, q_vals, label="q(x)", color="#1f77b4")
    except Exception:
        ax_carga.text(0.5, 0.5, "Sin cargas distribuidas", transform=ax_carga.transAxes, ha="center")
    for carga in viga.cargas:
        if isinstance(carga, CargaPuntual):
            ax_carga.vlines(carga.posicion, 0, -carga.magnitud, colors="crimson", linewidth=2)
            ax_carga.plot(carga.posicion, -carga.magnitud, "o", color="crimson")
    ax_carga.set_ylabel("q(x) [N/m]")
    ax_carga.set_xlabel("x [m]")
    ax_carga.set_title("Diagrama de carga")
    ax_carga.grid(True, alpha=0.3)
    figuras["carga"] = fig_carga

    # Cortante y momento
    fig_vm, (ax_v, ax_m) = plt.subplots(2, 1, figsize=(7, 6), sharex=True)
    ax_v.plot(df["x"], df["cortante"], color="#ff7f0e")
    ax_v.set_ylabel("V(x) [N]")
    ax_v.grid(True, alpha=0.3)

    ax_m.plot(df["x"], df["momento"], color="#2ca02c")
    ax_m.set_ylabel("M(x) [N·m]")
    ax_m.set_xlabel("x [m]")
    ax_m.grid(True, alpha=0.3)
    fig_vm.suptitle("Diagramas de esfuerzo cortante y momento flector")
    figuras["cortante_momento"] = fig_vm

    # Deflexión
    fig_def, ax_def = plt.subplots(figsize=(7, 3))
    ax_def.plot(df["x"], df["deflexion"], color="#9467bd")
    ax_def.set_ylabel("y(x) [m]")
    ax_def.set_xlabel("x [m]")
    ax_def.set_title("Curva elástica")
    ax_def.grid(True, alpha=0.3)
    figuras["deflexion"] = fig_def

    # Comparativa numérica
    comparacion = calculos.comparar_simbolico_numerico(viga, num_puntos=len(df))
    fig_comp, ax_comp = plt.subplots(figsize=(7, 3))
    ax_comp.plot(comparacion["x"], comparacion["deflexion_simbolica"], label="Simbólica")
    ax_comp.plot(comparacion["x"], comparacion["deflexion_numerica"], "--", label="Numérica")
    ax_comp.set_xlabel("x [m]")
    ax_comp.set_ylabel("y(x) [m]")
    ax_comp.set_title("Comparación simbólica vs numérica")
    ax_comp.legend()
    ax_comp.grid(True, alpha=0.3)
    figuras["comparacion"] = fig_comp

    return figuras


def _resolver_viga(viga: Viga) -> None:
    reacciones = viga.calcular_reacciones()
    print("\n✅ Reacciones:")
    print(f"  RA = {reacciones['RA']:.4f} N")
    print(f"  RB = {reacciones['RB']:.4f} N")

    df = calculos.generar_dataframe(viga)
    maximos = calculos.obtener_maximos(df)
    print("\n📈 Valores máximos:")
    print(utils.formatear_maximos(maximos))

    figuras = _generar_graficas(viga, df)

    exportar = _solicitar_opcion("\n¿Desea exportar resultados y gráficas? (s/n): ", ("s", "n"))
    if exportar == "s":
        ruta_tabla = utils.exportar_tabla(df, "resultados_viga")
        print(f"📝 Tabla guardada en {ruta_tabla}")
        for nombre, figura in figuras.items():
            ruta = utils.exportar_grafica(figura, nombre)
            print(f"🖼️ {nombre} → {ruta}")

    # Mostrar figuras en CLI
    plt.show(block=False)
    input("Presione Enter para continuar...")
    plt.close("all")


def iniciar_menu_cli() -> None:
    print("========================")
    print(" Analizador de Vigas 🧮")
    print("========================")

    ejemplos = {
        "1": Viga(6.0, 210e9, 8e-6),
        "2": Viga(8.0, 200e9, 1.2e-5),
    }
    ejemplos["1"].agregar_carga(CargaUniforme(5000.0, 0.0, 6.0))
    ejemplos["2"].agregar_carga(CargaPuntual(15000.0, 3.5))
    ejemplos["2"].agregar_carga(CargaUniforme(3000.0, 0.0, 8.0))

    while True:
        print(
            textwrap.dedent(
                """
                Opciones:
                  1) Crear nueva viga
                  2) Usar ejemplo 1 (L=6 m, carga uniforme)
                  3) Usar ejemplo 2 (L=8 m, carga combinada)
                  0) Salir
                """
            )
        )
        opcion = _solicitar_opcion("Seleccione una opción: ", ("0", "1", "2", "3"))
        if opcion == "0":
            print("Hasta pronto 👋")
            break
        if opcion == "1":
            viga = _crear_viga_cli()
            while True:
                carga = _crear_carga_cli(viga)
                if carga is None:
                    break
                viga.agregar_carga(carga)
            if not viga.cargas:
                print("⚠️ Agregue al menos una carga para continuar.")
                continue
            _mostrar_resumen(viga)
            _resolver_viga(viga)
        else:
            idx = opcion
            viga = Viga(**{k: getattr(ejemplos[idx], k) for k in ["longitud", "E", "I"]})
            for carga in ejemplos[idx].cargas:
                viga.agregar_carga(carga)
            _mostrar_resumen(viga)
            _resolver_viga(viga)


# --------------- Widgets en Jupyter ---------------


def _crear_carga_desde_widgets(viga: Viga, tipo: str, valores: Dict[str, float]) -> Carga:
    if tipo == "Carga puntual":
        return CargaPuntual(valores["magnitud"], valores["posicion"])
    if tipo == "Carga uniforme":
        return CargaUniforme(valores["intensidad"], valores["inicio"], valores["fin"])
    if tipo == "Carga triangular 0→w₀":
        return CargaTriangular(0.0, valores["intensidad"], valores["inicio"], valores["fin"])
    if tipo == "Carga triangular w₀→0":
        return CargaTriangular(valores["intensidad"], 0.0, valores["inicio"], valores["fin"])
    if tipo == "Carga trapezoidal":
        return CargaTrapezoidal(valores["intensidad_inicio"], valores["intensidad_fin"], valores["inicio"], valores["fin"])
    raise ValueError("Tipo de carga no reconocido")


def iniciar_menu_jupyter() -> None:
    if not _WIDGETS_DISPONIBLES:
        raise RuntimeError("ipywidgets no está disponible en este entorno")

    viga_actual: Optional[Viga] = None
    cargas: List[Carga] = []

    longitud = widgets.FloatText(description="L (m)", value=6.0, min=0.1)
    E = widgets.FloatText(description="E (Pa)", value=210e9, min=1e3)
    I = widgets.FloatText(description="I (m⁴)", value=8e-6, min=1e-12)

    tipo_carga = widgets.Dropdown(
        options=[
            "Carga puntual",
            "Carga uniforme",
            "Carga triangular 0→w₀",
            "Carga triangular w₀→0",
            "Carga trapezoidal",
        ],
        description="Carga",
    )

    magnitud = widgets.FloatText(description="P (N)", value=1000.0)
    posicion = widgets.FloatText(description="a (m)", value=2.0)
    intensidad = widgets.FloatText(description="w (N/m)", value=2000.0)
    inicio = widgets.FloatText(description="Inicio (m)", value=0.0)
    fin = widgets.FloatText(description="Fin (m)", value=3.0)
    intensidad_fin = widgets.FloatText(description="w₂ (N/m)", value=1000.0)

    boton_agregar = widgets.Button(description="Agregar carga", button_style="success")
    boton_calcular = widgets.Button(description="Calcular", button_style="primary")
    boton_limpiar = widgets.Button(description="Limpiar", button_style="warning")

    salida = widgets.Output()

    def _actualizar_visibilidad(*_):
        magnitud.layout.display = "none"
        posicion.layout.display = "none"
        intensidad.layout.display = "none"
        inicio.layout.display = "none"
        fin.layout.display = "none"
        intensidad_fin.layout.display = "none"

        if tipo_carga.value == "Carga puntual":
            magnitud.layout.display = ""
            posicion.layout.display = ""
        elif tipo_carga.value in {"Carga uniforme", "Carga triangular 0→w₀", "Carga triangular w₀→0"}:
            intensidad.layout.display = ""
            inicio.layout.display = ""
            fin.layout.display = ""
        elif tipo_carga.value == "Carga trapezoidal":
            inicio.layout.display = ""
            fin.layout.display = ""
            intensidad.layout.display = ""
            intensidad_fin.layout.display = ""

    _actualizar_visibilidad()
    tipo_carga.observe(_actualizar_visibilidad, "value")

    def _crear_viga():
        nonlocal viga_actual, cargas
        viga_actual = Viga(float(longitud.value), float(E.value), float(I.value))
        cargas = []

    _crear_viga()

    def _on_agregar(_):
        # Evitar ejecuciones múltiples con un flag de bloqueo
        if hasattr(_on_agregar, '_ejecutando') and _on_agregar._ejecutando:
            return
        _on_agregar._ejecutando = True
        
        # Deshabilitar temporalmente el botón para evitar clics múltiples
        boton_agregar.disabled = True
        
        try:
            if viga_actual is None:
                _crear_viga()
            
            # Validar que los valores sean razonables
            try:
                if float(longitud.value) <= 0:
                    raise ValueError("La longitud debe ser positiva")
                if float(E.value) <= 0:
                    raise ValueError("El módulo de elasticidad debe ser positivo")
                if float(I.value) <= 0:
                    raise ValueError("El momento de inercia debe ser positivo")
            except ValueError as e:
                with salida:
                    clear_output()
                    print(f"❌ Error en propiedades de la viga: {e}")
                return
            
            valores: Dict[str, float] = {
                "magnitud": float(magnitud.value),
                "posicion": float(posicion.value),
                "intensidad": float(intensidad.value),
                "intensidad_inicio": float(intensidad.value),
                "intensidad_fin": float(intensidad_fin.value),
                "inicio": float(inicio.value),
                "fin": float(fin.value),
            }
            
            try:
                carga = _crear_carga_desde_widgets(viga_actual, tipo_carga.value, valores)
                # Validar que la carga se puede agregar a la viga actual
                viga_temp = Viga(float(longitud.value), float(E.value), float(I.value))
                viga_temp.agregar_carga(carga)  # Esto validará los límites
            except Exception as exc:
                with salida:
                    clear_output()
                    print(f"❌ Error al crear carga: {exc}")
                return
            
            cargas.append(carga)
            with salida:
                # Limpiar salida completamente antes de mostrar
                clear_output(wait=True)
                # Mostrar solo las cargas actuales, sin acumular mensajes
                current_output = f"✅ Carga agregada: {carga.descripcion()}\n"
                current_output += f"📋 Cargas actuales ({len(cargas)}):\n"
                for i, c in enumerate(cargas, 1):
                    current_output += f"  {i}. {c.descripcion()}\n"
                print(current_output.strip())
                
        finally:
            # Reactivar el botón y liberar el flag
            boton_agregar.disabled = False
            _on_agregar._ejecutando = False

    def _on_calcular(_):
        # Evitar ejecuciones múltiples con un flag de bloqueo
        if hasattr(_on_calcular, '_ejecutando') and _on_calcular._ejecutando:
            return
        _on_calcular._ejecutando = True
        
        # Deshabilitar temporalmente el botón
        boton_calcular.disabled = True
        
        try:
            if not cargas:
                with salida:
                    clear_output(wait=True)
                    print("⚠️ Agregue al menos una carga.")
                return
            
            # Crear viga con validaciones
            viga = Viga(float(longitud.value), float(E.value), float(I.value))
            for carga in cargas:
                viga.agregar_carga(carga)
            
            # Calcular con manejo de errores
            with salida:
                clear_output(wait=True)
                print("🔄 Calculando...")
            
            reacciones = viga.calcular_reacciones()
            df = calculos.generar_dataframe(viga)
            maximos = calculos.obtener_maximos(df)
            figuras = _generar_graficas(viga, df)
            
            with salida:
                clear_output(wait=True)
                print("✅ Cálculo completado exitosamente!")
                print("\nReacciones:")
                ra, rb = reacciones.values()
                print(f"  RA = {ra:.3f} N | RB = {rb:.3f} N")
                print("\nValores máximos:")
                print(utils.formatear_maximos(maximos))
                display(df.head())
                for fig in figuras.values():
                    display(fig)
                    
        except Exception as e:
            with salida:
                clear_output(wait=True)
                print(f"❌ Error durante el cálculo: {e}")
                print("Verifique que las cargas y propiedades de la viga sean válidas.")
                import traceback
                print("\nDetalles del error:")
                print(traceback.format_exc())
                
        finally:
            # Reactivar el botón y liberar el flag
            boton_calcular.disabled = False
            _on_calcular._ejecutando = False

    def _on_limpiar(_):
        # Evitar ejecuciones múltiples con un flag de bloqueo
        if hasattr(_on_limpiar, '_ejecutando') and _on_limpiar._ejecutando:
            return
        _on_limpiar._ejecutando = True
        
        # Deshabilitar temporalmente el botón
        boton_limpiar.disabled = True
        
        try:
            nonlocal cargas
            _crear_viga()
            cargas = []  # Limpiar explícitamente la lista de cargas
            
            with salida:
                clear_output(wait=True)
                print("🔄 Campos reiniciados.")
                print("📋 Lista de cargas vaciada.")
                
        finally:
            # Reactivar el botón y liberar el flag
            boton_limpiar.disabled = False
            _on_limpiar._ejecutando = False

    boton_agregar.on_click(_on_agregar)
    boton_calcular.on_click(_on_calcular)
    boton_limpiar.on_click(_on_limpiar)

    panel_cargas = widgets.VBox([
        tipo_carga,
        magnitud,
        posicion,
        intensidad,
        intensidad_fin,
        inicio,
        fin,
        widgets.HBox([boton_agregar, boton_calcular, boton_limpiar]),
    ])

    layout = widgets.VBox([
        widgets.HTML("<h2>Analizador interactivo de vigas</h2>"),
        widgets.HBox([longitud, E, I]),
        panel_cargas,
        salida,
    ])

    display(layout)
