"""
Motor de cálculo de costos directos.

Replica las fórmulas de las hojas "Datos CD" y "Datos Aux" del Excel fuente:

  Costo (resource cost)
    Equipos        : CU_AI + (CU_RR*(1+%EsfRR) + CU_Comb*(1+%EsfGO))*(1-%HsParo)
    Mano de Obra   : costo_hora (jornalizada) o costo_mes (mensualizada)
    Materiales     : costo
    Combustibles   : costo
    Subcontratos   : costo
    Auxiliares     : costo del auxiliar
    Tpte Interno   : costo del ciclo

  C Unit Tarea (cu_tarea)
    Equipos        : Cuantía * Costo / Rendimiento
    Mano de Obra   : Cuantía * Costo / Rendimiento / Efi_MO * (1 + Incr_MO)
    Resto          : Cuantía * Costo

  Costo Unit (costo_unitario)
    cu_tarea * incidencia

  Unidad (lookup según Tipo)
"""

import uuid
from collections import defaultdict
from typing import List, Dict, Tuple
from models.items import DatoCD, Item
from models.proyecto import Proyecto


def lookup_recurso_info(
    tipo: str,
    nombre: str,
    equipos: list,
    mo_jorn: list,
    mo_mens: list,
    materiales: list,
    combustibles: list,
    subcontratos: list,
    auxiliares: list,
    transportes: list,
) -> Tuple[str, float, dict]:
    """Devuelve (unidad, costo_base, extras) del recurso.

    Para Equipos, `costo_base` queda en 0.0 y `extras` contiene
    {'cu_ai', 'cu_rr', 'cu_comb'} para que el caller aplique los porcentajes.
    Para el resto, `costo_base` ya es el valor utilizable y extras={}.
    """
    tipo_lower = (tipo or "").lower()

    if "equipo" in tipo_lower:
        for e in equipos:
            if e.nombre == nombre:
                return ("hs", 0.0, {
                    "cu_ai": e.cu_ai, "cu_rr": e.cu_rr, "cu_comb": e.cu_comb,
                })

    elif "mano" in tipo_lower or tipo_lower == "mo":
        for m in mo_jorn:
            if m.funcion == nombre:
                return ("hs", m.costo_hora, {})
        for m in mo_mens:
            if m.funcion == nombre:
                return ("mes", m.costo_mes, {})

    elif "material" in tipo_lower:
        for m in materiales:
            if m.descripcion == nombre:
                return (m.unidad or "", m.costo, {})

    elif "combustible" in tipo_lower:
        for c in combustibles:
            if c.descripcion == nombre:
                return (c.unidad or "lts", c.costo, {})

    elif "subcontrat" in tipo_lower:
        for s in subcontratos:
            if s.descripcion == nombre:
                return (s.unidad or "", s.costo, {})

    elif "auxiliar" in tipo_lower or "elaborado" in tipo_lower:
        for a in auxiliares:
            if a.descripcion == nombre:
                return (a.unidad or "", a.costo, {})

    elif "tpte" in tipo_lower or "transport" in tipo_lower:
        for t in transportes:
            if t.descripcion == nombre:
                return (t.unidad or "", t.costo, {})

    return ("", 0.0, {})


def lookup_costo_recurso(
    tipo: str,
    nombre: str,
    equipos: list,
    mo_jorn: list,
    mo_mens: list,
    materiales: list,
    combustibles: list,
    subcontratos: list,
    auxiliares: list,
    transportes: list,
) -> float:
    """Compat: retorna sólo el costo base del recurso (sin ajustes de equipos)."""
    _, costo, extras = lookup_recurso_info(
        tipo, nombre, equipos, mo_jorn, mo_mens,
        materiales, combustibles, subcontratos, auxiliares, transportes,
    )
    if extras:  # Equipos: sumar componentes sin ajustes
        return extras.get("cu_ai", 0.0) + extras.get("cu_rr", 0.0) + extras.get("cu_comb", 0.0)
    return costo


def _aplicar_ajustes_equipo(extras: dict, hs_paro: float, esf_rr: float, esf_go: float) -> float:
    """Excel: CU_AI + (CU_RR*(1+%EsfRR) + CU_Comb*(1+%EsfGO))*(1-%HsParo)."""
    cu_ai = extras.get("cu_ai", 0.0)
    cu_rr = extras.get("cu_rr", 0.0)
    cu_comb = extras.get("cu_comb", 0.0)
    return cu_ai + (cu_rr * (1.0 + esf_rr) + cu_comb * (1.0 + esf_go)) * (1.0 - hs_paro)


def _cu_tarea(cuantia: float, costo: float, rendimiento: float,
              tipo_recurso: str, efi_mo: float, incr_mo: float) -> float:
    """Excel:
      Equipos      : cuantia * costo / rendimiento
      Mano de Obra : cuantia * costo / rendimiento / Efi_MO * (1 + Incr_MO)
      Resto        : cuantia * costo
    """
    t = (tipo_recurso or "").lower()
    rend = rendimiento if rendimiento != 0 else 1.0
    if "equipo" in t:
        return cuantia * costo / rend
    if "mano" in t or t == "mo":
        efi = efi_mo if efi_mo != 0 else 1.0
        return cuantia * costo / rend / efi * (1.0 + incr_mo)
    return cuantia * costo


