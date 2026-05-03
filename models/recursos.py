from pydantic import BaseModel, Field
from typing import List, Literal


class Equipo(BaseModel):
    nombre: str
    marca: str = ""
    modelo: str = ""
    potencia: float = 0.0           # HP
    moneda: str = "USD"
    precio: float = 0.0             # precio en su moneda original
    k_combustible: float = 0.0      # litros/HP/hora
    propiedad: str = "Propio"       # "Propio" | "Alquilado"
    # Parámetros DNV (se usan cuando metodo_costeo="DNV")
    vida_util_hs: float = 10000.0   # horas totales de vida útil
    vr: float = 0.35                # valor residual (fracción)
    uso_anual: float = 2000.0       # horas de uso anuales
    k_rr: float = 0.65              # coeficiente reparaciones y repuestos
    metodo_costeo: str = "KEOPS"    # "KEOPS" | "DNV" | "Porcentaje" | "Manual_AR"
    porcentaje: float = 0.04        # % anual sobre precio; solo si metodo == "Porcentaje"
    # Para KEOPS: ratios CU/precio_ar calculados al importar.
    # Permiten escalar cuando cambia la cotización sin la base de datos KEOPS.
    ratio_ai: float = 0.0           # cu_ai / precio_ar al momento del import
    ratio_rr: float = 0.0           # cu_rr / precio_ar al momento del import
    cotiz_base: float = 1.0         # cotizacion USD usada al calcular/importar los CU
    # Calculados (se actualizan en cada recálculo)
    cu_ai: float = 0.0
    cu_rr: float = 0.0
    cu_comb: float = 0.0
    costo_hora: float = 0.0


class MOJornalizada(BaseModel):
    funcion: str
    id: int = 0                     # categoría UOCRA: 1=Of.esp, 2=Oficial, 3=Medio, 4=Ayudante
    moneda: str = "$AR"
    bruto: float = 0.0
    aguinaldo: float = 0.0
    vacaciones: float = 0.0
    cargas_sociales: float = 0.0
    bolsillo: float = 0.0           # adicional de zona / bolsillo
    viatico: float = 0.0
    horas_mes: float = 200.0
    # Calculado
    costo_hora: float = 0.0


class MOMensualizada(BaseModel):
    funcion: str
    moneda: str = "$AR"
    neto: float = 0.0
    bruto: float = 0.0              # bruto = neto / (1 - aporte_empleado)
    aguinaldo: float = 0.0
    dias_vacaciones: int = 14
    vacaciones: float = 0.0
    cargas_sociales: float = 0.0
    prop_despido: float = 0.0
    # Calculado
    costo_mes: float = 0.0


class Material(BaseModel):
    numero: int = 0
    descripcion: str
    unidad: str = ""
    moneda: str = "$AR"
    proveedor: str = ""
    origen: str = ""
    distancia_km: float = 0.0
    costo_origen: float = 0.0
    costo_flete: float = 0.0        # $/km (calculado: distancia * tarifa)
    otros: float = 0.0
    perc_perdida: float = 0.0
    # Calculado
    costo: float = 0.0


class Combustible(BaseModel):
    descripcion: str
    unidad: str = "lts"
    moneda: str = "$AR"
    proveedor: str = ""
    costo_origen: float = 0.0
    otros: float = 0.0
    # Calculado
    costo: float = 0.0


class Subcontrato(BaseModel):
    numero: int = 0
    descripcion: str
    unidad: str = ""
    moneda: str = "$AR"
    proveedor: str = ""
    costo_or: float = 0.0
    otros: float = 0.0
    # Calculado
    costo: float = 0.0


class RecursoAux(BaseModel):
    """Fila de composición de un Auxiliar (misma estructura que DatoCD)."""
    tarea: str = ""
    tarea_unidad: str = ""
    incidencia: float = 1.0
    rendimiento: float = 1.0
    tipo_recurso: str = ""          # "Equipos"|"Mano de Obra"|"Materiales"|"Combustibles"|"Subcontratos"
    recurso: str = ""
    cuantia: float = 0.0
    comentario: str = ""
    # Calculados
    cuantia_por_unidad: float = 0.0
    costo_unitario: float = 0.0


class Auxiliar(BaseModel):
    tipo: str = "Auxiliar"          # "Auxiliar" | "Elaborados" | "Tpte Interno"
    descripcion: str
    unidad: str = ""
    recursos: List[RecursoAux] = Field(default_factory=list)
    # Calculado
    costo: float = 0.0


class CicloTransporte(BaseModel):
    descripcion: str
    unidad: str = "m3"
    equipo: str = ""
    capacidad: float = 0.0          # tn o m3
    distancia_km: float = 0.0
    rendimiento_base: float = 0.0   # unidades/día de referencia
    vel_ida: float = 40.0           # km/h
    vel_vuelta: float = 40.0
    tiempo_espera: float = 5.0      # minutos
    tiempo_carga: float = 5.0
    tiempo_descarga: float = 5.0
    hs_dia: float = 10.0
    # Calculados
    tiempo_viaje_min: float = 0.0
    tiempo_ciclo_min: float = 0.0
    rend_dia: float = 0.0
    n_camiones: float = 0.0
    costo: float = 0.0              # $/unidad
