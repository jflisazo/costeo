from pydantic import BaseModel, Field
from typing import List, Literal


TIPOS_RECURSO = ["Equipos", "Mano de Obra", "Materiales", "Combustibles", "Subcontratos", "Tpte Interno", "Auxiliares"]


class DatoCD(BaseModel):
    """Una fila en la tabla maestra de costos directos."""
    item_aux: Literal["Item", "Aux"] = "Item"  # contenedor: ítem de obra o auxiliar
    item_id: str                    # número de ítem (si item_aux="Item") o descripción del auxiliar (si "Aux")
    item_uid: str = ""              # UID único del ítem (resuelve duplicados de número)
    tarea: str = ""                 # descripción de la tarea
    tarea_unidad: str = ""          # unidad de la tarea (m3, m2, etc.)
    incidencia: float = 1.0         # unidades de tarea por unidad de ítem
    rendimiento: float = 1.0        # unidades de tarea por día
    tipo_recurso: str = ""
    recurso: str = ""
    cuantia: float = 0.0            # recursos por día
    # Ajustes sobre el costo horario de equipos (Excel: %HS paro / %Esf. RR / %Esf. GO)
    perc_hs_paro: float = 0.0       # fracción de horas en paro (descontada del costo R&R+Comb)
    perc_esf_rr: float = 0.0        # incremento sobre CU R&R (esfuerzo extra)
    perc_esf_go: float = 0.0        # incremento sobre CU combustible (gasoil)
    comentario: str = ""
    # Calculados
    unidad_recurso: str = ""        # unidad del recurso (lookup según Tipo)
    costo_recurso: float = 0.0      # costo unitario del recurso (lookup según Tipo, con ajustes para Equipos)
    cu_tarea: float = 0.0           # C Unit Tarea = cuantia*costo/rendimiento (o *cuantia para materiales)
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
    categoria: str = ""             # "Item" en el Excel: "01 Mensualizados", "02 Equipos", etc.
    recurso: str = ""
    unidad: str = ""
    moneda: str = "$AR"
    cantidad: float = 0.0
    mes_inicio: int = 1             # "Comienzo" en el Excel
    meses: int = 1
    amort_perc: float = 1.0         # fracción de amortización (1 = 100%)
    costo_unitario: float = 0.0     # "Costo" en el Excel; si recurso coincide con MO mensual se autocompleta
    aux: str = ""                   # campo de texto libre auxiliar
    comentario: str = ""
    # Calculado: cantidad * meses * amort * costo * cotizacion(moneda)
    total: float = 0.0


class GanttFila(BaseModel):
    """Una fila de la tabla Gantt: distribución mensual del avance de un ítem.

    Los campos Tipo / numero / unidad / cantidad se reflejan desde la tabla Items.
    Las columnas mes_1..mes_60 contienen la fracción de avance por mes (0..1).
    Ctrl = sum(mes_1..mes_60); debería sumar 1.0 para ítems con cantidad > 0.
    """
    tipo: Literal["Título", "Item"] = "Item"
    numero: str = ""
    item_uid: str = ""
    descripcion: str = ""
    unidad: str = ""
    cantidad: float = 0.0
    meses: List[float] = Field(default_factory=lambda: [0.0] * 60)
    # Calculado
    ctrl: float = 0.0
