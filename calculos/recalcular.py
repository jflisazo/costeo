"""
Recálculo en cascada cuando cambian parámetros globales (cotización, precio gasoil,
factores Efi_MO/Incr_MO, %HsParo/%EsfRR/%EsfGO).

Orden:
  1. Combustibles  (solo costo_origen + otros → costo)
  2. MO            (jornalizada/mensualizada → costo_hora / costo_mes)
  3. Equipos       (KEOPS escala con cotiz; DNV recalcula; combustible con nuevo gasoil)
  4. Materiales    (precio_origen * cotiz + flete + pérdidas)
  5. Subcontratos  (costo_or * cotiz + otros)
  6. Auxiliares    (sus recursos internos → costo)
  7. Transportes   (costo_hora equipo / rend_dia)
  8. Datos CD      (cuantia*costo*ajustes → costo_unitario)
  9. Ítems         (sum CU, costo_total, precio*coef_oferta)
 10. GG            (cantidad*meses*amort*costo*cotiz)
 11. Gantt         (ctrl = sum mes_1..60)
"""

from models import Proyecto, Item, GanttFila
from models.items import DatoCD

from calculos.equipos import calc_costo_equipo
from calculos.mano_obra import calc_costo_jornal, calc_costo_mensual
from calculos.materiales import calc_costo_material, calc_costo_combustible, calc_costo_subcontrato
from calculos.transporte import calc_ciclo_transporte
from calculos.costos_directos import recalcular_datos_cd, calc_cu_item


def _precio_gasoil(combustibles: list) -> float:
    for c in combustibles:
        if "gas oil" in c.descripcion.lower():
            return c.costo
    return 0.0


def _migrar_aux_recursos(datos_cd: list, auxiliares: list) -> list:
    """Mueve filas de Auxiliar.recursos (legacy) a datos_cd con item_aux='Aux'."""
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


