"""
Plan de trabajos: distribución % del costo de cada ítem en los meses del proyecto.
Permite editar la distribución manualmente o aplicar perfiles predefinidos.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from state import init_state, guardar
from models import PlanTrabajo

st.set_page_config(page_title="Plan de Trabajos", layout="wide")
init_state()

st.title("📅 Plan de Trabajos")

s = st.session_state
p = s.proyecto
plazo = max(p.plazo_meses, 1)

items_obra = [i for i in s["items"] if i.tipo == "Item" and i.costo_total > 0]
if not items_obra:
    st.info("No hay ítems con costo calculado. Completá la página **Ítems de Obra** primero.")
    st.stop()

# ── Estado del plan ────────────────────────────────────────────────────────────
# Construir/actualizar plan de trabajos en session state
if "plan_trabajos" not in s or not s.plan_trabajos:
    # Plan vacío: distribuir uniformemente por defecto
    s.plan_trabajos = [
        PlanTrabajo(
            item_id=i.numero,
            descripcion=i.descripcion,
            distribucion=[round(1 / plazo, 6)] * plazo,
        )
        for i in items_obra
    ]
else:
    # Sincronizar ítems nuevos
    ids_plan = {pt.item_id for pt in s.plan_trabajos}
    for i in items_obra:
        if i.numero not in ids_plan:
            s.plan_trabajos.append(PlanTrabajo(
                item_id=i.numero,
                descripcion=i.descripcion,
                distribucion=[round(1 / plazo, 6)] * plazo,
            ))

plan_map = {pt.item_id: pt for pt in s.plan_trabajos}

# ── Perfil de distribución rápida ─────────────────────────────────────────────
st.subheader("Distribución rápida")
col1, col2, col3 = st.columns([2, 1, 1])
perfil = col1.selectbox(
    "Perfil",
    ["Uniforme", "Rampa (inicio lento)", "Campana (pico al 50%)", "Manual"],
)
items_sel_ids = col2.multiselect(
    "Aplicar a ítems", [i.numero for i in items_obra],
    default=[i.numero for i in items_obra],
    max_selections=20,
)

if col3.button("Aplicar perfil") and perfil != "Manual":
    meses = list(range(1, plazo + 1))
    if perfil == "Uniforme":
        dist = [1 / plazo] * plazo
    elif perfil == "Rampa (inicio lento)":
        raw = [float(m) for m in meses]
        s_raw = sum(raw)
        dist = [r / s_raw for r in raw]
    else:  # "Campana (pico al 50%)"
        import math
        mid = plazo / 2
        raw = [math.exp(-((m - mid) ** 2) / (2 * (plazo / 4) ** 2)) for m in meses]
        s_raw = sum(raw)
        dist = [r / s_raw for r in raw]
    for item_id in items_sel_ids:
        if item_id in plan_map:
            plan_map[item_id] = plan_map[item_id].model_copy(update={"distribucion": dist})
    s.plan_trabajos = list(plan_map.values())
    guardar()
    st.success("Perfil aplicado")
    st.rerun()

# ── Tabla editable de distribución ────────────────────────────────────────────
st.divider()
st.subheader("Distribución % por ítem y mes")
st.caption("Cada fila debe sumar 100%. Los valores son porcentajes del costo total del ítem.")

# Construir DataFrame: filas = ítems, columnas = Mes 1..N
cols_mes = [f"M{i+1}" for i in range(plazo)]
rows_plan = []
for item in items_obra:
    pt = plan_map.get(item.numero)
    dist = pt.distribucion if pt else [1 / plazo] * plazo
    # Asegurar longitud correcta
    if len(dist) < plazo:
        dist = dist + [0.0] * (plazo - len(dist))
    dist = dist[:plazo]
    row = {"Ítem": item.numero, "Descripción": item.descripcion[:40], "Total $": item.costo_total}
    row.update({f"M{i+1}": round(d * 100, 2) for i, d in enumerate(dist)})
    rows_plan.append(row)

df_plan = pd.DataFrame(rows_plan)

# Calcular suma por ítem
df_plan["Suma %"] = df_plan[cols_mes].sum(axis=1).round(2)

edited_plan = st.data_editor(
    df_plan,
    use_container_width=True,
    num_rows="fixed",
    column_config={
        "Ítem": st.column_config.TextColumn(disabled=True, width="small"),
        "Descripción": st.column_config.TextColumn(disabled=True, width="medium"),
        "Total $": st.column_config.NumberColumn(disabled=True, format="$%.0f"),
        "Suma %": st.column_config.NumberColumn(disabled=True, format="%.1f%%"),
        **{m: st.column_config.NumberColumn(m, format="%.1f", min_value=0, max_value=100) for m in cols_mes},
    },
    key="plan_editor",
    height=400,
)

if st.button("💾 Guardar plan de trabajos"):
    nuevos_pt = []
    for _, row in edited_plan.iterrows():
        item_id = str(row["Ítem"])
        dist_pct = [float(row.get(m, 0) or 0) for m in cols_mes]
        total = sum(dist_pct)
        dist = [v / 100 for v in dist_pct] if total > 0 else [1 / plazo] * plazo
        item = next((i for i in items_obra if i.numero == item_id), None)
        nuevos_pt.append(PlanTrabajo(
            item_id=item_id,
            descripcion=item.descripcion if item else "",
            distribucion=dist,
        ))
    s.plan_trabajos = nuevos_pt
    guardar()
    st.success("Plan guardado")
    st.rerun()

# ── Histograma de inversión mensual ───────────────────────────────────────────
st.divider()
st.subheader("Histograma de inversión mensual")

inversion_mensual = [0.0] * plazo
for pt in s.plan_trabajos:
    item = next((i for i in items_obra if i.numero == pt.item_id), None)
    if not item:
        continue
    dist = pt.distribucion
    if len(dist) < plazo:
        dist = dist + [0.0] * (plazo - len(dist))
    for mes_i, frac in enumerate(dist[:plazo]):
        inversion_mensual[mes_i] += item.costo_total * frac

acumulado = []
acc = 0.0
for v in inversion_mensual:
    acc += v
    acumulado.append(acc)

fig = go.Figure()
fig.add_bar(
    x=[f"Mes {i+1}" for i in range(plazo)],
    y=inversion_mensual,
    name="Inversión mensual",
    marker_color="steelblue",
)
fig.add_scatter(
    x=[f"Mes {i+1}" for i in range(plazo)],
    y=acumulado,
    name="Acumulado",
    mode="lines+markers",
    yaxis="y2",
    line=dict(color="orange", width=2),
)
fig.update_layout(
    yaxis=dict(title="Inversión mensual ($)"),
    yaxis2=dict(title="Acumulado ($)", overlaying="y", side="right"),
    legend=dict(x=0, y=1),
    height=400,
    margin=dict(t=10),
)
st.plotly_chart(fig, use_container_width=True)

total_plan = sum(inversion_mensual)
st.metric("Total planificado", f"${total_plan:,.0f}")
