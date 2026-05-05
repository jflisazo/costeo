import streamlit as st
import pandas as pd
from state import init_state, guardar
from models import Material, Combustible, Subcontrato
from calculos.materiales import calc_costo_material, calc_costo_combustible, calc_costo_subcontrato

st.set_page_config(page_title="Materiales", layout="wide")
init_state()

st.title("🧱 Materiales, Combustibles y Subcontratos")

proyecto = st.session_state.proyecto
tab1, tab2, tab3 = st.tabs(["Materiales", "Combustibles", "Subcontratos"])

# ── Materiales ────────────────────────────────────────────────────────────────
with tab1:
    COLS_MAT = ["numero", "descripcion", "unidad", "moneda", "proveedor", "origen",
                "distancia_km", "costo_origen", "costo_flete", "otros", "perc_perdida", "costo"]

    def mat_a_df(lista):
        if not lista:
            return pd.DataFrame(columns=COLS_MAT)
        return pd.DataFrame([{c: getattr(m, c, 0) for c in COLS_MAT} for m in lista])

    edited_mat = st.data_editor(
        mat_a_df(st.session_state.materiales),
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "numero": st.column_config.NumberColumn("#", width="small"),
            "descripcion": st.column_config.TextColumn("Descripción", width="large"),
            "unidad": st.column_config.TextColumn("Un", width="small"),
            "moneda": st.column_config.SelectboxColumn("Moneda", options=["$AR", "USD", "EUR"]),
            "proveedor": st.column_config.TextColumn("Proveedor"),
            "origen": st.column_config.TextColumn("Origen/Puesto obra"),
            "distancia_km": st.column_config.NumberColumn("Dist km", format="%.0f"),
            "costo_origen": st.column_config.NumberColumn("Precio OR", format="%.2f"),
            "costo_flete": st.column_config.NumberColumn("Flete", format="%.2f"),
            "otros": st.column_config.NumberColumn("Otros", format="%.2f"),
            "perc_perdida": st.column_config.NumberColumn("% Pérd", format="%.3f"),
            "costo": st.column_config.NumberColumn("COSTO", format="%.2f", disabled=True),
        },
        key="mat_editor",
    )

    if st.button("⚙️ Recalcular y Guardar", key="btn_mat"):
        nuevos = []
        for i, (_, row) in enumerate(edited_mat.iterrows()):
            if not row.get("descripcion"):
                continue
            m = Material(
                numero=int(row.get("numero") or i),
                descripcion=str(row["descripcion"]),
                unidad=str(row.get("unidad", "")),
                moneda=str(row.get("moneda", "$AR")),
                proveedor=str(row.get("proveedor", "")),
                origen=str(row.get("origen", "")),
                distancia_km=float(row.get("distancia_km") or 0),
                costo_origen=float(row.get("costo_origen") or 0),
                costo_flete=float(row.get("costo_flete") or 0),
                otros=float(row.get("otros") or 0),
                perc_perdida=float(row.get("perc_perdida") or 0),
            )
            m = calc_costo_material(m, proyecto)
            nuevos.append(m)
        st.session_state.materiales = nuevos
        guardar()
        st.success(f"{len(nuevos)} materiales guardados")
        st.rerun()

# ── Combustibles ──────────────────────────────────────────────────────────────
with tab2:
    COLS_COMB = ["descripcion", "unidad", "moneda", "proveedor", "costo_origen", "otros", "costo"]

    def comb_a_df(lista):
        if not lista:
            return pd.DataFrame(columns=COLS_COMB)
        return pd.DataFrame([{c: getattr(c2, c, 0) for c in COLS_COMB} for c2 in lista])

    edited_comb = st.data_editor(
        comb_a_df(st.session_state.combustibles),
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "descripcion": st.column_config.TextColumn("Descripción", width="medium"),
            "unidad": st.column_config.TextColumn("Un"),
            "moneda": st.column_config.SelectboxColumn("Moneda", options=["$AR", "USD"]),
            "proveedor": st.column_config.TextColumn("Proveedor"),
            "costo_origen": st.column_config.NumberColumn("Precio", format="%.2f"),
            "otros": st.column_config.NumberColumn("Otros", format="%.2f"),
            "costo": st.column_config.NumberColumn("COSTO", format="%.2f", disabled=True),
        },
        key="comb_editor",
    )

    if st.button("⚙️ Guardar combustibles", key="btn_comb"):
        nuevos = []
        for _, row in edited_comb.iterrows():
            if not row.get("descripcion"):
                continue
            c = Combustible(
                descripcion=str(row["descripcion"]),
                unidad=str(row.get("unidad", "lts")),
                moneda=str(row.get("moneda", "$AR")),
                proveedor=str(row.get("proveedor", "")),
                costo_origen=float(row.get("costo_origen") or 0),
                otros=float(row.get("otros") or 0),
            )
            c = calc_costo_combustible(c)
            nuevos.append(c)
        st.session_state.combustibles = nuevos
        guardar()
        st.success(f"{len(nuevos)} combustibles guardados")
        st.rerun()

# ── Subcontratos ───────────────────────────────────────────────────────────────
with tab3:
    COLS_SUB = ["numero", "descripcion", "unidad", "moneda", "proveedor", "costo_or", "otros", "costo"]

    def sub_a_df(lista):
        if not lista:
            return pd.DataFrame(columns=COLS_SUB)
        return pd.DataFrame([{c: getattr(s, c, 0) for c in COLS_SUB} for s in lista])

    edited_sub = st.data_editor(
        sub_a_df(st.session_state.subcontratos),
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "numero": st.column_config.NumberColumn("#", width="small"),
            "descripcion": st.column_config.TextColumn("Descripción", width="large"),
            "unidad": st.column_config.TextColumn("Un"),
            "moneda": st.column_config.SelectboxColumn("Moneda", options=["$AR", "USD", "EUR"]),
            "proveedor": st.column_config.TextColumn("Proveedor"),
            "costo_or": st.column_config.NumberColumn("Precio OR", format="%.2f"),
            "otros": st.column_config.NumberColumn("Otros", format="%.2f"),
            "costo": st.column_config.NumberColumn("COSTO", format="%.2f", disabled=True),
        },
        key="sub_editor",
    )

    if st.button("⚙️ Guardar subcontratos", key="btn_sub"):
        nuevos = []
        for i, (_, row) in enumerate(edited_sub.iterrows()):
            if not row.get("descripcion"):
                continue
            s = Subcontrato(
                numero=int(row.get("numero") or i),
                descripcion=str(row["descripcion"]),
                unidad=str(row.get("unidad", "")),
                moneda=str(row.get("moneda", "$AR")),
                proveedor=str(row.get("proveedor", "")),
                costo_or=float(row.get("costo_or") or 0),
                otros=float(row.get("otros") or 0),
            )
            s = calc_costo_subcontrato(s, proyecto)
            nuevos.append(s)
        st.session_state.subcontratos = nuevos
        guardar()
        st.success(f"{len(nuevos)} subcontratos guardados")
        st.rerun()
