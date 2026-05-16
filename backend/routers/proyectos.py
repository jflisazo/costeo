import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Body, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.database import get_db
from backend.models_db import ProyectoRecord
from calculos import recalcular_todo
from calculos.costos_directos import asignar_uids_items
from importar.excel_reader import leer_excel
from models import (
    Auxiliar, Combustible, CicloTransporte, DatoCD, Equipo, GanttFila,
    GastoGeneral, Item, Material, MOJornalizada, MOMensualizada,
    Proyecto, Subcontrato,
)

router = APIRouter()

SECCIONES = {
    "proyecto", "equipos", "mo_jornalizada", "mo_mensualizada",
    "materiales", "combustibles", "subcontratos", "auxiliares",
    "transportes", "items", "datos_cd", "gastos_generales",
    "plan_trabajos", "gantt",
}


def _estado_vacio() -> dict:
    return {
        "proyecto": Proyecto().model_dump(),
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
        "gantt": [],
    }


def _get_or_404(db: Session, proyecto_id: int) -> ProyectoRecord:
    rec = db.query(ProyectoRecord).filter(ProyectoRecord.id == proyecto_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return rec


def _deserializar(estado: dict) -> dict:
    return {
        "proyecto":   Proyecto(**estado.get("proyecto", {})),
        "equipos":    [Equipo(**e) for e in estado.get("equipos", [])],
        "mo_jorn":    [MOJornalizada(**m) for m in estado.get("mo_jornalizada", [])],
        "mo_mens":    [MOMensualizada(**m) for m in estado.get("mo_mensualizada", [])],
        "materiales": [Material(**m) for m in estado.get("materiales", [])],
        "combustibles": [Combustible(**c) for c in estado.get("combustibles", [])],
        "subcontratos": [Subcontrato(**s) for s in estado.get("subcontratos", [])],
        "auxiliares": [Auxiliar(**a) for a in estado.get("auxiliares", [])],
        "transportes": [CicloTransporte(**t) for t in estado.get("transportes", [])],
        "datos_cd":   [DatoCD(**d) for d in estado.get("datos_cd", [])],
        "items":      [Item(**i) for i in estado.get("items", [])],
        "gastos_generales": [GastoGeneral(**g) for g in estado.get("gastos_generales", [])],
        "gantt":      [GanttFila(**g) for g in estado.get("gantt", [])],
    }


def _rec_to_resp(rec: ProyectoRecord) -> dict:
    return {"id": rec.id, "nombre": rec.nombre, "estado": rec.estado,
            "updated_at": rec.updated_at.isoformat() if rec.updated_at else None}


# ── List / Create ─────────────────────────────────────────────────────────────

@router.get("/proyectos")
def listar(db: Session = Depends(get_db)):
    rows = db.query(ProyectoRecord).all()
    return [{"id": r.id, "nombre": r.nombre,
             "updated_at": r.updated_at.isoformat() if r.updated_at else None}
            for r in rows]


@router.post("/proyectos", status_code=201)
def crear(body: dict = Body(...), db: Session = Depends(get_db)):
    nombre = (body.get("nombre") or "").strip()
    if not nombre:
        raise HTTPException(400, "nombre requerido")
    if db.query(ProyectoRecord).filter(ProyectoRecord.nombre == nombre).first():
        raise HTTPException(409, "Ya existe un proyecto con ese nombre")
    rec = ProyectoRecord(nombre=nombre, estado=_estado_vacio())
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return _rec_to_resp(rec)


# ── Get / Delete ──────────────────────────────────────────────────────────────

@router.get("/proyectos/{pid}")
def obtener(pid: int, db: Session = Depends(get_db)):
    return _rec_to_resp(_get_or_404(db, pid))


@router.delete("/proyectos/{pid}", status_code=204)
def eliminar(pid: int, db: Session = Depends(get_db)):
    rec = _get_or_404(db, pid)
    db.delete(rec)
    db.commit()


# ── Patch section ─────────────────────────────────────────────────────────────

@router.patch("/proyectos/{pid}/{seccion}")
def actualizar_seccion(
    pid: int,
    seccion: str,
    body: Any = Body(...),
    db: Session = Depends(get_db),
):
    if seccion not in SECCIONES:
        raise HTTPException(400, f"Sección inválida: {seccion}")
    rec = _get_or_404(db, pid)
    nuevo_estado = dict(rec.estado)
    nuevo_estado[seccion] = body
    rec.estado = nuevo_estado
    rec.updated_at = datetime.utcnow()
    flag_modified(rec, "estado")
    db.commit()
    db.refresh(rec)
    return _rec_to_resp(rec)


# ── Recalcular en cascada ─────────────────────────────────────────────────────

@router.post("/proyectos/{pid}/recalcular")
def recalcular(pid: int, db: Session = Depends(get_db)):
    rec = _get_or_404(db, pid)
    m = _deserializar(rec.estado)
    resultado = recalcular_todo(
        m["proyecto"], m["equipos"], m["mo_jorn"], m["mo_mens"],
        m["materiales"], m["combustibles"], m["subcontratos"],
        m["auxiliares"], m["transportes"], m["datos_cd"],
        m["items"], m["gastos_generales"], m["gantt"],
    )
    nuevo_estado = dict(rec.estado)
    for k, v in resultado.items():
        nuevo_estado[k] = [x.model_dump() for x in v]
    rec.estado = nuevo_estado
    rec.updated_at = datetime.utcnow()
    flag_modified(rec, "estado")
    db.commit()
    db.refresh(rec)
    return _rec_to_resp(rec)


def _aplicar_uids(estado: dict) -> dict:
    """Asigna UIDs a items y datos_cd, y calcula coef_oferta global desde precio importado."""
    items_raw = [Item(**i) for i in estado.get("items", [])]
    datos_raw = [DatoCD(**d) for d in estado.get("datos_cd", [])]
    items_con_uid, datos_con_uid = asignar_uids_items(items_raw, datos_raw)

    # Coef. oferta global = sum(precio_total) / sum(costo_total) sobre ítems con CU>0
    total_costo = sum(i.costo_total for i in items_con_uid
                      if i.tipo == "Item" and i.costo_total > 0)
    total_precio = sum(i.precio_total for i in items_con_uid
                       if i.tipo == "Item" and i.costo_total > 0)
    coef = round(total_precio / total_costo, 6) if total_costo > 0 else 1.0

    estado = dict(estado)
    estado["items"] = [i.model_dump() for i in items_con_uid]
    estado["datos_cd"] = [d.model_dump() for d in datos_con_uid]
    proyecto_dict = dict(estado.get("proyecto", {}))
    proyecto_dict["coef_oferta"] = coef
    estado["proyecto"] = proyecto_dict
    return estado


# ── Importar Excel ────────────────────────────────────────────────────────────

@router.post("/proyectos/{pid}/importar-excel")
async def importar_excel(
    pid: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    rec = _get_or_404(db, pid)
    with tempfile.NamedTemporaryFile(suffix=".xlsm", delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    try:
        estado_importado = leer_excel(tmp_path)
    finally:
        os.unlink(tmp_path)
    estado_importado.setdefault("plan_trabajos", [])
    estado_importado.setdefault("gantt", [])
    estado_importado = _aplicar_uids(estado_importado)
    rec.estado = estado_importado
    rec.updated_at = datetime.utcnow()
    flag_modified(rec, "estado")
    db.commit()
    db.refresh(rec)
    return _rec_to_resp(rec)


# ── Importar JSON ─────────────────────────────────────────────────────────────

@router.post("/proyectos/{pid}/importar-json")
async def importar_json(
    pid: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    rec = _get_or_404(db, pid)
    contenido = await file.read()
    import json
    try:
        estado_importado = json.loads(contenido)
    except Exception as e:
        raise HTTPException(400, f"JSON inválido: {e}")
    estado_importado.setdefault("plan_trabajos", [])
    estado_importado.setdefault("gantt", [])
    estado_importado = _aplicar_uids(estado_importado)
    rec.estado = estado_importado
    rec.updated_at = datetime.utcnow()
    flag_modified(rec, "estado")
    db.commit()
    db.refresh(rec)
    return _rec_to_resp(rec)
