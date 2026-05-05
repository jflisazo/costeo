"""
Página de ítems de obra y análisis de costos directos (Datos CD).
- Tabla jerárquica de ítems (Títulos e Ítems)
- Editor de tareas/recursos por ítem seleccionado
- Recálculo automático del costo unitario
"""

import streamlit as st
import pandas as pd
from state import init_state, guardar
from models import Item, DatoCD
from models.items import TIPOS_RECURSO
from calculos.costos_directos import recalcular_datos_cd, calc_cu_item

st.set_page_config(page_title="Ítems de Obra", layout="wide")
init_state()

st.title("📐 Ítems de Obra — Análisis de Costos Directos")

s = st.session_state

# ══════════════════════════════════════════════════════════════════════════════
# Panel izquierdo: lista de ítems / Panel derecho: datos CD
# ══════════════════════════════════════════════════════════════════════════════
left, right = st.columns([2, 3])

# ── PANEL IZQUIERDO: Items ────────────────────────────────────────────────────
with left:
    st.subheader(f"Ítems ({len(s['items'])})")

    COLS_ITEM = ["tipo", "numero", "descripcion", "unidad", "cantidad",
                 "costo_unitario", "costo_total"]

    def items_a_df():
        if not s["items"]:
            return pd.DataFrame(columns=COLS_ITEM)
        return pd.DataFrame([{c: getattr(i, c, "") for c in COLS_ITEM} for i in s["items"]])

    edited_items = st.data_editor(
        items_a_df(),
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "tipo": st.column_config.SelectboxColumn("Tipo", options=["Título", "Item"], width="small"),
            "numero": st.column_config.TextColumn("N°", width="medium"),
            "descripcion": st.column_config.TextColumn("Descripción", width="large"),
            "unidad": st.column_config.TextColumn("Un", width="small"),
            "cantidad": st.column_config.NumberColumn("Cantidad", format="%.2f"),
            "costo_unitario": st.column_config.NumberColumn("CU $", format="%.2f", disabled=True),
            "costo_total": st.column_config.NumberColumn("Total $", format="%.0f", disabled=True),
        },
        key="items_editor",
        height=500,
    )

    c1, c2 = st.columns(2)
    with c1:
        if st.button("💾 Guardar ítems", use_container_width=True):
            nuevos = []
            for _, row in edited_items.iterrows():
                if not row.get("numero"):
                    continue
                item = Item(
                    tipo="Título" if str(row.get("tipo", "Item")) == "Título" else "Item",
                    numero=str(row["numero"]),
                    descripcion=str(row.get("descripcion", "")),
                    unidad=str(row.get("unidad", "")),
                    cantidad=float(row.get("cantidad") or 0),
                    costo_unitario=float(row.get("costo_unitario") or 0),
                    costo_total=float(row.get("costo_total") or 0),
                )
                nuevos.append(item)
            s["items"] = nuevos
            guardar()
            st.success("Ítems guardados")
            st.rerun()
    with c2:
        if st.button("⚙️ Recalcular todos", use_container_width=True):
            # Recalcular datos CD
            s.datos_cd = recalcular_datos_cd(
                s.datos_cd, s.equipos, s.mo_jornalizada, s.mo_mensualizada,
                s.materiales, s.combustibles, s.subcontratos, s.auxiliares, s.transportes,
            )
            # Actualizar costos unitarios de ítems
            for i, item in enumerate(s["items"]):
                if item.tipo == "Item":
                    cu = calc_cu_item(item.numero, s.datos_cd)
                    ct = round(cu * item.cantidad, 2)
                    s["items"][i] = item.model_copy(update={
                        "costo_unitario": round(cu, 4),
                        "costo_total": ct,
                    })
            guardar()
            st.success("Costos recalculados")
            st.rerun()

