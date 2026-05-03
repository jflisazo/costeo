import streamlit as st
import pandas as pd
from state import init_state, guardar
from models import GastoGeneral
from calculos.costos_directos import lookup_costo_recurso

st.set_page_config(page_title="Gastos Generales", layout="wide")
init_state()

st.title("🏢 Gastos Generales")

s = st.session_state

COLS_GG = ["id", "tipo", "categoria", "recurso", "unidad", "moneda",
           "cantidad", "mes_inicio", "meses", "amort_perc",
           "costo_unitario", "comentario", "total"]

def gg_a_df():
    if not s.gastos_generales:
        return pd.DataFrame(columns=COLS_GG)
    return pd.DataFrame([{c: getattr(g, c, "") for c in COLS_GG} for g in s.gastos_generales])


edited = st.data_editor(
    gg_a_df(),
    use_container_width=True,
    num_rows="dynamic",
    column_config={
        "id": st.column_config.NumberColumn("#", width="small"),
        "tipo": st.column_config.SelectboxColumn("Tipo", options=["Título", "Item"], width="small"),
        "categoria": st.column_config.TextColumn("Categoría", width="medium"),
        "recurso": st.column_config.TextColumn("Recurso / Descripción", width="large"),
        "unidad": st.column_config.TextColumn("Un"),
        "moneda": st.column_config.SelectboxColumn("Moneda", options=["$AR", "USD", "EUR"]),
        "cantidad": st.column_config.NumberColumn("Cantidad", format="%.2f"),
        "mes_inicio": st.column_config.NumberColumn("Mes inicio", format="%d"),
        "meses": st.column_config.NumberColumn("Meses", format="%d"),
        "amort_perc": st.column_config.NumberColumn("Amort %", format="%.2f"),
        "costo_unitario": st.column_config.NumberColumn("CU $", format="%.2f"),
        "comentario": st.column_config.TextColumn("Comentario"),
        "total": st.column_config.NumberColumn("TOTAL $", format="%.0f", disabled=True),
    },
    key="gg_editor",
    height=500,
)

col1, col2 = st.columns([1, 4])
with col1:
    if st.button("⚙️ Recalcular y Guardar", use_container_width=True):
        nuevos = []
        for i, row in edited.iterrows():
            tipo = str(row.get("tipo", "Item"))
            recurso = str(row.get("recurso", ""))
            if not recurso:
                continue

            # Intentar obtener costo unitario de MO mensualizada si está vacío
            cu = float(row.get("costo_unitario") or 0)
            if cu == 0 and tipo == "Item":
                cu = lookup_costo_recurso(
                    "mano de obra", recurso,
                    s.equipos, s.mo_jornalizada, s.mo_mensualizada,
                    s.materiales, s.combustibles, s.subcontratos,
                    s.auxiliares, s.transportes,
                )

            cantidad = float(row.get("cantidad") or 0)
            meses = float(row.get("meses") or 1)
            amort = float(row.get("amort_perc") or 1)
            total = cu * cantidad * meses * amort if tipo == "Item" else 0.0

            g = GastoGeneral(
                id=int(row.get("id") or i),
                tipo=tipo,
                categoria=str(row.get("categoria", "")),
                recurso=recurso,
                unidad=str(row.get("unidad", "")),
                moneda=str(row.get("moneda", "$AR")),
                cantidad=cantidad,
                mes_inicio=int(row.get("mes_inicio") or 1),
                meses=int(meses),
                amort_perc=amort,
                costo_unitario=round(cu, 4),
                comentario=str(row.get("comentario", "")),
                total=round(total, 2),
            )
            nuevos.append(g)
        s.gastos_generales = nuevos
        guardar()
        st.success(f"{len(nuevos)} líneas guardadas")
        st.rerun()

# Resumen por categoría
items_gg = [g for g in s.gastos_generales if g.tipo == "Item"]
if items_gg:
    st.divider()
    total_gg = sum(g.total for g in items_gg)
    st.metric("Total Gastos Generales", f"${total_gg:,.0f}")

    por_cat = {}
    for g in items_gg:
        por_cat[g.categoria] = por_cat.get(g.categoria, 0) + g.total
    df_cat = pd.DataFrame(
        [{"Categoría": k, "Total $": v, "%": v / total_gg * 100 if total_gg else 0}
         for k, v in sorted(por_cat.items(), key=lambda x: -x[1])]
    )
    st.dataframe(df_cat, hide_index=True, use_container_width=True,
                 column_config={
                     "Total $": st.column_config.NumberColumn(format="$%.0f"),
                     "%": st.column_config.NumberColumn(format="%.1f%%"),
                 })
