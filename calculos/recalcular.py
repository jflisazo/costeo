"""
Recálculo en cascada cuando cambian parámetros globales (cotización, precio gasoil).

Orden:
  1. Combustibles  (solo costo_origen + otros → costo)
  2. Equipos       (KEOPS escala con cotiz; DNV recalcula; combustible con nuevo gasoil)
  3. Materiales    (precio_origen * cotiz + flete + pérdidas)
  4. Subcontratos  (costo_or * cotiz + otros)
  5. Auxiliares    (sus recursos internos → costo)
  6. Transportes   (costo_hora equipo / rend_dia)
  7. Datos CD      (cuantia_por_unidad * costo_recurso)
  8. Ítems         (sum CU * cantidad)
  9. GG            (costo_unitario ya viene de MO mensualizada; solo total = CU*cant*meses*amort)
"""

from models import Proyecto, Item
from models.recursos import Equipo, Material, Combustible, Subcontrato, Auxiliar, CicloTransporte
from models.items import DatoCD, GastoGeneral

from calculos.equipos import calc_costo_equipo
from calculos.mano_obra import calc_costo_jornal, calc_costo_mensual
from calculos.materiales import calc_costo_material, calc_costo_combustible, calc_costo_subcontrato
from calculos.transporte import calc_ciclo_transporte
from calculos.costos_directos import recalcular_datos_cd, calc_cu_item, lookup_costo_recurso, _cuantia_por_unidad


def _precio_gasoil(combustibles: list) -> float:
    for c in combustibles:
        if "gas oil" in c.descripcion.lower():
            return c.costo
    return 0.0


def _migrar_aux_recursos(datos_cd: list, auxiliares: list) -> list:
    """Mueve filas de Auxiliar.recursos (legacy) a datos_cd con item_aux='Aux'.
    Se ejecuta una sola vez por auxiliar: si ya hay filas datos_cd Aux para ese
    auxiliar, se asume que ya migró y se ignoran las recursos legacy."""
    nuevas = list(datos_cd)
    for aux in auxiliares:
        if not aux.recursos:
            continue
        ya_migrado = any(
            d.item_aux == "Aux" and d.item_id == aux.descripcion
            for d in nuevas
        )
        if ya_migrado:
            continue
        for r in aux.recursos:
            nuevas.append(DatoCD(
                item_aux="Aux",
                item_id=aux.descripcion,
                tarea=r.tarea,
                tarea_unidad=r.tarea_unidad,
                incidencia=r.incidencia,
                rendimiento=r.rendimiento,
                tipo_recurso=r.tipo_recurso,
                recurso=r.recurso,
                cuantia=r.cuantia,
                comentario=r.comentario,
                cuantia_por_unidad=r.cuantia_por_unidad,
                costo_unitario=r.costo_unitario,
            ))
    return nuevas


