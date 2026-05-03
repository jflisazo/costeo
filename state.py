"""
Gestión del estado de sesión de Streamlit.
Centraliza la inicialización y serialización/deserialización del estado.
"""

from typing import Any
import streamlit as st
from models import (
    Proyecto, Equipo, MOJornalizada, MOMensualizada,
    Material, Combustible, Subcontrato, Auxiliar, CicloTransporte,
    Item, DatoCD, GastoGeneral, PlanTrabajo,
)
from storage import save_proyecto, load_proyecto


# ── Clave maestra del estado ─────────────────────────────────────────────────

DEFAULTS: dict[str, Any] = {
    "proyecto_nombre": "",
    "proyecto": Proyecto(),
    "equipos": [],
    "mo_jornalizada": [],
    "mo_mensualizada": [],
    "materiales": [],
    "combustibles": [],
    "subcontratos": [],
    "auxiliares": [],
    "transportes": [],
    "items": [],
    "datos_cd": [],
    "gastos_generales": [],
    "plan_trabajos": [],
}


def init_state():
    for k, v in DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ── Serialización ─────────────────────────────────────────────────────────────

def _ser(obj):
    if isinstance(obj, list):
        return [_ser(x) for x in obj]
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    return obj


def _de(cls, data):
    if isinstance(data, list):
        return [cls(**x) for x in data]
    return cls(**data)


def estado_a_dict() -> dict:
    s = st.session_state
    return {
        "proyecto": s.proyecto.model_dump(),
        "equipos": _ser(s.equipos),
        "mo_jornalizada": _ser(s.mo_jornalizada),
        "mo_mensualizada": _ser(s.mo_mensualizada),
        "materiales": _ser(s.materiales),
        "combustibles": _ser(s.combustibles),
        "subcontratos": _ser(s.subcontratos),
        "auxiliares": _ser(s.auxiliares),
        "transportes": _ser(s.transportes),
        "items": _ser(s.items),
        "datos_cd": _ser(s.datos_cd),
        "gastos_generales": _ser(s.gastos_generales),
        "plan_trabajos": _ser(s.plan_trabajos),
    }


def dict_a_estado(d: dict):
    st.session_state.proyecto = Proyecto(**d.get("proyecto", {}))
    st.session_state.equipos = _de(Equipo, d.get("equipos", []))
    st.session_state.mo_jornalizada = _de(MOJornalizada, d.get("mo_jornalizada", []))
    st.session_state.mo_mensualizada = _de(MOMensualizada, d.get("mo_mensualizada", []))
    st.session_state.materiales = _de(Material, d.get("materiales", []))
    st.session_state.combustibles = _de(Combustible, d.get("combustibles", []))
    st.session_state.subcontratos = _de(Subcontrato, d.get("subcontratos", []))
    st.session_state.auxiliares = _de(Auxiliar, d.get("auxiliares", []))
    st.session_state.transportes = _de(CicloTransporte, d.get("transportes", []))
    st.session_state.items = _de(Item, d.get("items", []))
    st.session_state.datos_cd = _de(DatoCD, d.get("datos_cd", []))
    st.session_state.gastos_generales = _de(GastoGeneral, d.get("gastos_generales", []))
    st.session_state.plan_trabajos = _de(PlanTrabajo, d.get("plan_trabajos", []))


def guardar():
    nombre = st.session_state.get("proyecto_nombre", "sin_nombre")
    if not nombre:
        nombre = "sin_nombre"
    save_proyecto(nombre, estado_a_dict())


def cargar(nombre: str):
    d = load_proyecto(nombre)
    if d:
        st.session_state.proyecto_nombre = nombre
        dict_a_estado(d)
        return True
    return False
