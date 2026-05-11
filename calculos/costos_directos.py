"""
Motor de cálculo de costos directos.

lookup_costo_recurso: dado tipo + nombre devuelve el costo unitario del recurso.
recalcular_datos_cd:  actualiza cuantia_por_unidad y costo_unitario de cada DatoCD.
calc_cu_item:         suma los costos de todas las filas de un ítem.
asignar_uids_items:   asigna UIDs únicos a Items y los propaga a DatoCD.
"""

import uuid
from collections import defaultdict
from typing import List, Dict, Any, Tuple
from models.items import DatoCD, Item


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
    """Retorna el costo unitario del recurso dado su tipo y nombre."""
    tipo_lower = tipo.lower()

    if "equipo" in tipo_lower:
        for e in equipos:
            if e.nombre == nombre:
                return e.costo_hora

    elif "mano" in tipo_lower or "mo" in tipo_lower:
        for m in mo_jorn:
            if m.funcion == nombre:
                return m.costo_hora
        for m in mo_mens:
            if m.funcion == nombre:
                return m.costo_mes

    elif "material" in tipo_lower:
        for m in materiales:
            if m.descripcion == nombre:
                return m.costo

    elif "combustible" in tipo_lower:
        for c in combustibles:
            if c.descripcion == nombre:
                return c.costo

    elif "subcontrat" in tipo_lower:
        for s in subcontratos:
            if s.descripcion == nombre:
                return s.costo

    elif "auxiliar" in tipo_lower or "elaborado" in tipo_lower:
        for a in auxiliares:
            if a.descripcion == nombre:
                return a.costo

    elif "tpte" in tipo_lower or "transport" in tipo_lower:
        for t in transportes:
            if t.descripcion == nombre:
                return t.costo

    return 0.0


def _cuantia_por_unidad(cuantia: float, rendimiento: float, incidencia: float, tipo_recurso: str) -> float:
    """
    Equipos y MO: cuantia es cantidad/día, rendimiento es producción/día del frente.
        q_u = (cuantia / rendimiento) * incidencia
    Materiales, Combustibles, Subcontratos, Auxiliares, Transporte:
        cuantia ya está expresada por unidad de ítem (no por día).
        q_u = cuantia * incidencia
    """
    t = tipo_recurso.lower()
    if "equipo" in t or "mano" in t:
        rend = rendimiento if rendimiento != 0 else 1.0
        return (cuantia / rend) * incidencia
    return cuantia * incidencia


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
) -> List[DatoCD]:
    """Recalcula cuantia_por_unidad y costo_unitario de cada fila.
    Si el recurso no se encuentra en el sistema (costo_recurso=0 pero CU almacenado!=0),
    preserva el CU almacenado para no perder datos importados desde Excel."""
    resultado = []
    for d in datos:
        cuantia_por_unidad = _cuantia_por_unidad(d.cuantia, d.rendimiento, d.incidencia, d.tipo_recurso)

        costo_recurso = lookup_costo_recurso(
            d.tipo_recurso, d.recurso,
            equipos, mo_jorn, mo_mens,
            materiales, combustibles, subcontratos,
            auxiliares, transportes,
        )

        if costo_recurso == 0.0 and d.costo_unitario != 0.0:
            # Recurso no encontrado pero hay CU almacenado: preservar
            resultado.append(d)
        else:
            costo_unitario = cuantia_por_unidad * costo_recurso
            resultado.append(d.model_copy(update={
                "cuantia_por_unidad": round(cuantia_por_unidad, 6),
                "costo_unitario": round(costo_unitario, 4),
            }))
    return resultado


def asignar_uids_items(items: List[Item], datos_cd: List[DatoCD]) -> Tuple[List[Item], List[DatoCD]]:
    """
    Asigna UIDs únicos a Items y los propaga a DatoCD.
    Resuelve el problema de ítems con número duplicado distribuyendo las filas
    de DatoCD en orden hasta que la suma de CU coincida con el CU almacenado.
    """
    # Contar cuántos Items comparten cada número
    id_count: Dict[str, int] = defaultdict(int)
    for item in items:
        if item.tipo == "Item":
            id_count[item.numero] += 1

    # Agrupar DatoCD por item_id preservando orden
    cd_by_id: Dict[str, List[Tuple[int, DatoCD]]] = defaultdict(list)
    for i, d in enumerate(datos_cd):
        cd_by_id[d.item_id].append((i, d))

    # Cursor de posición por cada item_id
    id_cursor: Dict[str, int] = defaultdict(int)
    id_seen: Dict[str, int] = defaultdict(int)

    # Mapeo: índice original de DatoCD → item_uid
    datocd_uid_map: Dict[int, str] = {}

    items_out: List[Item] = []
    for item in items:
        item_uid = str(uuid.uuid4())
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
            # Único o último: toma todas las filas restantes
            for orig_idx, _ in group[start:]:
                datocd_uid_map[orig_idx] = item_uid
            id_cursor[item_id] = len(group)
        else:
            # Hay múltiples items con el mismo número: consume filas hasta que
            # la suma de CU coincida con el CU almacenado del item (tolerancia 0.1%)
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

    # Asignar item_uid a DatoCD
    datos_cd_out: List[DatoCD] = []
    for i, d in enumerate(datos_cd):
        uid = datocd_uid_map.get(i, "")
        datos_cd_out.append(d.model_copy(update={"item_uid": uid}))

    return items_out, datos_cd_out


def calc_cu_item(item_id: str, datos: List[DatoCD], item_uid: str = "") -> float:
    """Suma los costo_unitario de todas las filas del ítem.
    Usa item_uid (único) si está disponible, si no cae back a item_id.
    Solo considera filas con item_aux='Item' (las 'Aux' alimentan auxiliares)."""
    if item_uid:
        return sum(d.costo_unitario for d in datos
                   if d.item_aux == "Item" and d.item_uid == item_uid)
    return sum(d.costo_unitario for d in datos
               if d.item_aux == "Item" and d.item_id == item_id)
