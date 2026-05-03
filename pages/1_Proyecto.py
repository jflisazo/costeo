import streamlit as st
from state import init_state, guardar
from models import Proyecto
from calculos import recalcular_todo

st.set_page_config(page_title="Proyecto", layout="wide")
init_state()

st.title("📋 Datos del Proyecto")

p = st.session_state.proyecto
s = st.session_state

with st.form("form_proyecto"):
    st.subheader("Parámetros del Contrato")
    c1, c2 = st.columns(2)
    empresa = c1.text_input("Empresa", value=p.empresa)
    comitente = c2.text_input("Comitente", value=p.comitente)
    obra = st.text_input("Obra", value=p.obra)

    c3, c4, c5 = st.columns(3)
    plazo = c3.number_input("Plazo (meses)", value=p.plazo_meses, min_value=1, step=1)
    moneda = c4.selectbox("Moneda oferta", ["$AR", "USD"], index=0 if p.moneda_oferta == "$AR" else 1)
    mes_base = c5.text_input("Mes base (YYYY-MM)", value=p.mes_base, placeholder="2024-01")

    c6, c7 = st.columns(2)
    plazo_pago = c6.number_input("Plazo de pago (días)", value=p.plazo_pago, step=1)
    anticipo = c7.number_input("Anticipo (%)", value=p.anticipo * 100, step=1.0) / 100

    st.subheader("Cotizaciones de Monedas")
    st.caption("Al cambiar la cotización y presionar **Guardar y Recalcular**, todos los costos se actualizan automáticamente.")
    col_usd, col_eur = st.columns(2)
    usd_anterior = p.cotizaciones.get("USD", 1460.0)
    eur_anterior = p.cotizaciones.get("EUR", 1715.0)
    usd = col_usd.number_input("USD ($/AR por dólar)", value=float(usd_anterior), step=10.0)
    eur = col_eur.number_input("EUR ($/AR por euro)", value=float(eur_anterior), step=10.0)

    st.subheader("Parámetros DNV (para equipos con método DNV)")
    d1, d2, d3 = st.columns(3)
    horas_mes = d1.number_input("HS/mes equipo", value=p.horas_mes_eq, step=1.0)
    tasa = d2.number_input("Tasa anual (%)", value=p.tasa_anual * 100, step=0.5) / 100
    vida_util = d3.number_input("Vida útil default (hs)", value=p.vida_util_hs, step=500.0)

    submitted = st.form_submit_button("💾 Guardar y Recalcular todo", use_container_width=True, type="primary")

if submitted:
    nuevo_proyecto = Proyecto(
        empresa=empresa,
        obra=obra,
        comitente=comitente,
        plazo_meses=int(plazo),
        moneda_oferta=moneda,
        mes_base=mes_base,
        cotizaciones={"USD": usd, "EUR": eur},
        plazo_pago=int(plazo_pago),
        anticipo=anticipo,
        horas_mes_eq=horas_mes,
        tasa_anual=tasa,
        vida_util_hs=vida_util,
    )
    st.session_state.proyecto = nuevo_proyecto

    cotiz_cambio = abs(usd - usd_anterior) > 0.01 or abs(eur - eur_anterior) > 0.01
    tiene_datos = bool(s.equipos or s.materiales or s.datos_cd)

    if tiene_datos:
        with st.spinner("Recalculando costos..."):
            resultado = recalcular_todo(
                nuevo_proyecto,
                s.equipos, s.mo_jornalizada, s.mo_mensualizada,
                s.materiales, s.combustibles, s.subcontratos,
                s.auxiliares, s.transportes,
                s.datos_cd, s.items, s.gastos_generales,
            )
        for k, v in resultado.items():
            setattr(st.session_state, k, v)

    guardar()

    if cotiz_cambio and tiene_datos:
        st.success(f"Cotización actualizada (USD: {usd_anterior:,.0f} → {usd:,.0f}) y costos recalculados en cascada.")
    elif tiene_datos:
        st.success("Proyecto guardado y costos recalculados.")
    else:
        st.success("Proyecto guardado.")

# ── Panel informativo ──────────────────────────────────────────────────────────
if s.equipos:
    st.divider()
    st.subheader("Impacto de la cotización actual")

    gasoil = next((c.costo for c in s.combustibles if "gas oil" in c.descripcion.lower()), 0)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("USD", f"${p.cotizaciones.get('USD', 0):,.0f}")
    c2.metric("EUR", f"${p.cotizaciones.get('EUR', 0):,.0f}")
    c3.metric("Gas Oil", f"${gasoil:,.2f}/lt" if gasoil else "—")
    c4.metric("Equipos cargados", len(s.equipos))

    items_obra = [i for i in s.items if i.tipo == "Item"]
    if items_obra:
        costo_cd = sum(i.costo_total for i in items_obra)
        total_gg = sum(g.total for g in s.gastos_generales if g.tipo == "Item")
        m1, m2, m3 = st.columns(3)
        m1.metric("Costo Directo", f"${costo_cd:,.0f}")
        m2.metric("Gastos Generales", f"${total_gg:,.0f}")
        m3.metric("Costo Total", f"${costo_cd + total_gg:,.0f}")