def recalcular_gantt(gantt: list[GanttFila], items: list[Item]) -> list[GanttFila]:
    """Sincroniza descripción/unidad/cantidad desde Items y recalcula ctrl.

    Si gantt está vacío, lo genera a partir de items (todos en 0).
    Si items tiene filas nuevas, las añade. Si items eliminó filas,
    elimina las correspondientes filas de gantt (match por uid o numero).
    """
    items_by_uid = {it.uid: it for it in items if it.uid}
    items_by_num = {it.numero: it for it in items}

    # Si está vacío, generar a partir de items
    if not gantt:
        out = []
        for it in items:
            out.append(GanttFila(
                tipo=it.tipo,
                numero=it.numero,
                item_uid=it.uid,
                descripcion=it.descripcion,
                unidad=it.unidad,
                cantidad=it.cantidad,
                meses=[0.0] * 60,
                ctrl=0.0,
            ))
        return out

    # Sincronizar filas existentes y agregar nuevas
    seen_uids = set()
    seen_nums = set()
    out: list[GanttFila] = []
    for g in gantt:
        it = items_by_uid.get(g.item_uid) if g.item_uid else items_by_num.get(g.numero)
        if it is None:
            continue  # el ítem ya no existe; descartar la fila
        meses = list(g.meses) if g.meses else [0.0] * 60
        if len(meses) < 60:
            meses = meses + [0.0] * (60 - len(meses))
        elif len(meses) > 60:
            meses = meses[:60]
        ctrl = round(sum(meses), 6)
        out.append(g.model_copy(update={
            "tipo": it.tipo,
            "numero": it.numero,
            "item_uid": it.uid,
            "descripcion": it.descripcion,
            "unidad": it.unidad,
            "cantidad": it.cantidad,
            "meses": meses,
            "ctrl": ctrl,
        }))
        if it.uid:
            seen_uids.add(it.uid)
        seen_nums.add(it.numero)

    # Agregar ítems nuevos
    for it in items:
        if (it.uid and it.uid in seen_uids) or (not it.uid and it.numero in seen_nums):
            continue
        out.append(GanttFila(
            tipo=it.tipo, numero=it.numero, item_uid=it.uid,
            descripcion=it.descripcion, unidad=it.unidad, cantidad=it.cantidad,
            meses=[0.0] * 60, ctrl=0.0,
        ))
    return out


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
    gantt: list | None = None,
) -> dict:
    """Recalcula todo en cascada. Retorna dict con las listas actualizadas."""

    # 1. Combustibles
    combustibles = [calc_costo_combustible(c) for c in combustibles]
    gasoil = _precio_gasoil(combustibles)

    # 2. MO: si costo_hora/costo_mes es 0 (nueva fila), calcular desde parámetros
    mo_jorn = [calc_costo_jornal(m) if m.costo_hora == 0 else m for m in mo_jorn]
    mo_mens = [calc_costo_mensual(m) if m.costo_mes == 0 else m for m in mo_mens]

    # 3. Equipos
    equipos = [calc_costo_equipo(e, proyecto, gasoil) for e in equipos]

    # 4. Materiales
    materiales = [calc_costo_material(m, proyecto) for m in materiales]

    # 5. Subcontratos
    subcontratos = [calc_costo_subcontrato(s, proyecto) for s in subcontratos]

    # 6. Auxiliares
    datos_cd = _migrar_aux_recursos(datos_cd, auxiliares)
    nuevos_aux = []
    for aux in auxiliares:
        filas_aux = [d for d in datos_cd
                     if d.item_aux == "Aux" and d.item_id == aux.descripcion]
        filas_recalc = recalcular_datos_cd(
            filas_aux, equipos, mo_jorn, mo_mens,
            materiales, combustibles, subcontratos,
            nuevos_aux, transportes, proyecto,
        )
        otros = [d for d in datos_cd
                 if not (d.item_aux == "Aux" and d.item_id == aux.descripcion)]
        datos_cd = otros + filas_recalc
        costo_aux = round(sum(r.costo_unitario for r in filas_recalc), 4)
        nuevos_aux.append(aux.model_copy(update={
            "recursos": [],
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

    # 8. Datos CD — filas de ítems
    filas_item = [d for d in datos_cd if d.item_aux == "Item"]
    filas_item = recalcular_datos_cd(
        filas_item, equipos, mo_jorn, mo_mens,
        materiales, combustibles, subcontratos, auxiliares, transportes,
        proyecto,
    )
    filas_aux_final = [d for d in datos_cd if d.item_aux == "Aux"]
    datos_cd = filas_aux_final + filas_item

    # 9. Ítems
    items_nuevos = []
    for item in items:
        if item.tipo == "Item":
            cu = calc_cu_item(item.numero, datos_cd, item_uid=item.uid)
            ct = round(cu * item.cantidad, 2)
            # Precio = CU * coef_oferta (Excel: Resumen!G57). Si margen propio del
            # ítem != 0, se prefiere ese (caso editado manualmente).
            if item.margen and item.margen > 0:
                pu = round(cu * (1 + item.margen), 4)
            else:
                pu = round(cu * proyecto.coef_oferta, 4)
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

    # 10. GG
    gg_nuevos = []
    for g in gastos_generales:
        if g.tipo == "Item":
            cu = g.costo_unitario
            for m in mo_mens:
                if m.funcion == g.recurso:
                    cu = m.costo_mes
                    break
            cotiz_gg = proyecto.cotizaciones.get(g.moneda, 1.0) if g.moneda != "$AR" else 1.0
            total = round(cu * cotiz_gg * g.cantidad * g.meses * g.amort_perc, 2)
            gg_nuevos.append(g.model_copy(update={"costo_unitario": round(cu, 4), "total": total}))
        else:
            gg_nuevos.append(g)
    gastos_generales = gg_nuevos

    # 11. Gantt
    gantt = recalcular_gantt(gantt or [], items)

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
        "gantt": gantt,
    }
