"""
Persistencia en JSON. Cada proyecto se guarda en data/<nombre>.json.
El estado completo de la app es un dict con las siguientes claves:
  proyecto, equipos, mo_jornalizada, mo_mensualizada,
  materiales, combustibles, subcontratos, auxiliares, transportes,
  items, datos_cd, gastos_generales
"""

import json
import os
from pathlib import Path
from typing import Optional

DATA_DIR = Path(__file__).parent.parent / "data"


def _ensure_dir():
    DATA_DIR.mkdir(exist_ok=True)


def _path(nombre: str) -> Path:
    safe = nombre.replace("/", "_").replace("\\", "_")
    return DATA_DIR / f"{safe}.json"


def save_proyecto(nombre: str, estado: dict) -> None:
    _ensure_dir()
    with open(_path(nombre), "w", encoding="utf-8") as f:
        json.dump(estado, f, ensure_ascii=False, indent=2)


def load_proyecto(nombre: str) -> Optional[dict]:
    p = _path(nombre)
    if not p.exists():
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def list_proyectos() -> list[str]:
    _ensure_dir()
    return [f.stem for f in DATA_DIR.glob("*.json")]


def delete_proyecto(nombre: str) -> None:
    p = _path(nombre)
    if p.exists():
        p.unlink()
