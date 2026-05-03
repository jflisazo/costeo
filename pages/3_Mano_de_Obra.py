import streamlit as st
import pandas as pd
from state import init_state, guardar
from models import MOJornalizada, MOMensualizada
from calculos import calc_costo_jornal, calc_costo_mensual

st.set_page_config(page_title="Mano de Obra", layout="wide")
init_state()

st.title("👷 Mano de Obra")

tab1, tab2 = st.tabs(["Jornalizados", "Mensualizados"])

# ── Jornalizados ──────────────────────────────────────────────────────────────
with tab1:
    COLS_J = ["funcion", "id", "moneda", "bruto", "aguinaldo", "vacaciones",
              "cargas_sociales", "viatico", "horas_mes", "costo_hora"]

    def jorn_a_df(lista):
        if not lista:
            return pd.DataFrame(columns=COLS_J)
        return pd.DataFrame([{c: getattr(m, c, 0) for c in COLS_J} for m in lista])

    df_j = jorn_a_df(st.session_state.mo_jornalizada)

    edited_j = st.data_editor(
        df_j,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "funcion": st.column_config.TextColumn("Función", width="medium"),
            "id": st.column_config.NumberColumn("Cat.", format="%d", width="small"),
            "moneda": st.column_config.SelectboxColumn("Moneda", options=["$AR", "USD"]),
            "bruto": st.column_config.NumberColumn("Bruto $/mes", format="%.2f"),
            "aguinaldo": st.column_config.NumberColumn("Aguinaldo $/mes", format="%.2f"),
            "vacaciones": st.column_config.NumberColumn("Vacaciones $/mes", format="%.2f"),
            "cargas_sociales": st.column_config.NumberColumn("Cargas Soc $/mes", format="%.2f"),
            "viatico": st.column_config.NumberColumn("Viático $/mes", format="%.2f"),
            "horas_mes": st.column_config.NumberColumn("Hs/mes", format="%.0f"),
            "costo_hora": st.column_config.NumberColumn("COSTO $/hs", format="%.2f", disabled=True),
        },
        key="jorn_editor",
    )

    if st.button("⚙️ Recalcular y Guardar", key="btn_jorn"):
        nuevos = []
        for _, row in edited_j.iterrows():
            if not row.get("funcion"):
                continue
            mo = MOJornalizada(
                funcion=str(row["funcion"]),
                id=int(row.get("id") or 0),
                moneda=str(row.get("moneda", "$AR")),
                bruto=float(row.get("bruto") or 0),
                aguinaldo=float(row.get("aguinaldo") or 0),
                vacaciones=float(row.get("vacaciones") or 0),
                cargas_sociales=float(row.get("cargas_sociales") or 0),
                viatico=float(row.get("viatico") or 0),
                horas_mes=float(row.get("horas_mes") or 200),
            )
            mo = calc_costo_jornal(mo)
            nuevos.append(mo)
        st.session_state.mo_jornalizada = nuevos
        guardar()
        st.success(f"{len(nuevos)} jornalizados guardados")
        st.rerun()

# ── Mensualizados ─────────────────────────────────────────────────────────────
with tab2:
    COLS_M = ["funcion", "moneda", "neto", "bruto", "aguinaldo", "dias_vacaciones",
              "vacaciones", "cargas_sociales", "prop_despido", "costo_mes"]

    def mens_a_df(lista):
        if not lista:
            return pd.DataFrame(columns=COLS_M)
        return pd.DataFrame([{c: getattr(m, c, 0) for c in COLS_M} for m in lista])

    df_m = mens_a_df(st.session_state.mo_mensualizada)

    edited_m = st.data_editor(
        df_m,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "funcion": st.column_config.TextColumn("Función", width="medium"),
            "moneda": st.column_config.SelectboxColumn("Moneda", options=["$AR", "USD"]),
            "neto": st.column_config.NumberColumn("Neto $/mes", format="%.2f"),
            "bruto": st.column_config.NumberColumn("Bruto $/mes", format="%.2f"),
            "aguinaldo": st.column_config.NumberColumn("Aguinaldo", format="%.2f"),
            "dias_vacaciones": st.column_config.NumberColumn("Días Vac", format="%d"),
            "vacaciones": st.column_config.NumberColumn("Vacaciones", format="%.2f"),
            "cargas_sociales": st.column_config.NumberColumn("Cargas Soc", format="%.2f"),
            "prop_despido": st.column_config.NumberColumn("Prop. Despido", format="%.2f"),
            "costo_mes": st.column_config.NumberColumn("COSTO $/mes", format="%.2f", disabled=True),
        },
        key="mens_editor",
    )

    if st.button("⚙️ Recalcular y Guardar", key="btn_mens"):
        nuevos = []
        for _, row in edited_m.iterrows():
            if not row.get("funcion"):
                continue
            mo = MOMensualizada(
                funcion=str(row["funcion"]),
                moneda=str(row.get("moneda", "$AR")),
                neto=float(row.get("neto") or 0),
                bruto=float(row.get("bruto") or 0),
                aguinaldo=float(row.get("aguinaldo") or 0),
                dias_vacaciones=int(row.get("dias_vacaciones") or 14),
                vacaciones=float(row.get("vacaciones") or 0),
                cargas_sociales=float(row.get("cargas_sociales") or 0),
                prop_despido=float(row.get("prop_despido") or 0),
            )
            mo = calc_costo_mensual(mo)
            nuevos.append(mo)
        st.session_state.mo_mensualizada = nuevos
        guardar()
        st.success(f"{len(nuevos)} mensualizados guardados")
        st.rerun()
