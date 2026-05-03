import streamlit as st
import pandas as pd
from state import init_state, guardar
from models import Equipo
from calculos import calc_costo_equipo

st.set_page_config(page_title="Equipos", layout="wide")
init_state()

st.title("🚜 Equipos")

proyecto = st.session_state.proyecto

precio_gasoil = next(
    (c.costo for c in st.session_state.combustibles if "gas oil" in c.descripcion.lower()),
    0.0,
)

# ── Tabla principal ────────────────────────────────────────────────────────────
COLS_TABLE = ["nombre", "marca", "modelo", "potencia", "moneda", "precio",
              "k_combustible", "propiedad", "metodo_costeo",
              "cu_ai", "cu_rr", "cu_comb", "costo_hora"]

METODOS = ["KEOPS", "DNV", "Porcentaje", "Manual_AR"]


def equipos_a_df(equipos):
    if not equipos:
        return pd.DataFrame(columns=COLS_TABLE)
    return pd.DataFrame([{c: getattr(e, c, "") for c in COLS_TABLE} for e in equipos])


df = equipos_a_df(st.session_state.equipos)
st.subheader(f"Equipos cargados: {len(st.session_state.equipos)}")

edited_df = st.data_editor(
    df,
    use_container_width=True,
    num_rows="dynamic",
    column_config={
        "nombre":        st.column_config.TextColumn("Equipo", width="medium"),
        "marca":         st.column_config.TextColumn("Marca"),
        "modelo":        st.column_config.TextColumn("Modelo"),
        "potencia":      st.column_config.NumberColumn("Potencia (HP)", format="%.0f"),
        "moneda":        st.column_config.SelectboxColumn("Moneda", options=["USD", "EUR", "$AR"]),
        "precio":        st.column_config.NumberColumn("Precio", format="%.0f"),
        "k_combustible": st.column_config.NumberColumn("K Comb", format="%.3f"),
        "propiedad":     st.column_config.SelectboxColumn("Propiedad", options=["Propio", "Alquilado"]),
        "metodo_costeo": st.column_config.SelectboxColumn("Método", options=METODOS),
        "cu_ai":         st.column_config.NumberColumn("A+I $/hs",   format="%.2f", disabled=True),
        "cu_rr":         st.column_config.NumberColumn("R&R $/hs",   format="%.2f", disabled=True),
        "cu_comb":       st.column_config.NumberColumn("Comb $/hs",  format="%.2f", disabled=True),
        "costo_hora":    st.column_config.NumberColumn("COSTO $/hs", format="%.2f", disabled=True),
    },
    key="eq_editor",
)

col_btn, _ = st.columns([2, 5])
with col_btn:
    if st.button("⚙️ Recalcular y Guardar tabla", use_container_width=True, type="primary"):
        # Build lookup by nombre to preserve method-specific fields
        existentes = {e.nombre: e for e in st.session_state.equipos}
        nuevos = []
        for _, row in edited_df.iterrows():
            if not row.get("nombre"):
                continue
            base = existentes.get(row["nombre"])
            # Start from existing object (preserves ratio_ai, ratio_rr, vida_util_hs, etc.)
            if base:
                eq = base.model_copy(update={
                    "nombre":        row.get("nombre", base.nombre),
                    "marca":         row.get("marca", base.marca),
                    "modelo":        row.get("modelo", base.modelo),
                    "potencia":      float(row.get("potencia") or base.potencia),
                    "moneda":        row.get("moneda", base.moneda),
                    "precio":        float(row.get("precio") or base.precio),
                    "k_combustible": float(row.get("k_combustible") or base.k_combustible),
                    "propiedad":     row.get("propiedad", base.propiedad),
                    "metodo_costeo": row.get("metodo_costeo", base.metodo_costeo),
                })
            else:
                eq = Equipo(
                    nombre=        row.get("nombre", ""),
                    marca=         row.get("marca", ""),
                    modelo=        row.get("modelo", ""),
                    potencia=      float(row.get("potencia") or 0),
                    moneda=        row.get("moneda", "USD"),
                    precio=        float(row.get("precio") or 0),
                    k_combustible= float(row.get("k_combustible") or 0),
                    propiedad=     row.get("propiedad", "Propio"),
                    metodo_costeo= row.get("metodo_costeo", "KEOPS"),
                )
            eq = calc_costo_equipo(eq, proyecto, precio_gasoil)
            nuevos.append(eq)
        st.session_state.equipos = nuevos
        guardar()
        st.success(f"{len(nuevos)} equipos guardados y recalculados.")
        st.rerun()

