from pydantic import BaseModel, Field
from typing import Dict, List


class ResumenPresupuesto(BaseModel):
    costo_directo_total: float = 0.0
    gastos_generales_total: float = 0.0
    costo_total: float = 0.0
    margen_porcentaje: float = 0.0
    precio_total: float = 0.0
    # Desglose por tipo de recurso
    desglose_cd: Dict[str, float] = Field(default_factory=dict)
    # Desglose por capítulo de ítems
    desglose_items: Dict[str, float] = Field(default_factory=dict)


class PlanTrabajo(BaseModel):
    """Distribución mensual del costo directo."""
    item_id: str
    descripcion: str
    distribucion: List[float] = Field(default_factory=list)  # fracción por mes, len == plazo_meses