def recalcular_todo(
    proyecto: Proyecto,
    equipos: list,
    mo_jorn: list,
    mo_mens: list,
    materiales: list,
    combustibles: list,
    subcontratos: list,
    auxiliares: list,
    transportes: list,
    datos_cd: list,
    items: list,
    gastos_generales: list,
) -> dict:
    """
    Recalcula todo en cascada.
    Retorna dict con las listas actualizadas.
    """
    # 1. Combustibles
    combustibles = [calc_costo_combustible(c) for c in combustibles]
    gasoil = _precio_gasoil(combustibles)

    # 2. MO: los costos no dependen de cotizaciones; se preservan los valores almacenados.
    # Si costo_hora/costo_mes es 0 (nueva fila), calculamos desde los parámetros.
    mo_jorn = [calc_costo_jornal(m) if m.costo_hora == 0 else m for m in mo_jorn]
    mo_mens = [calc_costo_mensual(m) if m.costo_mes == 0 else m for m in mo_mens]

    # 3. Equipos
    equipos = [calc_costo_equipo(e, proyecto, gasoil) for e in equipos]

    # 4. Materiales
    materiales = [calc_costo_material(m, proyecto) for m in materiales]

    # 5. Subcontratos
    subcontratos = [calc_costo_subcontrato(s, proyecto) for s in subcontratos]

    # 6. Auxiliares — migrar aux.recursos legacy a datos_cd (item_aux="Aux"),
    #    luego recalcular y agregar el costo de cada auxiliar.
    datos_cd = _migrar_aux_recursos(datos_cd, auxiliares)

    nuevos_aux = []
    for aux in auxiliares:
        # Filas datos_cd Aux de este auxiliar (procesadas con los auxs ya recalculados)
        filas_aux = [d for d in datos_cd
                     if d.item_aux == "Aux" and d.item_id == aux.descripcion]
        filas_recalc = recalcular_datos_cd(
            filas_aux, equipos, mo_jorn, mo_mens,
            materiales, combustibles, subcontratos,
            nuevos_aux,  # solo auxs ya recalculados (sin anidamiento hacia adelante)
            transportes,
        )
        # Reemplazar en datos_cd
        otros = [d for d in datos_cd
                 if not (d.item_aux == "Aux" and d.item_id == aux.descripcion)]
        datos_cd = otros + filas_recalc
        costo_aux = round(sum(r.costo_unitario for r in filas_recalc), 4)
        nuevos_aux.append(aux.model_copy(update={
            "recursos": [],          # legacy: vaciar, datos_cd es la fuente
            "costo": costo_aux,
        }))
    auxiliares = nuevos_aux

    # 7. Transportes
    transportes_nuevos = []
    for t in transportes:
        costo_hora_eq = next(
            (e.costo_hora for e in equipos if e.nombre == t.equipo), 0.0
        )
        transportes_nuevos.append(calc_ciclo_transporte(t, costo_hora_eq))
    transportes = transportes_nuevos

    # 8. Datos CD — recalcular filas de ítems (las Aux ya están actualizadas).
    filas_item = [d for d in datos_cd if d.item_aux == "Item"]
    filas_item = recalcular_datos_cd(
        filas_item, equipos, mo_jorn, mo_mens,
        materiales, combustibles, subcontratos, auxiliares, transportes,
    )
    filas_aux_final = [d for d in datos_cd if d.item_aux == "Aux"]
    datos_cd = filas_aux_final + filas_item

    # 9. Ítems
    items_nuevos = []
    for item in items:
        if item.tipo == "Item":
            cu = calc_cu_item(item.numero, datos_cd, item_uid=item.uid)
            ct = round(cu * item.cantidad, 2)
            pu = round(cu * (1 + item.margen), 4)
            pt = round(pu * item.cantidad, 2)
            items_nuevos.append(item.model_copy(update={
                "costo_unitario": round(cu, 4),
                "costo_total": ct,
                "precio_unitario": pu,
                "precio_total": pt,
            }))
        else:
            items_nuevos.append(item)
    items = items_nuevos

    # 10. GG: actualizar costo_unitario desde MO mensualizada y recalcular total
    gg_nuevos = []
    for g in gastos_generales:
        if g.tipo == "Item":
            cu = g.costo_unitario
            # Si recurso coincide con MO mensualizada, actualizar CU
            for m in mo_mens:
                if m.funcion == g.recurso:
                    cu = m.costo_mes
                    break
            # Aplicar cotización para GG en moneda extranjera
            cotiz_gg = proyecto.cotizaciones.get(g.moneda, 1.0) if g.moneda != "$AR" else 1.0
            total = round(cu * cotiz_gg * g.cantidad * g.meses * g.amort_perc, 2)
            gg_nuevos.append(g.model_copy(update={"costo_unitario": round(cu, 4), "total": total}))
        else:
            gg_nuevos.append(g)
    gastos_generales = gg_nuevos

    return {
        "equipos": equipos,
        "mo_jornalizada": mo_jorn,
        "mo_mensualizada": mo_mens,
        "materiales": materiales,
        "combustibles": combustibles,
        "subcontratos": subcontratos,
        "auxiliares": auxiliares,
        "transportes": transportes,
        "datos_cd": datos_cd,
        "items": items,
        "gastos_generales": gastos_generales,
    }
