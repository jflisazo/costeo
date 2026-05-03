import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from state import init_state
from models.items import TIPOS_RECURSO

st.set_page_config(page_title="Presupuesto", layout="wide")
init_state()

st.title("💰 Presupuesto y Plan de Trabajos")

s = st.session_state
p = s.proyecto

items_obra = [i for i in s.items if i.tipo == "Item"]
gg_items = [g for g in s.gastos_generales if g.tipo == "Item"]

if not items_obra:
    st.info("No hay ítems de obra cargados. Cargá ítems en la página **Ítems de Obra**.")
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# Resumen ejecutivo
# ══════════════════════════════════════════════════════════════════════════════
costo_cd = sum(i.costo_total for i in items_obra)
total_gg = sum(g.total for g in gg_items)
costo_total = costo_cd + total_gg

col1, col2, col3 = st.columns(3)
col1.metric("Costo Directo", f"${costo_cd:,.0f}")
col2.metric("Gastos Generales", f"${total_gg:,.0f}",
            delta=f"{total_gg/costo_cd*100:.1f}% del CD" if costo_cd else None)
col3.metric("Costo Total", f"${costo_total:,.0f}")

# Margen
st.divider()
margen_pct = st.slider("Margen / Beneficio (%)", min_value=0, max_value=40, value=10)
precio_oferta = costo_total * (1 + margen_pct / 100)
st.metric("Precio de Oferta", f"${precio_oferta:,.0f}",
          delta=f"+${precio_oferta - costo_total:,.0f}")

# ══════════════════════════════════════════════════════════════════════════════
# Tabla de ítems con precio oferta
# ══════════════════════════════════════════════════════════════════════════════
st.divider()
st.subheader("Planilla de Precios")

coef_gg = (costo_total / costo_cd) if costo_cd else 1
coef_oferta = (1 + margen_pct / 100) * coef_gg

rows = []
for i in s.items:
    pu_oferta = i.costo_unitario * coef_oferta if i.tipo == "Item" else 0
    pt_oferta = pu_oferta * i.cantidad if i.tipo == "Item" else 0
    rows.append({
        "N°": i.numero,
        "Tipo": i.tipo,
        "Descripción": i.descripcion,
        "Un": i.unidad,
        "Cantidad": i.cantidad if i.tipo == "Item" else None,
        "C. Unitario": i.costo_unitario if i.tipo == "Item" else None,
        "Costo Total": i.costo_total if i.tipo == "Item" else None,
        "P. Unitario": pu_oferta if i.tipo == "Item" else None,
        "Precio Total": pt_oferta if i.tipo == "Item" else None,
    })

df_items = pd.DataFrame(rows)
st.dataframe(
    df_items,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Cantidad": st.column_config.NumberColumn(format="%.2f"),
        "C. Unitario": st.column_config.NumberColumn(format="$%.2f"),
        "Costo Total": st.column_config.NumberColumn(format="$%.0f"),
        "P. Unitario": st.column_config.NumberColumn(format="$%.2f"),
        "Precio Total": st.column_config.NumberColumn(format="$%.0f"),
    },
    height=400,
)

precio_total_items = sum(r["Precio Total"] or 0 for r in rows)
st.metric("Total Oferta (ítems)", f"${precio_total_items:,.0f}")

# ══════════════════════════════════════════════════════════════════════════════
# Desglose por tipo de recurso (CD)
# ══════════════════════════════════════════════════════════════════════════════
st.divider()
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Desglose CD por tipo de recurso")
    desglose = {}
    for d in s.datos_cd:
        item = next((i for i in items_obra if i.numero == d.item_id), None)
        if item:
            contrib = d.costo_unitario * item.cantidad
            desglose[d.tipo_recurso] = desglose.get(d.tipo_recurso, 0) + contrib

    if desglose:
        df_des = pd.DataFrame(
            [{"Tipo": k, "Monto $": v, "%": v / costo_cd * 100 if costo_cd else 0}
             for k, v in sorted(desglose.items(), key=lambda x: -x[1])]
        )
        st.dataframe(df_des, hide_index=True, use_container_width=True,
                     column_config={
                         "Monto $": st.column_config.NumberColumn(format="$%.0f"),
                         "%": st.column_config.NumberColumn(format="%.1f%%"),
                     })

with col_b:
    st.subheader("Desglose CD por capítulo")
    por_cap = {}
    for i in items_obra:
        cap = i.numero.split(".")[0] if "." in i.numero else i.numero
        por_cap[cap] = por_cap.get(cap, 0) + i.costo_total

    if por_cap:
        fig = go.Figure(go.Pie(
            labels=list(por_cap.keys()),
            values=list(por_cap.values()),
            hole=0.4,
        ))
        fig.update_layout(height=350, margin=dict(t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# Plan de trabajos (distribución mensual uniforme como baseline)
# ══════════════════════════════════════════════════════════════════════════════
st.divider()
st.subheader("Plan de Trabajos — Histograma mensual")

plazo = p.plazo_meses or 12
# Distribución uniforme por defecto
costo_mensual = [costo_total / plazo] * plazo

fig_bar = go.Figure(go.Bar(
    x=[f"Mes {i+1}" for i in range(plazo)],
    y=costo_mensual,
    marker_color="steelblue",
    text=[f"${v:,.0f}" for v in costo_mensual],
    textposition="outside",
))
fig_bar.update_layout(
    yaxis_title="Costo ($AR)",
    height=350,
    margin=dict(t=10, b=40),
)
st.plotly_chart(fig_bar, use_container_width=True)
st.caption("Distribución uniforme de referencia. Para una distribución personalizada, usá la hoja PT del Excel original.")