def recalcular_datos_cd(
    datos: List[DatoCD],
    equipos: list,
    mo_jorn: list,
    mo_mens: list,
    materiales: list,
    combustibles: list,
    subcontratos: list,
    auxiliares: list,
    transportes: list,
    proyecto: Proyecto | None = None,
) -> List[DatoCD]:
    """Recalcula cada fila DatoCD aplicando todas las fórmulas del Excel.

    Si el recurso no se encuentra y la fila ya tenía un costo_unitario almacenado,
    preserva ese valor para no perder datos importados desde Excel.
    """
    efi_mo = proyecto.efi_mo if proyecto else 1.0
    incr_mo = proyecto.incr_mo if proyecto else 0.0

    resultado = []
    for d in datos:
        unidad, costo_base, extras = lookup_recurso_info(
            d.tipo_recurso, d.recurso,
            equipos, mo_jorn, mo_mens,
            materiales, combustibles, subcontratos,
            auxiliares, transportes,
        )

        if extras:  # Equipos
            costo_recurso = _aplicar_ajustes_equipo(
                extras, d.perc_hs_paro, d.perc_esf_rr, d.perc_esf_go,
            )
        else:
            costo_recurso = costo_base

        # Si el recurso no fue encontrado pero hay CU almacenado, preservamos.
        if costo_recurso == 0.0 and not extras and d.costo_unitario != 0.0:
            resultado.append(d)
            continue

        cu_tarea = _cu_tarea(
            d.cuantia, costo_recurso, d.rendimiento,
            d.tipo_recurso, efi_mo, incr_mo,
        )
        costo_unitario = cu_tarea * d.incidencia

        # cuantia_por_unidad se mantiene para compatibilidad (= cuantia/rend * incid para Eq/MO)
        t = (d.tipo_recurso or "").lower()
        rend = d.rendimiento if d.rendimiento != 0 else 1.0
        if "equipo" in t or "mano" in t or t == "mo":
            qpu = (d.cuantia / rend) * d.incidencia
        else:
            qpu = d.cuantia * d.incidencia

        resultado.append(d.model_copy(update={
            "unidad_recurso": unidad,
            "costo_recurso": round(costo_recurso, 4),
            "cu_tarea": round(cu_tarea, 4),
            "cuantia_por_unidad": round(qpu, 6),
            "costo_unitario": round(costo_unitario, 4),
        }))
    return resultado


def asignar_uids_items(items: List[Item], datos_cd: List[DatoCD]) -> Tuple[List[Item], List[DatoCD]]:
    """
    Asigna UIDs únicos a Items y los propaga a DatoCD.
    Resuelve el problema de ítems con número duplicado distribuyendo las filas
    de DatoCD en orden hasta que la suma de CU coincida con el CU almacenado.
    """
    id_count: Dict[str, int] = defaultdict(int)
    for item in items:
        if item.tipo == "Item":
            id_count[item.numero] += 1

    cd_by_id: Dict[str, List[Tuple[int, DatoCD]]] = defaultdict(list)
    for i, d in enumerate(datos_cd):
        if d.item_aux == "Item":
            cd_by_id[d.item_id].append((i, d))

    id_cursor: Dict[str, int] = defaultdict(int)
    id_seen: Dict[str, int] = defaultdict(int)
    datocd_uid_map: Dict[int, str] = {}

    items_out: List[Item] = []
    for item in items:
        item_uid = item.uid or str(uuid.uuid4())
        items_out.append(item.model_copy(update={"uid": item_uid}))

        if item.tipo != "Item":
            continue

        item_id = item.numero
        group = cd_by_id[item_id]
        start = id_cursor[item_id]
        total_with_id = id_count[item_id]
        id_seen[item_id] += 1
        seen = id_seen[item_id]

        if start >= len(group):
            continue

        if total_with_id == 1 or seen == total_with_id:
            for orig_idx, _ in group[start:]:
                datocd_uid_map[orig_idx] = item_uid
            id_cursor[item_id] = len(group)
        else:
            target = item.costo_unitario
            running = 0.0
            end = start
            for j in range(start, len(group)):
                orig_idx, d = group[j]
                running += d.costo_unitario
                end = j + 1
                if target > 0 and abs(running / target - 1.0) < 0.001:
                    break
                if target == 0 and running == 0:
                    break
            for orig_idx, _ in group[start:end]:
                datocd_uid_map[orig_idx] = item_uid
            id_cursor[item_id] = end

    datos_cd_out: List[DatoCD] = []
    for i, d in enumerate(datos_cd):
        if d.item_aux == "Item":
            uid = datocd_uid_map.get(i, "")
            datos_cd_out.append(d.model_copy(update={"item_uid": uid}))
        else:
            datos_cd_out.append(d)

    return items_out, datos_cd_out


def calc_cu_item(item_id: str, datos: List[DatoCD], item_uid: str = "") -> float:
    """Suma los costo_unitario de todas las filas del ítem."""
    if item_uid:
        return sum(d.costo_unitario for d in datos
                   if d.item_aux == "Item" and d.item_uid == item_uid)
    return sum(d.costo_unitario for d in datos
               if d.item_aux == "Item" and d.item_id == item_id)


