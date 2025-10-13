import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Helper compatibilidad para rerun (Streamlit >=1.27 usa st.rerun())
if not hasattr(st, "experimental_rerun"):
    def _compat_rerun():
        st.rerun()
    st.experimental_rerun = _compat_rerun  # type: ignore[attr-defined]

# Helper para limpiar resultados evitando dejar la clave con valor None
def reset_resultados():
    st.session_state.pop("resultados", None)

# Asegurar path al backend
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from backend.viga import (
    Viga,
    CargaPuntual,
    CargaUniforme,
    CargaTriangular,
    CargaTrapezoidal,
        CargaMomento,
)
from backend.calculos import generar_dataframe, obtener_maximos, discretizar
from backend.utils import exportar_tabla, exportar_grafica, asegurar_directorios, convertir_dataframe_export
# Añadimos import de nueva utilidad
from backend.utils import exportar_configuracion

from backend.units import (
    LENGTH_UNITS,
    FORCE_UNITS,
    DIST_LOAD_UNITS,
    E_UNITS,
    INERCIA_UNITS,
    DEFLEXION_DISPLAY,
    UNIT_SYSTEMS,
)

st.set_page_config(page_title="Analizador de Vigas", layout="wide")
st.title("🧮 Analizador de Vigas - Curva Elástica")
st.markdown(
    "**Interfaz interactiva** para análisis de vigas simplemente apoyadas. "
    "Agrega cargas, genera diagramas y verifica el principio de superposición."
)

# Detección simple del tema para ajustar colores (fallback a claro)
try:
    _theme_base = st.get_option("theme.base")  # 'light' o 'dark'
except Exception:
    _theme_base = "light"
IS_DARK = (_theme_base == "dark")

