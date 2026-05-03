from pydantic import BaseModel, Field
from typing import Dict


class CotizacionMoneda(BaseModel):
    moneda: str
    cotizacion: float


class Proyecto(BaseModel):
    empresa: str = ""
    obra: str = ""
    comitente: str = ""
    plazo_meses: int = 12
    moneda_oferta: str = "$AR"
    mes_base: str = ""          # Ej: "2024-01"
    cotizaciones: Dict[str, float] = Field(default_factory=lambda: {"USD": 1460.0, "EUR": 1715.0})
    calculo: str = "Automático"  # "Automático" | "Manual"
    plazo_pago: int = 30
    anticipo: float = 0.0
    # Parámetros DNV para equipos
    horas_mes_eq: float = 200.0
    tasa_anual: float = 0.10     # tasa de interés anual
    vida_util_hs: float = 10000.0
