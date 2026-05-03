from models.recursos import MOJornalizada, MOMensualizada


# Porcentaje IVA social (cargas patronales ~50%)
K_CARGAS_DEFAULT = 0.38


def calc_costo_jornal(mo: MOJornalizada) -> MOJornalizada:
    """
    Costo hora jornalizado:
        jornal = bruto / horas_mes
        aguinaldo = jornal / 12
        vacaciones = jornal * dias_vac / (365 - dias_vac)   (aprox: jornal * 14/351)
        cargas = (jornal + aguinaldo + vacaciones) * k_cargas
        costo_hora = jornal + aguinaldo + vacaciones + cargas + viatico/horas_mes
    Los valores de aguinaldo, vacaciones y cargas_sociales ya vienen calculados
    del Excel; si están en cero se calculan aquí.
    """
    horas = mo.horas_mes if mo.horas_mes > 0 else 200.0

    jornal = mo.bruto / horas
    agu = mo.aguinaldo / horas if mo.aguinaldo else jornal / 12
    vac = mo.vacaciones / horas if mo.vacaciones else jornal * 14 / 351
    cs = mo.cargas_sociales / horas if mo.cargas_sociales else (jornal + agu + vac) * K_CARGAS_DEFAULT
    viat = mo.viatico / horas if mo.viatico else 0.0

    costo_hora = jornal + agu + vac + cs + viat

    return mo.model_copy(update={"costo_hora": round(costo_hora, 4)})


def calc_costo_mensual(mo: MOMensualizada) -> MOMensualizada:
    """
    Costo mensual del personal mensualizado.
    bruto = neto / (1 - aporte_empleado)  — ya viene calculado del Excel
    costo_mes = bruto + aguinaldo + vacaciones + cargas_sociales + prop_despido
    """
    costo_mes = (
        mo.bruto
        + mo.aguinaldo
        + mo.vacaciones
        + mo.cargas_sociales
        + mo.prop_despido
    )
    return mo.model_copy(update={"costo_mes": round(costo_mes, 4)})
