import streamlit as st
import pandas as pd
from state import init_state, guardar
from models import Auxiliar, RecursoAux
from calculos.costos_directos import lookup_costo_recurso, recalcular_datos_cd
from models.items import TIPOS_RECURSO

st.set_page_config(page_title="Auxiliares", layout="wide")
init_state()

st.title("🔧 Ítems Auxiliares y Elaborados")

s = st.session_state

# ── Lista de auxiliares ────────────────────────────────────────────────────────
nombres = [a.descripcion for a in s.auxiliares]
col1, col2 = st.columns([3, 1])

with col1:
    sel = st.selectbox("Seleccionar auxiliar", ["— nuevo —"] + nombres)

with col2:
    if st.button("➕ Nuevo auxiliar"):
        st.session_state._aux_nuevo = True
        st.rerun()

# ── Formulario para crear/editar un auxiliar ──────────────────────────────────
if sel == "— nuevo —" or st.session_state.get("_aux_nuevo"):
    with st.form("form_aux_nuevo"):
        st.subheader("Nuevo auxiliar")
        cc1, cc2, cc3 = st.columns(3)
        desc = cc1.text_input("Descripción")
        unidad = cc2.text_input("Unidad")
        tipo = cc3.selectbox("Tipo", ["Auxiliar", "Elaborados", "Tpte Interno"])
        if st.form_submit_button("Crear"):
            if desc:
                aux = Auxiliar(tipo=tipo, descripcion=desc, unidad=unidad)
                s.auxiliares.append(aux)
                guardar()
                st.session_state._aux_nuevo = False
                st.rerun()
    if sel != "— nuevo —":
        st.session_state._aux_nuevo = False

elif sel in nombres:
    idx = nombres.index(sel)
    aux = s.auxiliares[idx]

    st.subheader(f"{aux.tipo}: {aux.descripcion} [{aux.unidad}]")
    st.caption(f"Costo calculado: **${aux.costo:,.2f} / {aux.unidad}**")

    # Tabla de recursos del auxiliar
    COLS_REC = ["tarea", "tarea_unidad", "incidencia", "rendimiento",
                "tipo_recurso", "recurso", "cuantia", "comentario",
                "cuantia_por_unidad", "costo_unitario"]

    def rec_a_df(recursos):
        if not recursos:
            return pd.DataFrame(columns=COLS_REC)
        return pd.DataFrame([{c: getattr(r, c, 0) for c in COLS_REC} for r in recursos])

    edited = st.data_editor(
        rec_a_df(aux.recursos),
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "tarea": st.column_config.TextColumn("Tarea", width="medium"),
            "tarea_unidad": st.column_config.TextColumn("Un Tarea"),
            "incidencia": st.column_config.NumberColumn("Incidencia", format="%.4f"),
            "rendimiento": st.column_config.NumberColumn("Rendimiento/día", format="%.2f"),
            "tipo_recurso": st.column_config.SelectboxColumn("Tipo", options=TIPOS_RECURSO),
            "recurso": st.column_config.TextColumn("Recurso", width="medium"),
            "cuantia": st.column_config.NumberColumn("Cuantía/día", format="%.4f"),
            "comentario": st.column_config.TextColumn("Comentario"),
            "cuantia_por_unidad": st.column_config.NumberColumn("Cuantía/Un", disabled=True, format="%.6f"),
            "costo_unitario": st.column_config.NumberColumn("CU $", disabled=True, format="%.4f"),
        },
        key=f"aux_editor_{idx}",
    )

    col_a, col_b = st.columns([1, 5])
    with col_a:
        if st.button("⚙️ Recalcular y Guardar"):
            nuevos_rec = []
            for _, row in edited.iterrows():
                if not row.get("recurso"):
                    continue
                rec = RecursoAux(
                    tarea=str(row.get("tarea", "")),
                    tarea_unidad=str(row.get("tarea_unidad", "")),
                    incidencia=float(row.get("incidencia") or 1),
                    rendimiento=float(row.get("rendimiento") or 1),
                    tipo_recurso=str(row.get("tipo_recurso", "")),
                    recurso=str(row.get("recurso", "")),
                    cuantia=float(row.get("cuantia") or 0),
                    comentario=str(row.get("comentario", "")),
                )
                # Calcular
                rend = rec.rendimiento if rec.rendimiento != 0 else 1
                rec = rec.model_copy(update={
                    "cuantia_por_unidad": round((rec.cuantia / rend) * rec.incidencia, 6)
                })
                costo_rec = lookup_costo_recurso(
                    rec.tipo_recurso, rec.recurso,
                    s.equipos, s.mo_jornalizada, s.mo_mensualizada,
                    s.materiales, s.combustibles, s.subcontratos,
                    s.auxiliares, s.transportes,
                )
                rec = rec.model_copy(update={
                    "costo_unitario": round(rec.cuantia_por_unidad * costo_rec, 4)
                })
                nuevos_rec.append(rec)

            costo_total = sum(r.costo_unitario for r in nuevos_rec)
            s.auxiliares[idx] = aux.model_copy(update={
                "recursos": nuevos_rec,
                "costo": round(costo_total, 4),
            })
            guardar()
            st.success(f"Auxiliar '{aux.descripcion}' → ${costo_total:,.2f}")
            st.rerun()

    with col_b:
        if st.button("🗑️ Eliminar auxiliar", type="secondary"):
            s.auxiliares.pop(idx)
            guardar()
            st.rerun()

# ── Resumen de todos los auxiliares ───────────────────────────────────────────
if s.auxiliares:
    st.divider()
    st.subheader("Resumen")
    df_res = pd.DataFrame([
        {"Tipo": a.tipo, "Descripción": a.descripcion, "Unidad": a.unidad, "Costo": a.costo}
        for a in s.auxiliares
    ])
    st.dataframe(df_res, use_container_width=True, hide_index=True,
                 column_config={"Costo": st.column_config.NumberColumn(format="$%.2f")})
