from pydantic import BaseModel, Field
from typing import List, Literal, Optional


TIPOS_RECURSO = ["Equipos", "Mano de Obra", "Materiales", "Combustibles", "Subcontratos", "Tpte Interno", "Auxiliares"]


class DatoCD(BaseModel):
    """Una fila en la tabla maestra de costos directos."""
    item_id: str                    # número del ítem (ej: "00.20.004.0001")
    item_uid: str = ""              # UID único del ítem (resuelve duplicados de número)
    tarea: str = ""                 # descripción de la tarea
    tarea_unidad: str = ""          # unidad de la tarea (m3, m2, etc.)
    incidencia: float = 1.0         # unidades de tarea por unidad de ítem
    rendimiento: float = 1.0        # unidades de tarea por día
    tipo_recurso: str = ""
    recurso: str = ""
    cuantia: float = 0.0            # recursos por día
    comentario: str = ""
    # Calculados
    cuantia_por_unidad: float = 0.0
    costo_unitario: float = 0.0     # por unidad de ítem


class Item(BaseModel):
    tipo: Literal["Título", "Item"] = "Item"
    numero: str                     # "00.20.004.0001"
    uid: str = ""                   # UID único para resolver números duplicados
    descripcion: str = ""
    unidad: str = ""
    cantidad: float = 0.0
    grupo: str = ""
    sub_grupo: str = ""
    margen: float = 0.0             # % margen sobre costo
    # Calculados
    costo_unitario: float = 0.0
    costo_total: float = 0.0
    precio_unitario: float = 0.0
    precio_total: float = 0.0


class GastoGeneral(BaseModel):
    id: int = 0
    tipo: Literal["Título", "Item"] = "Item"
    categoria: str = ""             # "01 Mensualizados", "02 Equipos", etc.
    recurso: str = ""
    unidad: str = ""
    moneda: str = "$AR"
    cantidad: float = 0.0
    mes_inicio: int = 1
    meses: int = 1
    amort_perc: float = 1.0         # fracción de amortización (1 = 100%)
    costo_unitario: float = 0.0
    comentario: str = ""
    # Calculado
    total: float = 0.0
