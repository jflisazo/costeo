"""
Costeo de Obra Civil — Aplicación Streamlit
Punto de entrada principal (home).
"""

import streamlit as st
from state import init_state, guardar, cargar
from storage import list_proyectos, delete_proyecto

st.set_page_config(
    page_title="Costeo de Obra",
    page_icon="🏗️",
    layout="wide",
)

init_state()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🏗️ Costeo de Obra")
    st.divider()

    proyectos = list_proyectos()
    st.subheader("Proyectos")

    col1, col2 = st.columns([3, 1])
    with col1:
        nombre_nuevo = st.text_input("Nuevo proyecto", placeholder="Nombre...", label_visibility="collapsed")
    with col2:
        if st.button("➕", help="Crear proyecto"):
            if nombre_nuevo:
                st.session_state.proyecto_nombre = nombre_nuevo
                guardar()
                st.rerun()

    if proyectos:
        seleccion = st.selectbox("Cargar proyecto", ["— seleccionar —"] + proyectos)
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("📂 Abrir") and seleccion != "— seleccionar —":
                cargar(seleccion)
                st.rerun()
        with col_b:
            if st.button("🗑️ Borrar") and seleccion != "— seleccionar —":
                delete_proyecto(seleccion)
                st.rerun()

    st.divider()
    if st.session_state.proyecto_nombre:
        st.caption(f"Proyecto activo: **{st.session_state.proyecto_nombre}**")
        if st.button("💾 Guardar", use_container_width=True):
            guardar()
            st.success("Guardado")

# ── Página home ───────────────────────────────────────────────────────────────
st.title("Costeo de Obra Civil")

if not st.session_state.proyecto_nombre:
    st.info("Creá o cargá un proyecto desde la barra lateral para comenzar.")
else:
    p = st.session_state.proyecto
    st.subheader(p.obra or "Sin nombre de obra")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Empresa", p.empresa or "—")
    col2.metric("Comitente", p.comitente or "—")
    col3.metric("Plazo", f"{p.plazo_meses} meses")
    col4.metric("Moneda", p.moneda_oferta)

    st.divider()

    # Resumen rápido
    equipos = st.session_state.equipos
    materiales = st.session_state.materiales
    items = [i for i in st.session_state["items"] if i.tipo == "Item"]
    datos_cd = st.session_state.datos_cd
    gg = st.session_state.gastos_generales

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Equipos", len(equipos))
    c2.metric("Materiales", len(materiales))
    c3.metric("Ítems de obra", len(items))
    c4.metric("Recursos CD", len(datos_cd))
    c5.metric("Gastos Grales", len([g for g in gg if g.tipo == "Item"]))

    if items:
        costo_cd = sum(i.costo_total for i in items)
        total_gg = sum(g.total for g in gg if g.tipo == "Item")
        st.divider()
        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("Costo Directo Total", f"${costo_cd:,.0f}")
        mc2.metric("Gastos Generales", f"${total_gg:,.0f}")
        mc3.metric("Costo Total", f"${costo_cd + total_gg:,.0f}")

    st.divider()
    st.caption("Navegá usando el menú de la izquierda.")
