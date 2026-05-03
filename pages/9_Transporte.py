import streamlit as st
import pandas as pd
from state import init_state, guardar
from models import CicloTransporte
from calculos.transporte import calc_ciclo_transporte

st.set_page_config(page_title="Transporte Interno", layout="wide")
init_state()

st.title("🚛 Ciclo de Transporte Interno")

s = st.session_state

COLS = [
    "descripcion", "unidad", "equipo", "capacidad", "distancia_km", "rendimiento_base",
    "vel_ida", "vel_vuelta", "tiempo_espera", "tiempo_carga", "tiempo_descarga", "hs_dia",
    "tiempo_ciclo_min", "rend_dia", "n_camiones", "costo",
]

def tpte_a_df():
    if not s.transportes:
        return pd.DataFrame(columns=COLS)
    return pd.DataFrame([{c: getattr(t, c, 0) for c in COLS} for t in s.transportes])


edited = st.data_editor(
    tpte_a_df(),
    use_container_width=True,
    num_rows="dynamic",
    column_config={
        "descripcion": st.column_config.TextColumn("Descripción", width="large"),
        "unidad": st.column_config.TextColumn("Un"),
        "equipo": st.column_config.TextColumn("Equipo", width="medium"),
        "capacidad": st.column_config.NumberColumn("Cap (m3/tn)", format="%.2f"),
        "distancia_km": st.column_config.NumberColumn("Dist km", format="%.1f"),
        "rendimiento_base": st.column_config.NumberColumn("Rend base/día", format="%.1f"),
        "vel_ida": st.column_config.NumberColumn("V ida (km/h)", format="%.0f"),
        "vel_vuelta": st.column_config.NumberColumn("V vuelta (km/h)", format="%.0f"),
        "tiempo_espera": st.column_config.NumberColumn("Espera (min)", format="%.1f"),
        "tiempo_carga": st.column_config.NumberColumn("Carga (min)", format="%.1f"),
        "tiempo_descarga": st.column_config.NumberColumn("Descarga (min)", format="%.1f"),
        "hs_dia": st.column_config.NumberColumn("Hs/día", format="%.1f"),
        "tiempo_ciclo_min": st.column_config.NumberColumn("T ciclo (min)", disabled=True, format="%.1f"),
        "rend_dia": st.column_config.NumberColumn("Rend/día", disabled=True, format="%.2f"),
        "n_camiones": st.column_config.NumberColumn("N° Cam.", disabled=True, format="%.2f"),
        "costo": st.column_config.NumberColumn("Costo $/un", disabled=True, format="%.2f"),
    },
    key="tpte_editor",
)

if st.button("⚙️ Recalcular y Guardar", use_container_width=False):
    nuevos = []
    for _, row in edited.iterrows():
        desc = str(row.get("descripcion", "") or "")
        if not desc:
            continue
        equipo_nombre = str(row.get("equipo", "") or "")
        costo_hora_eq = next(
            (e.costo_hora for e in s.equipos if e.nombre == equipo_nombre), 0.0
        )
        t = CicloTransporte(
            descripcion=desc,
            unidad=str(row.get("unidad", "m3") or "m3"),
            equipo=equipo_nombre,
            capacidad=float(row.get("capacidad") or 0),
            distancia_km=float(row.get("distancia_km") or 0),
            rendimiento_base=float(row.get("rendimiento_base") or 0),
            vel_ida=float(row.get("vel_ida") or 40),
            vel_vuelta=float(row.get("vel_vuelta") or 40),
            tiempo_espera=float(row.get("tiempo_espera") or 5),
            tiempo_carga=float(row.get("tiempo_carga") or 5),
            tiempo_descarga=float(row.get("tiempo_descarga") or 5),
            hs_dia=float(row.get("hs_dia") or 10),
        )
        t = calc_ciclo_transporte(t, costo_hora_eq)
        nuevos.append(t)
    s.transportes = nuevos
    guardar()
    st.success(f"{len(nuevos)} ciclos calculados")
    st.rerun()

# Detalle de fórmula
if s.transportes:
    st.divider()
    st.subheader("Detalle de cálculo")
    sel = st.selectbox("Ver ciclo", [t.descripcion for t in s.transportes])
    t = next(x for x in s.transportes if x.descripcion == sel)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("T. ciclo", f"{t.tiempo_ciclo_min:.1f} min")
    c2.metric("Rend/día", f"{t.rend_dia:.2f} {t.unidad}")
    c3.metric("N° camiones", f"{t.n_camiones:.2f}")
    c4.metric("Costo", f"${t.costo:,.2f}/{t.unidad}")