# ── Editor de parámetros de método ────────────────────────────────────────────
if st.session_state.equipos:
    st.divider()
    st.subheader("Parámetros del método de costeo")
    st.caption("Edita los parámetros específicos del método para un equipo y guarda.")

    nombres = [e.nombre for e in st.session_state.equipos]
    sel = st.selectbox("Equipo a editar", nombres, key="sel_eq_detalle")
    eq = next(e for e in st.session_state.equipos if e.nombre == sel)

    with st.form("form_eq_metodo"):
        ca, cb = st.columns(2)
        nuevo_metodo = ca.selectbox(
            "Método de costeo",
            METODOS,
            index=METODOS.index(eq.metodo_costeo) if eq.metodo_costeo in METODOS else 0,
        )
        moneda = cb.selectbox("Moneda", ["USD", "EUR", "$AR"],
                              index=["USD", "EUR", "$AR"].index(eq.moneda) if eq.moneda in ["USD","EUR","$AR"] else 0)

        c1, c2, c3 = st.columns(3)
        precio    = c1.number_input("Precio (en moneda seleccionada)", value=float(eq.precio), step=1000.0)
        potencia  = c2.number_input("Potencia (HP)", value=float(eq.potencia), step=10.0)
        k_comb    = c3.number_input("K combustible (lt/HP·hs)", value=float(eq.k_combustible), step=0.001, format="%.4f")

        # Campos según método
        if nuevo_metodo == "KEOPS":
            st.info(
                f"**Ratios KEOPS (calculados al importar)**  \n"
                f"ratio\\_ai = {eq.ratio_ai:.6f} &nbsp;&nbsp; "
                f"ratio\\_rr = {eq.ratio_rr:.6f} &nbsp;&nbsp; "
                f"cotiz\\_base = {eq.cotiz_base:,.0f}"
            )
            st.caption(
                "El costo se escala automáticamente: `cu_ai = ratio_ai × precio × cotiz_actual`. "
                "Para cambiar los ratios, reimportá el Excel con la cotización actualizada."
            )
            vida_util = eq.vida_util_hs
            vr = eq.vr
            uso_anual = eq.uso_anual
            k_rr = eq.k_rr
            porcentaje = eq.porcentaje
            cu_ai_manual = eq.cu_ai
            cu_rr_manual = eq.cu_rr

        elif nuevo_metodo == "DNV":
            st.subheader("Parámetros DNV")
            d1, d2, d3, d4 = st.columns(4)
            vida_util = d1.number_input("Vida útil (hs)",       value=float(eq.vida_util_hs), step=500.0,
                                        help="0 = usa el default del proyecto")
            vr        = d2.number_input("Valor residual (vr)",  value=float(eq.vr),            step=0.01, format="%.3f")
            uso_anual = d3.number_input("Uso anual (hs)",        value=float(eq.uso_anual),     step=100.0)
            k_rr      = d4.number_input("K_RR",                  value=float(eq.k_rr),          step=0.01, format="%.3f")
            st.caption(f"Tasa anual: **{proyecto.tasa_anual*100:.1f}%** (se configura en Proyecto)")
            porcentaje = eq.porcentaje
            cu_ai_manual = eq.cu_ai
            cu_rr_manual = eq.cu_rr

        elif nuevo_metodo == "Porcentaje":
            st.subheader("Parámetros porcentaje")
            p1, p2 = st.columns(2)
            porcentaje = p1.number_input("% s/precio anual", value=float(eq.porcentaje * 100),
                                         step=0.5, format="%.2f", help="Ej: 4 = 4%") / 100
            uso_anual  = p2.number_input("Uso anual (hs)", value=float(eq.uso_anual), step=100.0)
            vida_util = eq.vida_util_hs
            vr = eq.vr
            k_rr = eq.k_rr
            cu_ai_manual = eq.cu_ai
            cu_rr_manual = eq.cu_rr

        else:  # Manual_AR
            st.subheader("Costo horario manual ($/hs fijos en $AR)")
            m1, m2 = st.columns(2)
            cu_ai_manual = m1.number_input("A+I ($/hs)", value=float(eq.cu_ai), step=10.0)
            cu_rr_manual = m2.number_input("R&R ($/hs)", value=float(eq.cu_rr), step=10.0)
            st.caption("El combustible se sigue calculando con potencia × K_comb × precio gasoil.")
            vida_util = eq.vida_util_hs
            vr = eq.vr
            uso_anual = eq.uso_anual
            k_rr = eq.k_rr
            porcentaje = eq.porcentaje

        if st.form_submit_button("💾 Guardar parámetros y recalcular", use_container_width=True):
            eq_actualizado = eq.model_copy(update={
                "moneda":        moneda,
                "precio":        precio,
                "potencia":      potencia,
                "k_combustible": k_comb,
                "metodo_costeo": nuevo_metodo,
                "vida_util_hs":  vida_util,
                "vr":            vr,
                "uso_anual":     uso_anual,
                "k_rr":          k_rr,
                "porcentaje":    porcentaje,
                "cu_ai":         cu_ai_manual if nuevo_metodo == "Manual_AR" else eq.cu_ai,
                "cu_rr":         cu_rr_manual if nuevo_metodo == "Manual_AR" else eq.cu_rr,
            })
            eq_actualizado = calc_costo_equipo(eq_actualizado, proyecto, precio_gasoil)
            st.session_state.equipos = [
                eq_actualizado if e.nombre == sel else e
                for e in st.session_state.equipos
            ]
            guardar()
            st.success(
                f"{sel}: costo horario actualizado → "
                f"**${eq_actualizado.costo_hora:,.2f}/hs**"
            )
            st.rerun()

    # ── Panel de métricas del equipo seleccionado ──────────────────────────────
    eq_actual = next(e for e in st.session_state.equipos if e.nombre == sel)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Método", eq_actual.metodo_costeo)
    c2.metric("A+I ($/hs)",   f"{eq_actual.cu_ai:,.2f}")
    c3.metric("R&R ($/hs)",   f"{eq_actual.cu_rr:,.2f}")
    c4.metric("Comb ($/hs)",  f"{eq_actual.cu_comb:,.2f}")
    c5.metric("TOTAL ($/hs)", f"{eq_actual.costo_hora:,.2f}")