# Ajustes CSS con soporte a modo oscuro usando media queries
CUSTOM_CSS = """
<style>
    .load-box { padding:0.4rem 0.6rem; background:#fafafa; border:1px solid #e3e3e3; border-radius:6px; }
    .stMetric { background:#f5f7fa; border-radius:8px; padding:0.25rem 0.5rem; }
    button[kind="primary"] { font-weight:600; }
    /* Ajustes modo oscuro */
    @media (prefers-color-scheme: dark) {
        .load-box { background:#1e1f26; border:1px solid #3a3d46; color:#e6e6e6; }
        .stMetric { background:#242730; color:#e6e6e6; }
        /* Tablas: forzar contraste en celdas claras */
        .stDataFrame tbody tr td { color:#e0e0e0; }
        .stDataFrame thead tr th { color:#ffffff; }
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Estilo Matplotlib acorde al modo
if IS_DARK:
    plt.style.use('dark_background')
    # Ajuste de colores de rejilla más sutil
    plt.rcParams['grid.color'] = '#444444'
else:
    # Asegurar estilo por defecto (por si el usuario cambió estilos previamente)
    plt.rcParams.update(plt.rcParamsDefault)

# ----------------- Helpers de conversión -----------------
# Internamente todo en SI. Las funciones to_si_* multiplican por factor.

def to_si_L(v, u): return v * LENGTH_UNITS[u]

def to_si_F(v, u): return v * FORCE_UNITS[u]

def to_si_w(v, u): return v * DIST_LOAD_UNITS[u]

def to_si_E(v, u): return v * E_UNITS[u]

def to_si_I(v, u): return v * INERCIA_UNITS[u]

def label_with_unit(base, unit): return f"{base} ({unit})"

# ----------------- Estado inicial -----------------
_defaults_si = {
    "L_si": 6.0,
    "E_si": 210e9,
    "I_si": 8e-6,
    "P_si": 1000.0,
    "a_si": 2.0,
    "w_si": 2000.0,
    "w1_si": 3000.0,
    "w2_si": 1000.0,
    "inicio_si": 0.0,
    "fin_si": 3.0,
}
for k, v in _defaults_si.items():
    st.session_state.setdefault(k, v)
st.session_state.setdefault("unit_system", "SI (N, m)")

st.sidebar.markdown("### Sistema de unidades")
chosen_system = st.sidebar.selectbox("Sistema", list(UNIT_SYSTEMS.keys()), key="unit_system")
sys_map = UNIT_SYSTEMS[chosen_system]

u_len = sys_map["len"]
u_force = sys_map["force"]
u_w = sys_map["w"]
u_E = sys_map["E"]
u_I = sys_map["I"]
u_defl_disp = sys_map["defl"]

with st.sidebar.expander("Unidades de exportación", expanded=False):
    exp_len = st.selectbox("Longitud exp", list(LENGTH_UNITS.keys()), key="exp_len")
    exp_force = st.selectbox("Fuerza exp", list(FORCE_UNITS.keys()), key="exp_force")
    exp_defl = st.selectbox("Deflexión exp", list(DEFLEXION_DISPLAY.keys()), key="exp_defl")

with st.sidebar:
    st.header("Propiedades de la viga")
    L_input = st.number_input(label_with_unit("Longitud L", u_len), min_value=0.1,
                              value=st.session_state.L_si / LENGTH_UNITS[u_len], step=0.5, key='L_input')
    E_input = st.number_input(label_with_unit("Módulo E", u_E),
                              value=st.session_state.E_si / E_UNITS[u_E], format="%.4e", key='E_input')
    I_input = st.number_input(label_with_unit("Momento de inercia I", u_I),
                              value=st.session_state.I_si / INERCIA_UNITS[u_I], format="%.6e", key='I_input')

    # Actualizar SI
    st.session_state.L_si = L_input * LENGTH_UNITS[u_len]
    st.session_state.E_si = E_input * E_UNITS[u_E]
    st.session_state.I_si = I_input * INERCIA_UNITS[u_I]

    L = st.session_state.L_si
    E = st.session_state.E_si
    I = st.session_state.I_si

    st.markdown("---")
    st.header("Agregar carga")
    tipo = st.selectbox(
        "Tipo de carga",
        [
            "Carga puntual",
            "Momento puntual",
            "Carga uniforme",
            "Carga triangular 0→w₀",
            "Carga triangular w₀→0",
            "Carga trapezoidal",
        ],
    )

    if "cargas" not in st.session_state:
        st.session_state.cargas = []
    if "viga_version" not in st.session_state:
        st.session_state.viga_version = 0

    # Entradas dependientes
    if tipo == "Carga puntual":
        P_input = st.number_input(label_with_unit("P", u_force),
                                  value=st.session_state.P_si / FORCE_UNITS[u_force], step=max(1.0, st.session_state.P_si / FORCE_UNITS[u_force] * 0.25), key='P_input')
        a_input = st.number_input(label_with_unit("Posición a", u_len), min_value=0.0, max_value=L_input,
                                  value=st.session_state.a_si / LENGTH_UNITS[u_len], step=0.1, key='a_input')
        st.session_state.P_si = P_input * FORCE_UNITS[u_force]
        st.session_state.a_si = a_input * LENGTH_UNITS[u_len]
        P = st.session_state.P_si
        a = st.session_state.a_si
    elif tipo == "Momento puntual":
        M_input = st.number_input(label_with_unit("M", f"{u_force}·{u_len}"), value=1000.0, step=100.0, key='M_input')
        aM_input = st.number_input(label_with_unit("Posición a", u_len), min_value=0.0, max_value=L_input,
                                   value=st.session_state.a_si / LENGTH_UNITS[u_len], step=0.1, key='aM_input')
        en_apoyo = (abs(aM_input - 0.0) < 1e-12) or (abs(aM_input - L_input) < 1e-12)
        en_vano_flag = True
        if en_apoyo:
            en_vano_flag = st.checkbox("Aplicar salto dentro del vano si está en apoyo", value=True, help="Si desmarcas, el momento en apoyo no introduce salto en M(x) dentro del vano (solo afecta reacciones).")
        M = M_input * FORCE_UNITS[u_force] * LENGTH_UNITS[u_len]
        aM = aM_input * LENGTH_UNITS[u_len]
    else:
        inicio_input = st.number_input(label_with_unit("Inicio", u_len), min_value=0.0, max_value=L_input,
                                       value=st.session_state.inicio_si / LENGTH_UNITS[u_len], step=0.1, key="inicio")
        fin_input = st.number_input(label_with_unit("Fin", u_len), min_value=inicio_input, max_value=L_input,
                                    value=st.session_state.fin_si / LENGTH_UNITS[u_len], step=0.1, key="fin")
        st.session_state.inicio_si = inicio_input * LENGTH_UNITS[u_len]
        st.session_state.fin_si = fin_input * LENGTH_UNITS[u_len]
        inicio = st.session_state.inicio_si
        fin = st.session_state.fin_si
        if tipo in {"Carga uniforme", "Carga triangular 0→w₀", "Carga triangular w₀→0"}:
            w_input = st.number_input(label_with_unit("w", u_w), value=st.session_state.w_si / DIST_LOAD_UNITS[u_w],
                                      step=max(1.0, st.session_state.w_si / DIST_LOAD_UNITS[u_w] * 0.25), key='w_input')
            st.session_state.w_si = w_input * DIST_LOAD_UNITS[u_w]
            w = st.session_state.w_si
        if tipo == "Carga trapezoidal":
            w1_input = st.number_input(label_with_unit("w₁", u_w), value=st.session_state.w1_si / DIST_LOAD_UNITS[u_w],
                                       step=max(1.0, st.session_state.w1_si / DIST_LOAD_UNITS[u_w] * 0.25), key='w1_input')
            w2_input = st.number_input(label_with_unit("w₂", u_w), value=st.session_state.w2_si / DIST_LOAD_UNITS[u_w],
                                       step=max(1.0, st.session_state.w2_si / DIST_LOAD_UNITS[u_w] * 0.25), key='w2_input')
            st.session_state.w1_si = w1_input * DIST_LOAD_UNITS[u_w]
            st.session_state.w2_si = w2_input * DIST_LOAD_UNITS[u_w]
            w1 = st.session_state.w1_si
            w2 = st.session_state.w2_si

    if st.button("➕ Agregar carga", help="Añadir la carga definida"):
        try:
            if tipo == "Carga puntual":
                carga = CargaPuntual(P, a)
            elif tipo == "Momento puntual":
                # Si no está en apoyo, en_vano es irrelevante; si está en apoyo, usar el flag seleccionado
                carga = CargaMomento(M, aM, en_vano=en_vano_flag)
            elif tipo == "Carga uniforme":
                carga = CargaUniforme(w, inicio, fin)
            elif tipo == "Carga triangular 0→w₀":
                carga = CargaTriangular(0.0, w, inicio, fin)
            elif tipo == "Carga triangular w₀→0":
                carga = CargaTriangular(w, 0.0, inicio, fin)
            elif tipo == "Carga trapezoidal":
                carga = CargaTrapezoidal(w1, w2, inicio, fin)
            else:
                raise ValueError("Tipo de carga no reconocido")
            viga_tmp = Viga(L, E, I)
            viga_tmp.agregar_carga(carga)
            st.session_state.cargas.append(carga)
            st.success(f"Carga agregada: {carga.descripcion()}")
        except Exception as e:
            st.error(f"Error al agregar carga: {e}")

    if st.button("🗑️ Limpiar cargas", help="Eliminar todas las cargas"):
        st.session_state.cargas = []
        st.info("Cargas eliminadas.")

    with st.expander("⚙️ Opciones avanzadas"):
        exportar = st.checkbox("Exportar resultados al calcular", value=True)
        num_puntos = st.slider("Resolución (n puntos)", min_value=100, max_value=1200, value=400, step=100)
        auto_recalc = st.checkbox("Recalcular automáticamente al editar cargas", value=True)
        # Modo debug simbólico deshabilitado (forzado a False)
        debug_mode = False
        if st.button("♻️ Forzar recalcular ahora"):
            reset_resultados()
            st.experimental_rerun()
        st.caption("Mayor resolución = más precisión pero más tiempo de cálculo.")
    do_calc = st.button("🔄 Calcular", type="primary")

# ----------------- Tabs principales -----------------

tabs = st.tabs(["🧱 Cargas", "📊 Resultados", "🧪 Verificación"])

# Helper graficado q(x) reutilizable

def plot_q(ax, cargas, L, E, I, u_len, u_w, u_force):
    if not cargas:
        ax.text(0.5,0.5,"(Sin cargas)", ha='center', transform=ax.transAxes)
        return
    v_tmp = Viga(L, E, I)
    for c in cargas:
        v_tmp.agregar_carga(c)
    try:
        expr_q = v_tmp.intensidad_total()
        xs_q, q_vals = discretizar(expr_q, v_tmp.longitud, 300)
        ax.plot(xs_q / LENGTH_UNITS[u_len], q_vals / DIST_LOAD_UNITS[u_w], color="#1f77b4")
        for c in v_tmp.cargas:
            if isinstance(c, CargaPuntual):
                ax.vlines(c.posicion / LENGTH_UNITS[u_len], 0, -c.magnitud / FORCE_UNITS[u_force], colors="crimson")
            elif isinstance(c, CargaMomento):
                xpos = c.posicion / LENGTH_UNITS[u_len]
                ax.scatter([xpos], [0], color="purple", marker="o")
    except Exception:
        ax.text(0.5,0.5,"(Error q(x))", ha='center', transform=ax.transAxes)
    ax.set_xlabel(f"x [{u_len}]")
    ax.set_ylabel(f"q [{u_w}]")
    ax.grid(alpha=0.3)

with tabs[0]:
    st.subheader("Cargas actuales")

    def format_carga_unidades(carga) -> str:
        if isinstance(carga, CargaPuntual):
            return f"P={carga.magnitud/ FORCE_UNITS[u_force]:.3g} {u_force} @ x={carga.posicion/ LENGTH_UNITS[u_len]:.3g} {u_len}"
        if isinstance(carga, CargaMomento):
            extra = " (vano)" if getattr(carga, "en_vano", True) else " (apoyo)"
            return (f"M={carga.magnitud/(FORCE_UNITS[u_force]*LENGTH_UNITS[u_len]):.3g} {u_force}·{u_len} @ x={carga.posicion/ LENGTH_UNITS[u_len]:.3g} {u_len}{extra}")
        if isinstance(carga, CargaUniforme):
            return (f"w={carga.intensidad/ DIST_LOAD_UNITS[u_w]:.3g} {u_w} entre "
                    f"{carga.inicio/ LENGTH_UNITS[u_len]:.3g}-{carga.fin/ LENGTH_UNITS[u_len]:.3g} {u_len}")
        if isinstance(carga, CargaTriangular):
            return (f"Triangular ({carga.intensidad_inicio/ DIST_LOAD_UNITS[u_w]:.2g}→{carga.intensidad_fin/ DIST_LOAD_UNITS[u_w]:.2g} {u_w}) "
                    f"{carga.inicio/ LENGTH_UNITS[u_len]:.3g}-{carga.fin/ LENGTH_UNITS[u_len]:.3g} {u_len}")
        if isinstance(carga, CargaTrapezoidal):
            return (f"Trapezoidal ({carga.intensidad_inicio/ DIST_LOAD_UNITS[u_w]:.2g}→{carga.intensidad_fin/ DIST_LOAD_UNITS[u_w]:.2g} {u_w}) "
                    f"{carga.inicio/ LENGTH_UNITS[u_len]:.3g}-{carga.fin/ LENGTH_UNITS[u_len]:.3g} {u_len}")
        return carga.descripcion()

    st.session_state.setdefault('edit_index', None)
    if not st.session_state.cargas:
        st.info("No hay cargas definidas todavía.")
    else:
        for idx, carga in enumerate(st.session_state.cargas):
            cols = st.columns([6,1,1,1])
            with cols[0]:
                st.markdown(f"<div class='load-box'>**{idx+1}.** {format_carga_unidades(carga)}</div>", unsafe_allow_html=True)
            with cols[1]:
                if st.button("✏️", key=f"ed_{idx}", help="Editar carga"):
                    st.session_state.edit_index = idx
            with cols[2]:
                if st.button("📄", key=f"dup_{idx}", help="Duplicar carga"):
                    st.session_state.cargas.append(carga)
                    reset_resultados()
                    if st.session_state.get('auto_recalc', True):
                        st.experimental_rerun()
            with cols[3]:
                if st.button("❌", key=f"del_{idx}", help="Eliminar carga"):
                    st.session_state.cargas.pop(idx)
                    reset_resultados()
                    if st.session_state.get('auto_recalc', True):
                        st.experimental_rerun()

        if st.session_state.edit_index is not None and 0 <= st.session_state.edit_index < len(st.session_state.cargas):
            ed = st.session_state.edit_index
            carga_ed = st.session_state.cargas[ed]
            st.markdown(f"#### Editar carga {ed+1}")
            with st.form(f"edit_form_{ed}"):
                if isinstance(carga_ed, CargaPuntual):
                    newP = st.number_input("Nueva P", value=float(carga_ed.magnitud))
                    newA = st.number_input("Nueva posición", value=float(carga_ed.posicion), min_value=0.0, max_value=float(L))
                elif isinstance(carga_ed, CargaMomento):
                    newM = st.number_input("Nuevo M", value=float(carga_ed.magnitud))
                    newA = st.number_input("Nueva posición", value=float(carga_ed.posicion), min_value=0.0, max_value=float(L))
                    en_apoyo_ed = (abs(newA - 0.0) < 1e-12) or (abs(newA - float(L)) < 1e-12)
                    newEnVano = carga_ed.en_vano
                    if en_apoyo_ed:
                        newEnVano = st.checkbox("Aplicar salto dentro del vano si está en apoyo", value=bool(carga_ed.en_vano), key=f"en_vano_ed_{ed}")
                elif isinstance(carga_ed, CargaUniforme):
                    newP = st.number_input("Nueva w", value=float(carga_ed.intensidad))
                    newIni = st.number_input("Nuevo inicio", value=float(carga_ed.inicio), min_value=0.0, max_value=float(L))
                    newFin = st.number_input("Nuevo fin", value=float(carga_ed.fin), min_value=newIni, max_value=float(L))
                elif isinstance(carga_ed, CargaTrapezoidal):
                    newP1 = st.number_input("Nueva w1", value=float(carga_ed.intensidad_inicio))
                    newP2 = st.number_input("Nueva w2", value=float(carga_ed.intensidad_fin))
                    newIni = st.number_input("Nuevo inicio", value=float(carga_ed.inicio), min_value=0.0, max_value=float(L))
                    newFin = st.number_input("Nuevo fin", value=float(carga_ed.fin), min_value=newIni, max_value=float(L))
                save = st.form_submit_button("Guardar cambios")
                cancel = st.form_submit_button("Cancelar")
                if cancel:
                    st.session_state.edit_index = None
                    st.experimental_rerun()
                if save:
                    try:
                        if isinstance(carga_ed, CargaPuntual):
                            carga_ed.magnitud = newP
                            carga_ed.posicion = newA
                        elif isinstance(carga_ed, CargaMomento):
                            carga_ed.magnitud = newM
                            carga_ed.posicion = newA
                            carga_ed.en_vano = newEnVano
                        elif isinstance(carga_ed, CargaUniforme):
                            carga_ed.intensidad = newP
                            carga_ed.inicio = newIni
                            carga_ed.fin = newFin
                        elif isinstance(carga_ed, CargaTrapezoidal):
                            carga_ed.intensidad_inicio = newP1
                            carga_ed.intensidad_fin = newP2
                            carga_ed.inicio = newIni
                            carga_ed.fin = newFin
                        st.success("Carga actualizada")
                        reset_resultados()
                        st.session_state.edit_index = None
                        if st.session_state.get('auto_recalc', True):
                            st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Error al actualizar: {e}")

    st.markdown("### Vista previa diagrama de carga")
    fig_prev, ax_prev = plt.subplots(figsize=(6,2.3))
    plot_q(ax_prev, st.session_state.cargas, L, E, I, u_len, u_w, u_force)
    st.pyplot(fig_prev)

    if do_calc:
        if not st.session_state.cargas:
            st.warning("Agrega al menos una carga.")
        else:
            try:
                viga = Viga(L, E, I, debug=debug_mode)
                for c in st.session_state.cargas:
                    viga.agregar_carga(c)
                df = generar_dataframe(viga, num_puntos=num_puntos)
                st.session_state.last_df_si = df
                maximos = obtener_maximos(df)
                reacciones = viga.calcular_reacciones()
                st.session_state["resultados"] = {
                    "df": df,
                    "maximos": maximos,
                    "reacciones": reacciones,
                    "L": L,
                    "E": E,
                    "I": I,
                    # Guardamos lista de cargas para exportación futura
                    "cargas": list(st.session_state.cargas),
                }
                if exportar:
                    asegurar_directorios()
                    ruta_tabla = exportar_tabla(df, "resultados_viga")
                    # Exportar configuración JSON automáticamente
                    ruta_cfg = exportar_configuracion(L, E, I, st.session_state.cargas, nombre="config_viga")
                    st.info(f"CSV guardado en {ruta_tabla}\nConfig JSON en {ruta_cfg}")
                st.success("Cálculo completado. Revisa la pestaña Resultados.")
            except Exception as e:
                st.error(f"Error en cálculo: {e}")

with tabs[1]:
    st.subheader("Resultados del análisis")
    data = st.session_state.get("resultados")
    if not data or not isinstance(data, dict) or "df" not in data:
        st.info("Realiza un cálculo en la pestaña Cargas.")
    else:
        df = data["df"]
        maximos = data["maximos"]
        reacciones = data["reacciones"]
        # Siempre mostrar en las unidades de exportación seleccionadas
        disp_len, disp_force, disp_defl = exp_len, exp_force, exp_defl
        # DataFrame convertido para visualización (copia)
        df_disp = convertir_dataframe_export(df, disp_len, disp_force, disp_defl)

        m1, m2, m3 = st.columns(3)
        m1.metric("RA", f"{reacciones['RA']/FORCE_UNITS[disp_force]:.3f} {disp_force}")
        m2.metric("RB", f"{reacciones['RB']/FORCE_UNITS[disp_force]:.3f} {disp_force}")
        if "deflexion" in maximos:
            xdef, ydef = maximos["deflexion"]
            m3.metric("|y|max", f"{ydef/DEFLEXION_DISPLAY[disp_defl]:.3e} {disp_defl}")

        st.markdown("### Tabla (primeras filas)")
        # Renombrar columnas con unidades mostradas
        rename_cols = {}
        if "x" in df_disp: rename_cols["x"] = f"x [{disp_len}]"
        if "cortante" in df_disp: rename_cols["cortante"] = f"cortante [{disp_force}]"
        if "momento" in df_disp: rename_cols["momento"] = f"momento [{disp_force}·{disp_len}]"
        if "deflexion" in df_disp: rename_cols["deflexion"] = f"deflexion [{disp_defl}]"
        st.dataframe(df_disp.rename(columns=rename_cols).head(), use_container_width=True)

        with st.expander("📌 Valores máximos"):
            for clave, (xpos, val) in maximos.items():
                if clave == "cortante":
                    val_conv = val / FORCE_UNITS[disp_force]
                    st.write(f"{clave}: {val_conv:.4e} {disp_force} en x={xpos/LENGTH_UNITS[disp_len]:.3f} {disp_len}")
                elif clave == "momento":
                    val_conv = val / (FORCE_UNITS[disp_force]*LENGTH_UNITS[disp_len])
                    st.write(f"{clave}: {val_conv:.4e} {disp_force}·{disp_len} en x={xpos/LENGTH_UNITS[disp_len]:.3f} {disp_len}")
                elif clave == "deflexion":
                    val_conv = val / DEFLEXION_DISPLAY[disp_defl]
                    st.write(f"{clave}: {val_conv:.4e} {disp_defl} en x={xpos/LENGTH_UNITS[disp_len]:.3f} {disp_len}")
                elif clave == "pendiente":
                    st.write(f"{clave}: {val:.4e} rad en x={xpos/LENGTH_UNITS[disp_len]:.3f} {disp_len}")
                else:
                    st.write(f"{clave}: {val:.4e} (SI) en x={xpos/LENGTH_UNITS[disp_len]:.3f} {disp_len}")

        st.markdown("### Diagramas")
        gtab = st.tabs(["Carga q(x)", "Cortante/Momento", "Deflexión"])
        with gtab[0]:
            fig1, ax1 = plt.subplots(figsize=(6,2.4))
            # Para q(x) se usa siempre el sistema actual (carga definida). Podría ampliarse a export.
            plot_q(ax1, st.session_state.cargas, data['L'], data['E'], data['I'], u_len, u_w, u_force)
            st.pyplot(fig1)
        with gtab[1]:
            fig2, (axv, axm) = plt.subplots(2,1, figsize=(6,5), sharex=True)
            axv.plot(df["x"] / LENGTH_UNITS[disp_len], df["cortante"] / FORCE_UNITS[disp_force], color="#ff7f0e")
            axv.set_ylabel(f"V [{disp_force}]")
            axv.grid(alpha=0.3)
            axm.plot(df["x"] / LENGTH_UNITS[disp_len], df["momento"] / (FORCE_UNITS[disp_force]*LENGTH_UNITS[disp_len]), color="#2ca02c")
            axm.set_ylabel(f"M [{disp_force}·{disp_len}]")
            axm.set_xlabel(f"x [{disp_len}]")
            axm.grid(alpha=0.3)
            st.pyplot(fig2)
        with gtab[2]:
            fig3, ax3 = plt.subplots(figsize=(6,2.4))
            ax3.plot(df["x"] / LENGTH_UNITS[disp_len], df["deflexion"] / DEFLEXION_DISPLAY[disp_defl], color="#9467bd")
            ax3.set_ylabel(f"y [{disp_defl}]")
            ax3.set_xlabel(f"x [{disp_len}]")
            ax3.grid(alpha=0.3)
            st.pyplot(fig3)

        st.markdown("### Descargas")
        df_export = convertir_dataframe_export(df, exp_len, exp_force, exp_defl)
        st.download_button(
            label=f"⬇️ CSV ({exp_len}, {exp_force}, {exp_defl})",
            data=df_export.to_csv(index=False).encode(),
            file_name="resultados_viga_convertidos.csv",
            mime="text/csv",
        )
        # Botón adicional para exportar configuración bajo demanda
        if st.button("💾 Exportar configuración (JSON)"):
            try:
                ruta_cfg = exportar_configuracion(data['L'], data['E'], data['I'], st.session_state.cargas)
                with open(ruta_cfg, 'r', encoding='utf-8') as fjson:
                    st.download_button(
                        label="⬇️ Descargar JSON configuración",
                        data=fjson.read(),
                        file_name=ruta_cfg.name,
                        mime="application/json",
                    )
                st.success(f"Configuración exportada en {ruta_cfg}")
            except Exception as e:
                st.error(f"No se pudo exportar configuración: {e}")
        st.caption("Mostrando tabla, métricas y diagramas en unidades de exportación. Cambia las unidades en el panel lateral para actualizar.")

        try:
            w_uniforme_dom = None
            for c in st.session_state.cargas:
                if isinstance(c, CargaUniforme):
                    if w_uniforme_dom is None or (c.fin - c.inicio) > w_uniforme_dom[2]:
                        w_uniforme_dom = (c.intensidad, c.inicio, c.fin - c.inicio)
            if w_uniforme_dom:
                w_val, _, long_w = w_uniforme_dom
                Ltot = data['L']
                est_defl = 5 * w_val * (Ltot ** 4) / (384 * data['E'] * data['I'])
                real_mid = df.loc[df['x'].sub(Ltot/2).abs().idxmin(), 'deflexion']
                ratio_raw = (real_mid / est_defl) if est_defl != 0 else float('nan')
                ratio = abs(ratio_raw)
                with st.expander("🔍 Diagnóstico de deflexión"):
                    st.markdown("**Estimación basada únicamente en la carga uniforme dominante (solo UDL).**")
                    st.write(f"Deflexión estimada (solo UDL) = {est_defl*1000:.3f} mm")
                    st.write(f"Deflexión numérica en centro = {real_mid*1000:.3f} mm")
                    if not np.isnan(ratio):
                        st.write(f"Relación |numérica| / |estimada| = {ratio:.3f}")
                        # Banda de tolerancia configurable (heurística): 0.5x a 2.0x
                        lower_tol, upper_tol = 0.5, 2.0
                        if ratio < lower_tol:
                            st.warning("Deflexión menor al 50% de la estimada. Posible sobreestimación de E·I o unidades de carga reducidas.")
                        elif ratio > upper_tol:
                            st.warning("Deflexión superior al doble de la estimada. Verifica E, I, magnitud de la carga o combinaciones de cargas no uniformes dominantes.")
                        else:
                            st.success("La deflexión está dentro de una banda razonable frente a la estimación simplificada (solo UDL).")
        except Exception:
            pass

with tabs[2]:
    st.subheader("Verificación de superposición")
    if len(st.session_state.cargas) < 2:
        st.info("Necesitas al menos dos cargas para verificar.")
    else:
        if st.button("🔍 Ejecutar verificación"):
            try:
                viga_total = Viga(L, E, I)
                for c in st.session_state.cargas:
                    viga_total.agregar_carga(c)
                df_total = generar_dataframe(viga_total, num_puntos=400)
                xs = df_total["x"].to_numpy()
                acumulado = pd.DataFrame({"x": xs, "cortante": 0.0, "momento": 0.0, "pendiente": 0.0, "deflexion": 0.0})
                for c in st.session_state.cargas:
                    v_tmp = Viga(L, E, I)
                    v_tmp.agregar_carga(c)
                    df_i = generar_dataframe(v_tmp, num_puntos=len(xs))
                    if not np.allclose(df_i["x"].to_numpy(), xs):
                        for col in ["cortante", "momento", "pendiente", "deflexion"]:
                            df_i[col] = np.interp(xs, df_i["x"], df_i[col])
                        df_i["x"] = xs
                    acumulado["cortante"] += df_i["cortante"]
                    acumulado["momento"] += df_i["momento"]
                    acumulado["pendiente"] += df_i["pendiente"]
                    acumulado["deflexion"] += df_i["deflexion"]

                resultados = pd.DataFrame({
                    "x": xs,
                    "V_total": df_total["cortante"],
                    "V_suma": acumulado["cortante"],
                    "M_total": df_total["momento"],
                    "M_suma": acumulado["momento"],
                    "y_total": df_total["deflexion"],
                    "y_suma": acumulado["deflexion"],
                })
                for par in [("V_total", "V_suma"), ("M_total", "M_suma"), ("y_total", "y_suma")]:
                    a, b = par
                    resultados[f"error_abs_{a[0].lower()}"] = (resultados[a] - resultados[b]).abs()
                    denom = resultados[a].abs().where(resultados[a].abs() > 1e-12, 1.0)
                    resultados[f"error_rel_{a[0].lower()}"] = resultados[f"error_abs_{a[0].lower()}"] / denom
                resumen = {
                    "max_error_abs_V": float(resultados["error_abs_v"].max()),
                    "max_error_abs_M": float(resultados["error_abs_m"].max()),
                    "max_error_abs_y": float(resultados["error_abs_y"].max()),
                    "max_error_rel_V": float(resultados["error_rel_v"].max()),
                    "max_error_rel_M": float(resultados["error_rel_m"].max()),
                    "max_error_rel_y": float(resultados["error_rel_y"].max()),
                }
                st.json(resumen)
                figd, axs = plt.subplots(3,1, figsize=(6,7), sharex=True)
                axs[0].plot(xs/LENGTH_UNITS[u_len], (resultados["V_total"]-resultados["V_suma"]) / FORCE_UNITS[u_force])
                axs[1].plot(xs/LENGTH_UNITS[u_len], (resultados["M_total"]-resultados["M_suma"]) / (FORCE_UNITS[u_force]*LENGTH_UNITS[u_len]))
                axs[2].plot(xs/LENGTH_UNITS[u_len], (resultados["y_total"]-resultados["y_suma"]) / DEFLEXION_DISPLAY[u_defl_disp])
                for ax, lab in zip(axs, [f"ΔV [{u_force}]", f"ΔM [{u_force}·{u_len}]", f"Δy [{u_defl_disp}]"]):
                    ax.set_ylabel(lab)
                    ax.grid(alpha=0.3)
                axs[-1].set_xlabel(f"x [{u_len}]")
                figd.suptitle("Diferencias (total - suma)")
                st.pyplot(figd)
            except Exception as e:
                st.error(f"Error en verificación: {e}")

st.markdown("---")
st.caption("Aplicación interactiva con tabs y vista previa. Unidades internas SI; conversiones sólo visuales/exportación.")
