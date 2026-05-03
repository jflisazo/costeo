from models.recursos import Material, Combustible, Subcontrato
from models.proyecto import Proyecto

# Tarifa de flete referencial $/km/tn
TARIFA_FLETE_DEFAULT = 0.075  # ajustar por proyecto


def calc_costo_material(mat: Material, proyecto: Proyecto) -> Material:
    """
    costo = (costo_origen * cotizacion + costo_flete + otros) * (1 + perc_perdida)
    costo_flete: si está dado directamente se usa tal cual;
                 si es 0 y hay distancia se calcula con tarifa default.
    """
    cotiz = proyecto.cotizaciones.get(mat.moneda, 1.0) if mat.moneda != "$AR" else 1.0

    flete = mat.costo_flete
    if flete == 0 and mat.distancia_km > 0:
        flete = mat.distancia_km * TARIFA_FLETE_DEFAULT

    # costo_origen and costo_flete are in mat.moneda → both multiplied by cotiz
    neto = (mat.costo_origen + flete) * cotiz + mat.otros
    costo = neto * (1 + mat.perc_perdida)

    return mat.model_copy(update={"costo": round(costo, 4)})


def calc_costo_combustible(c: Combustible) -> Combustible:
    costo = c.costo_origen + c.otros
    return c.model_copy(update={"costo": round(costo, 4)})


def calc_costo_subcontrato(sub: Subcontrato, proyecto: Proyecto) -> Subcontrato:
    cotiz = proyecto.cotizaciones.get(sub.moneda, 1.0) if sub.moneda != "$AR" else 1.0
    costo = sub.costo_or * cotiz + sub.otros
    return sub.model_copy(update={"costo": round(costo, 4)})
