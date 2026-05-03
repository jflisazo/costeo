"""
Migración de UIDs: lee el JSON original, asigna UIDs a items/datos_cd,
y actualiza el proyecto en la base de datos.

Uso:
    cd /home/fernando/costeo
    python scripts/migrar_uids.py data/JM-Seccion-A1yA2.json 2
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm.attributes import flag_modified
from datetime import datetime

from backend.database import SessionLocal
from backend.models_db import ProyectoRecord
from calculos.costos_directos import asignar_uids_items
from models.items import Item, DatoCD


def migrar(json_path: str, proyecto_id: int):
    with open(json_path) as f:
        estado = json.load(f)

    # Asignar UIDs
    items_raw = [Item(**i) for i in estado.get("items", [])]
    datos_raw = [DatoCD(**d) for d in estado.get("datos_cd", [])]
    items_con_uid, datos_con_uid = asignar_uids_items(items_raw, datos_raw)

    # Calcular margen implícito desde precio_unitario importado del Excel
    items_con_margen = []
    for item in items_con_uid:
        if item.tipo == "Item" and item.costo_unitario > 0 and item.precio_unitario > item.costo_unitario:
            margen = round(item.precio_unitario / item.costo_unitario - 1.0, 6)
            items_con_margen.append(item.model_copy(update={"margen": margen}))
        else:
            items_con_margen.append(item)

    estado["items"] = [i.model_dump() for i in items_con_margen]
    estado["datos_cd"] = [d.model_dump() for d in datos_con_uid]
    estado.setdefault("plan_trabajos", [])

    db = SessionLocal()
    try:
        rec = db.query(ProyectoRecord).filter(ProyectoRecord.id == proyecto_id).first()
        if not rec:
            print(f"Proyecto {proyecto_id} no encontrado.")
            return
        rec.estado = estado
        rec.updated_at = datetime.utcnow()
        flag_modified(rec, "estado")
        db.commit()
        print(f"Migración completada: proyecto '{rec.nombre}' (id={proyecto_id})")

        # Verificar
        db.refresh(rec)
        items_check = [i for i in rec.estado.get("items", []) if i.get("tipo") == "Item"]
        with_uid = sum(1 for i in items_check if i.get("uid"))
        cd_check = rec.estado.get("datos_cd", [])
        cd_with_uid = sum(1 for d in cd_check if d.get("item_uid"))
        print(f"  Items: {len(items_check)} total, {with_uid} con UID")
        print(f"  DatoCD: {len(cd_check)} total, {cd_with_uid} con item_uid")
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python scripts/migrar_uids.py <json_path> <proyecto_id>")
        sys.exit(1)
    migrar(sys.argv[1], int(sys.argv[2]))
