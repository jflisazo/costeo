"""
Cálculo del costo horario de equipos.

Métodos soportados:
  KEOPS      – CU pre-calculados por KEOPS; se escalan cuando cambia la cotización.
  DNV        – Fórmula estándar Dirección Nacional de Vialidad Argentina.
  Porcentaje – CU = precio_ar * porcentaje / uso_anual (equipos alquilados/simples).
  Manual_AR  – CU en $AR ingresados manualmente; no escalan con cotización.

Fórmula DNV (fuente: Manual DNV, Licitaciones de Obras Viales):
    precio_ar = precio_usd * cotiz_usd   (o precio_ar si moneda == "$AR")
    A_h = precio_ar * (1 - vr) / vida_util_hs
    I_h = precio_ar * (1 + vr) / 2 * tasa_anual / uso_anual
    cu_ai   = A_h + I_h
    cu_rr   = precio_ar * k_rr / vida_util_hs
    cu_comb = potencia * k_combustible * precio_gasoil
    costo_hora = cu_ai + cu_rr + cu_comb

Fórmula KEOPS (escalado por cotización):
    cotiz_nueva / cotiz_base:
    cu_ai_nuevo   = ratio_ai * precio * cotiz_nueva
    cu_rr_nuevo   = ratio_rr * precio * cotiz_nueva
    cu_comb_nuevo = potencia * k_combustible * precio_gasoil_nuevo
"""

from models.recursos import Equipo
from models.proyecto import Proyecto


def _cotiz(eq: Equipo, proyecto: Proyecto) -> float:
    """Retorna la cotización vigente de la moneda del equipo."""
    if eq.moneda == "$AR":
        return 1.0
    return proyecto.cotizaciones.get(eq.moneda, 1.0)


def calc_costo_equipo(eq: Equipo, proyecto: Proyecto, precio_gasoil: float) -> Equipo:
    """
    Recalcula cu_ai, cu_rr, cu_comb y costo_hora según el método del equipo.
    Retorna una nueva instancia con los campos calculados actualizados.
    """
    cotiz = _cotiz(eq, proyecto)

    if eq.metodo_costeo == "KEOPS":
        # Escalar ratios guardados al momento de importar con la nueva cotización.
        # ratio_ai = cu_ai_original / (precio * cotiz_base)
        # cu_ai_nuevo = ratio_ai * precio * cotiz_nueva
        precio_ar_nuevo = eq.precio * cotiz
        cu_ai = eq.ratio_ai * precio_ar_nuevo
        cu_rr = eq.ratio_rr * precio_ar_nuevo
        cu_comb = eq.potencia * eq.k_combustible * precio_gasoil

    elif eq.metodo_costeo == "DNV":
        precio_ar = eq.precio * cotiz
        vida = eq.vida_util_hs if eq.vida_util_hs > 0 else proyecto.vida_util_hs
        uso = eq.uso_anual if eq.uso_anual > 0 else 2000.0
        tasa = proyecto.tasa_anual

        a_h = precio_ar * (1.0 - eq.vr) / vida
        i_h = precio_ar * (1.0 + eq.vr) / 2.0 * tasa / uso
        cu_ai = a_h + i_h
        cu_rr = precio_ar * eq.k_rr / vida
        cu_comb = eq.potencia * eq.k_combustible * precio_gasoil

    elif eq.metodo_costeo == "Porcentaje":
        precio_ar = eq.precio * cotiz
        uso = eq.uso_anual if eq.uso_anual > 0 else 2000.0
        cu_ai = precio_ar * eq.porcentaje / uso
        cu_rr = 0.0
        cu_comb = eq.potencia * eq.k_combustible * precio_gasoil

    else:
        # Manual_AR: CU en $AR fijos; solo se actualiza combustible.
        cu_ai = eq.cu_ai
        cu_rr = eq.cu_rr
        cu_comb = eq.potencia * eq.k_combustible * precio_gasoil

    return eq.model_copy(update={
        "cu_ai": round(cu_ai, 4),
        "cu_rr": round(cu_rr, 4),
        "cu_comb": round(cu_comb, 4),
        "costo_hora": round(cu_ai + cu_rr + cu_comb, 4),
    })
