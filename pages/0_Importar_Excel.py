"""
Importar datos desde el archivo Excel .xlsm original.
Aparece primero en el menú (prefijo 0_).
"""

import streamlit as st
from pathlib import Path
from state import init_state, dict_a_estado, guardar
from importar.excel_reader import leer_excel

st.set_page_config(page_title="Importar Excel", layout="wide")
init_state()

st.title("📥 Importar desde Excel")

st.info(
    "Esta página lee el archivo `.xlsm` y carga todos los datos en la aplicación: "
    "equipos, mano de obra, materiales, ítems, Datos CD y gastos generales."
)

# ── Opción 1: archivo en disco ─────────────────────────────────────────────────
RUTA_DEFAULT = Path(__file__).parent.parent / "Camino acceso Jose Maria Seccion A1yA2.rev4.xlsm"

st.subheader("Archivo local")
ruta_input = st.text_input(
    "Ruta del archivo .xlsm",
    value=str(RUTA_DEFAULT) if RUTA_DEFAULT.exists() else "",
    help="Ruta absoluta al archivo Excel en el servidor.",
)

# ── Opción 2: upload ───────────────────────────────────────────────────────────
st.subheader("O subir archivo")
uploaded = st.file_uploader("Subir .xlsm", type=["xlsm", "xlsx"])

# ── Nombre del proyecto ────────────────────────────────────────────────────────
nombre_proyecto = st.text_input(
    "Nombre del proyecto (para guardar)",
    value=st.session_state.get("proyecto_nombre", "Importado"),
)

st.divider()
col1, _ = st.columns([1, 4])
with col1:
    importar = st.button("🚀 Importar", use_container_width=True, type="primary")

if importar:
    ruta = None

    if uploaded:
        # Guardar upload en un temp file
        import tempfile, shutil
        tmp = tempfile.NamedTemporaryFile(suffix=".xlsm", delete=False)
        shutil.copyfileobj(uploaded, tmp)
        tmp.flush()
        ruta = Path(tmp.name)
    elif ruta_input and Path(ruta_input).exists():
        ruta = Path(ruta_input)

    if not ruta:
        st.error("No se encontró ningún archivo. Ingresá una ruta válida o subí el archivo.")
    else:
        with st.spinner("Leyendo archivo Excel... (puede demorar unos segundos)"):
            try:
                data = leer_excel(ruta)
            except Exception as e:
                st.error(f"Error al leer el archivo: {e}")
                st.stop()

        # Cargar en session state
        st.session_state.proyecto_nombre = nombre_proyecto
        dict_a_estado(data)

        if nombre_proyecto:
            guardar()

        # Resumen de lo importado
        p = st.session_state.proyecto
        items_obra = [i for i in st.session_state.items if i.tipo == "Item"]

        st.success("✅ Importación completada")
        st.subheader("Resumen importado")

        c1, c2, c3 = st.columns(3)
        c1.metric("Empresa", p.empresa)
        c2.metric("Plazo", f"{p.plazo_meses} meses")
        c3.metric("USD", f"${p.cotizaciones.get('USD', 0):,.0f}")

        c4, c5, c6, c7, c8 = st.columns(5)
        c4.metric("Equipos", len(st.session_state.equipos))
        c5.metric("MO Jorn.", len(st.session_state.mo_jornalizada))
        c6.metric("Materiales", len(st.session_state.materiales))
        c7.metric("Subcontratos", len(st.session_state.subcontratos))
        c8.metric("Combustibles", len(st.session_state.combustibles))

        c9, c10, c11 = st.columns(3)
        c9.metric("Ítems de obra", len(items_obra))
        c10.metric("Filas Datos CD", len(st.session_state.datos_cd))
        c11.metric("Gastos Grales", len([g for g in st.session_state.gastos_generales if g.tipo == "Item"]))

        costo_cd = sum(i.costo_total for i in items_obra)
        total_gg = sum(g.total for g in st.session_state.gastos_generales if g.tipo == "Item")
        st.divider()
        m1, m2, m3 = st.columns(3)
        m1.metric("Costo Directo Total", f"${costo_cd:,.0f}")
        m2.metric("Gastos Generales", f"${total_gg:,.0f}")
        m3.metric("Costo Total", f"${costo_cd + total_gg:,.0f}")

        st.caption("Navegá a las otras páginas para revisar o editar los datos importados.")