# ── PANEL DERECHO: Datos CD del ítem seleccionado ─────────────────────────────
with right:
    items_obra = [i for i in s["items"] if i.tipo == "Item"]
    if not items_obra:
        st.info("Cargá ítems de obra en el panel izquierdo para ver el análisis de costos.")
    else:
        opciones = [f"{i.numero} — {i.descripcion}" for i in items_obra]
        sel_str = st.selectbox("Ítem a analizar", opciones)
        sel_item = items_obra[opciones.index(sel_str)]

        st.subheader(f"Análisis: {sel_item.numero}")
        st.caption(
            f"{sel_item.descripcion} | {sel_item.unidad} | "
            f"Cantidad: {sel_item.cantidad:,.2f} | "
            f"CU: **${sel_item.costo_unitario:,.2f}** | "
            f"Total: **${sel_item.costo_total:,.0f}**"
        )

        # Filtrar datos CD de este ítem
        datos_item = [d for d in s.datos_cd if d.item_id == sel_item.numero]

        COLS_CD = ["tarea", "tarea_unidad", "incidencia", "rendimiento",
                   "tipo_recurso", "recurso", "cuantia", "comentario",
                   "cuantia_por_unidad", "costo_unitario"]

        def cd_a_df(datos):
            if not datos:
                return pd.DataFrame(columns=COLS_CD)
            return pd.DataFrame([{c: getattr(d, c, "") for c in COLS_CD} for d in datos])

        edited_cd = st.data_editor(
            cd_a_df(datos_item),
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "tarea": st.column_config.TextColumn("Tarea", width="medium"),
                "tarea_unidad": st.column_config.TextColumn("Un T."),
                "incidencia": st.column_config.NumberColumn("Incid.", format="%.4f"),
                "rendimiento": st.column_config.NumberColumn("Rend/día", format="%.2f"),
                "tipo_recurso": st.column_config.SelectboxColumn("Tipo", options=TIPOS_RECURSO),
                "recurso": st.column_config.TextColumn("Recurso", width="large"),
                "cuantia": st.column_config.NumberColumn("Cuantía/día", format="%.4f"),
                "comentario": st.column_config.TextColumn("Comentario"),
                "cuantia_por_unidad": st.column_config.NumberColumn("Cuantía/Un", disabled=True, format="%.6f"),
                "costo_unitario": st.column_config.NumberColumn("CU $", disabled=True, format="%.4f"),
            },
            key=f"cd_{sel_item.numero}",
            height=450,
        )

        btn_cd1, btn_cd2 = st.columns(2)
        with btn_cd1:
            if st.button("⚙️ Recalcular ítem", use_container_width=True):
                # Parsear filas editadas
                nuevas_cd = []
                for _, row in edited_cd.iterrows():
                    if not row.get("recurso"):
                        continue
                    d = DatoCD(
                        item_id=sel_item.numero,
                        tarea=str(row.get("tarea", "")),
                        tarea_unidad=str(row.get("tarea_unidad", "")),
                        incidencia=float(row.get("incidencia") or 1),
                        rendimiento=float(row.get("rendimiento") or 1),
                        tipo_recurso=str(row.get("tipo_recurso", "")),
                        recurso=str(row.get("recurso", "")),
                        cuantia=float(row.get("cuantia") or 0),
                        comentario=str(row.get("comentario", "")),
                    )
                    nuevas_cd.append(d)

                # Recalcular las nuevas filas
                nuevas_cd = recalcular_datos_cd(
                    nuevas_cd, s.equipos, s.mo_jornalizada, s.mo_mensualizada,
                    s.materiales, s.combustibles, s.subcontratos, s.auxiliares, s.transportes,
                )

                # Reemplazar en la lista global
                otros = [d for d in s.datos_cd if d.item_id != sel_item.numero]
                s.datos_cd = otros + nuevas_cd

                # Actualizar costo del ítem
                cu = calc_cu_item(sel_item.numero, s.datos_cd)
                idx = next(i for i, x in enumerate(s["items"]) if x.numero == sel_item.numero)
                ct = round(cu * s["items"][idx].cantidad, 2)
                s["items"][idx] = s["items"][idx].model_copy(update={
                    "costo_unitario": round(cu, 4),
                    "costo_total": ct,
                })
                guardar()
                st.success(f"CU = ${cu:,.4f}")
                st.rerun()

        # Resumen por tipo de recurso
        if datos_item:
            st.divider()
            resumen = {}
            for d in datos_item:
                resumen[d.tipo_recurso] = resumen.get(d.tipo_recurso, 0) + d.costo_unitario
            df_res = pd.DataFrame(
                [{"Tipo": k, "CU $": v} for k, v in sorted(resumen.items())],
            )
            df_res["%"] = df_res["CU $"] / df_res["CU $"].sum() * 100
            st.dataframe(df_res, hide_index=True, use_container_width=True,
                         column_config={
                             "CU $": st.column_config.NumberColumn(format="$%.2f"),
                             "%": st.column_config.NumberColumn(format="%.1f%%"),
                         })
