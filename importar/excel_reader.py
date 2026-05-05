"""
Importador del archivo .xlsm de costeo.
Lee las hojas clave usando zipfile + xml (no depende de openpyxl para VBA)
y devuelve un dict compatible con state.dict_a_estado().
"""

import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from models import (
    Proyecto, Equipo, MOJornalizada, MOMensualizada,
    Material, Combustible, Subcontrato, Auxiliar, RecursoAux, CicloTransporte,
    Item, DatoCD, GastoGeneral,
)
from calculos import (
    calc_costo_equipo, calc_costo_jornal, calc_costo_mensual,
    calc_costo_material,
)
from calculos.materiales import calc_costo_combustible, calc_costo_subcontrato

NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"


# ── Utilidades XML ─────────────────────────────────────────────────────────────

def _shared_strings(z: zipfile.ZipFile) -> list[str]:
    xml = z.read("xl/sharedStrings.xml")
    root = ET.fromstring(xml)
    ns = {"ns": NS}
    result = []
    for si in root.findall("ns:si", ns):
        parts = [t.text or "" for t in si.findall(".//ns:t", ns)]
        result.append("".join(parts))
    return result


def _sheet_rels(z: zipfile.ZipFile) -> dict[str, str]:
    xml = z.read("xl/_rels/workbook.xml.rels")
    root = ET.fromstring(xml)
    return {rid: target for r in root
            if (rid := r.get("Id")) is not None
            and (target := r.get("Target")) is not None}


def _workbook_sheets(z: zipfile.ZipFile) -> dict[str, str]:
    """Retorna {nombre_hoja: rId}."""
    xml = z.read("xl/workbook.xml")
    root = ET.fromstring(xml)
    ns = {"ns": NS}
    result = {}
    for s in root.findall(".//ns:sheet", ns):
        name = s.get("name", "")
        rid = s.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id", "")
        result[name] = rid
    return result


def _read_sheet(z: zipfile.ZipFile, path: str, ss: list[str]) -> dict[int, dict[str, Any]]:
    """Lee una hoja y devuelve {row_num: {col_letter: value}}."""
    xml = z.read("xl/" + path)
    root = ET.fromstring(xml)
    ns = {"ns": NS}
    rows: dict[int, dict[str, Any]] = {}
    for row in root.findall(".//ns:row", ns):
        rn = int(row.get("r", 0))
        cells: dict[str, Any] = {}
        for cell in row.findall("ns:c", ns):
            ref = cell.get("r", "")
            col = "".join(c for c in ref if c.isalpha())
            t = cell.get("t", "")
            v = cell.find("ns:v", ns)
            if v is not None and v.text:
                if t == "s":
                    cells[col] = ss[int(v.text)]
                else:
                    txt = v.text
                    try:
                        cells[col] = float(txt)
                    except ValueError:
                        cells[col] = txt
            else:
                cells[col] = ""
        if cells:
            rows[rn] = cells
    return rows


def _get(row: dict, col: str, default: Any = "") -> Any:
    return row.get(col, default) or default


def _float(row: dict, col: str) -> float:
    v = row.get(col, 0) or 0
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _str(row: dict, col: str) -> str:
    return str(row.get(col, "") or "").strip()


# ── Lectura de cada hoja ───────────────────────────────────────────────────────

def _leer_proyecto(rows: dict) -> Proyecto:
    p = Proyecto()
    for rn, row in rows.items():
        a = _str(row, "A")
        b = row.get("B", "")
        if "Empresa" in a:
            p = p.model_copy(update={"empresa": str(b).replace("JOSÉ J. CHEDIACK S.A.I.C.A.", "JOSÉ J. CHEDIACK S.A.I.C.A.").strip()})
        elif "Obra" in a:
            p = p.model_copy(update={"obra": str(b).strip()})
        elif a == "Comitente":
            p = p.model_copy(update={"comitente": str(b).strip()})
        elif a == "Plazo en meses":
            try:
                p = p.model_copy(update={"plazo_meses": int(float(b))})
            except (TypeError, ValueError):
                pass
        elif a == "Moneda Oferta":
            p = p.model_copy(update={"moneda_oferta": str(b).strip()})
        elif a == "Plazo de pago":
            try:
                p = p.model_copy(update={"plazo_pago": int(float(b))})
            except (TypeError, ValueError):
                pass
        elif a == "USD":
            try:
                cotiz = dict(p.cotizaciones)
                cotiz["USD"] = float(b)
                p = p.model_copy(update={"cotizaciones": cotiz})
            except (TypeError, ValueError):
                pass
        elif a == "EUR":
            try:
                cotiz = dict(p.cotizaciones)
                cotiz["EUR"] = float(b)
                p = p.model_copy(update={"cotizaciones": cotiz})
            except (TypeError, ValueError):
                pass
    return p


def _leer_equipos(rows: dict, proyecto: Proyecto, precio_gasoil: float) -> list[Equipo]:
    equipos: list[Equipo] = []
    cotiz_usd = proyecto.cotizaciones.get("USD", 1.0)
    # Cabecera en fila 7; datos desde fila 8
    for rn in sorted(rows.keys()):
        if rn < 8:
            continue
        row = rows[rn]
        nombre = _str(row, "A")
        if not nombre or nombre.startswith("Empresa") or nombre.startswith("Obra"):
            continue
        moneda = _str(row, "E") or "USD"
        precio = _float(row, "F")
        if precio <= 0:
            continue

        cu_ai  = _float(row, "H")
        cu_rr  = _float(row, "I")
        cu_comb = _float(row, "J")

        # Calcular ratios para poder escalar cuando cambie la cotización
        cotiz = cotiz_usd if moneda != "$AR" else 1.0
        precio_ar = precio * cotiz
        ratio_ai = cu_ai / precio_ar if precio_ar > 0 else 0.0
        ratio_rr = cu_rr / precio_ar if precio_ar > 0 else 0.0

        eq = Equipo(
            nombre=nombre,
            marca=_str(row, "B"),
            modelo=_str(row, "C"),
            potencia=_float(row, "D"),
            moneda=moneda,
            precio=precio,
            k_combustible=_float(row, "G"),
            propiedad=_str(row, "L") or "Propio",
            metodo_costeo="KEOPS",
            ratio_ai=ratio_ai,
            ratio_rr=ratio_rr,
            cotiz_base=cotiz,
            cu_ai=cu_ai,
            cu_rr=cu_rr,
            cu_comb=cu_comb,
            costo_hora=_float(row, "K"),
        )
        equipos.append(eq)
    return equipos


def _leer_mo_jornalizada(rows: dict) -> list[MOJornalizada]:
    result: list[MOJornalizada] = []
    for rn in sorted(rows.keys()):
        if rn < 8:
            continue
        row = rows[rn]
        funcion = _str(row, "A")
        if not funcion or "Empresa" in funcion or "Obra" in funcion or "Mano" in funcion or "Función" in funcion:
            continue
        bruto = _float(row, "E")
        if bruto <= 0:
            continue
        mo = MOJornalizada(
            funcion=funcion,
            id=int(_float(row, "D")),
            moneda=_str(row, "C") or "$AR",
            bruto=bruto,
            aguinaldo=_float(row, "F"),
            vacaciones=_float(row, "G"),
            cargas_sociales=_float(row, "H"),
            bolsillo=_float(row, "I"),
            viatico=_float(row, "J"),
            costo_hora=_float(row, "K"),
        )
        result.append(mo)
    return result


def _leer_mo_mensualizada(rows: dict) -> list[MOMensualizada]:
    result: list[MOMensualizada] = []
    for rn in sorted(rows.keys()):
        if rn < 8:
            continue
        row = rows[rn]
        funcion = _str(row, "M")
        if not funcion:
            continue
        bruto = _float(row, "Q")
        if bruto <= 0:
            continue
        mo = MOMensualizada(
            funcion=funcion,
            moneda=_str(row, "O") or "$AR",
            neto=_float(row, "P"),
            bruto=bruto,
            aguinaldo=_float(row, "R"),
            dias_vacaciones=int(_float(row, "S") or 14),
            vacaciones=_float(row, "T"),
            cargas_sociales=_float(row, "U"),
            prop_despido=_float(row, "V"),
            costo_mes=_float(row, "W"),
        )
        result.append(mo)
    return result


def _leer_materiales(rows: dict, proyecto: Proyecto) -> list[Material]:
    result: list[Material] = []
    for rn in sorted(rows.keys()):
        if rn < 8:
            continue
        row = rows[rn]
        desc = _str(row, "B")
        if not desc:
            continue
        m = Material(
            numero=int(_float(row, "A") or rn - 7),
            descripcion=desc,
            unidad=_str(row, "C"),
            moneda=_str(row, "D") or "$AR",
            proveedor=_str(row, "E"),
            origen=_str(row, "F"),
            distancia_km=_float(row, "G"),
            costo_origen=_float(row, "H"),
            costo_flete=_float(row, "I"),
            otros=_float(row, "J"),
            perc_perdida=_float(row, "K"),
            costo=_float(row, "L"),
        )
        result.append(m)
    return result


def _leer_combustibles(rows: dict) -> list[Combustible]:
    result: list[Combustible] = []
    for rn in sorted(rows.keys()):
        if rn < 8:
            continue
        row = rows[rn]
        desc = _str(row, "B")
        if not desc:
            continue
        result.append(Combustible(
            descripcion=desc,
            unidad=_str(row, "C") or "lts",
            moneda=_str(row, "D") or "$AR",
            proveedor=_str(row, "E"),
            costo_origen=_float(row, "H"),
            costo=_float(row, "L"),
        ))
    return result


def _leer_subcontratos(rows: dict, proyecto: Proyecto) -> list[Subcontrato]:
    result: list[Subcontrato] = []
    for rn in sorted(rows.keys()):
        if rn < 8:
            continue
        row = rows[rn]
        desc = _str(row, "B")
        if not desc:
            continue
        result.append(Subcontrato(
            numero=int(_float(row, "A") or rn - 7),
            descripcion=desc,
            unidad=_str(row, "C"),
            moneda=_str(row, "D") or "$AR",
            proveedor=_str(row, "E"),
            costo_or=_float(row, "F"),
            otros=_float(row, "G"),
            costo=_float(row, "H"),
        ))
    return result


def _leer_items(rows: dict) -> list[Item]:
    result: list[Item] = []
    for rn in sorted(rows.keys()):
        if rn < 8:
            continue
        row = rows[rn]
        tipo = _str(row, "A")
        numero = _str(row, "B")
        if not numero or tipo not in ("Título", "Item"):
            continue
        result.append(Item(
            tipo=tipo,
            numero=numero,
            descripcion=_str(row, "C"),
            unidad=_str(row, "D"),
            cantidad=_float(row, "E"),
            costo_unitario=_float(row, "G"),
            costo_total=_float(row, "H"),
            precio_unitario=_float(row, "I"),
            precio_total=_float(row, "J"),
            grupo=_str(row, "K"),
            sub_grupo=_str(row, "L"),
        ))
    return result


def _leer_datos_cd(rows: dict) -> list[DatoCD]:
    result: list[DatoCD] = []
    # Fila 3 es header; datos desde fila 4
    for rn in sorted(rows.keys()):
        if rn < 4:
            continue
        row = rows[rn]
        tipo_fila = _str(row, "A")
        if tipo_fila != "Item":
            continue
        item_desc = _str(row, "B")
        if not item_desc:
            continue
        # El número de ítem es la primera parte del campo B (hasta el primer espacio)
        item_id = item_desc.split(" ")[0] if item_desc else ""
        tipo_recurso = _str(row, "I")
        recurso = _str(row, "J")
        if not recurso:
            continue
        result.append(DatoCD(
            item_id=item_id,
            tarea=_str(row, "E"),
            tarea_unidad=_str(row, "F"),
            incidencia=_float(row, "G") or 1.0,
            rendimiento=_float(row, "H") or 1.0,
            tipo_recurso=tipo_recurso,
            recurso=recurso,
            cuantia=_float(row, "K"),
            comentario=_str(row, "Q"),
            cuantia_por_unidad=_float(row, "S"),  # ya calculado en Excel
            costo_unitario=_float(row, "S"),
        ))
    return result


def _leer_gastos_generales(rows: dict) -> list[GastoGeneral]:
    result: list[GastoGeneral] = []
    for rn in sorted(rows.keys()):
        if rn < 8:
            continue
        row = rows[rn]
        tipo = _str(row, "B")
        recurso = _str(row, "D")
        if not recurso or tipo not in ("Título", "Item"):
            continue
        result.append(GastoGeneral(
            id=int(_float(row, "A") or rn - 7),
            tipo=tipo,
            categoria=_str(row, "C"),
            recurso=recurso,
            unidad=_str(row, "E"),
            moneda=_str(row, "F") or "$AR",
            cantidad=_float(row, "G"),
            mes_inicio=int(_float(row, "H") or 1),
            meses=int(_float(row, "I") or 1),
            amort_perc=_float(row, "J") or 1.0,
            costo_unitario=_float(row, "K"),
            total=_float(row, "L"),
        ))
    return result


def _leer_transporte(rows: dict) -> list[CicloTransporte]:
    result: list[CicloTransporte] = []
    for rn in sorted(rows.keys()):
        if rn < 8:
            continue
        row = rows[rn]
        desc = _str(row, "A")
        if not desc or "Lugar" in desc or "Cantera" in desc or "DMT" in desc:
            continue
        equipo = _str(row, "C")
        if not equipo:
            continue
        result.append(CicloTransporte(
            descripcion=desc,
            unidad=_str(row, "B") or "m3",
            equipo=equipo,
            capacidad=_float(row, "D"),
            distancia_km=_float(row, "E"),
            rendimiento_base=_float(row, "F"),
            vel_ida=_float(row, "G") or 40,
            vel_vuelta=_float(row, "H") or 40,
            tiempo_espera=_float(row, "I") or 5,
            tiempo_carga=_float(row, "J") or 5,
            tiempo_descarga=_float(row, "K") or 5,
            tiempo_ciclo_min=_float(row, "M"),
            hs_dia=_float(row, "N") or 10,
            rend_dia=_float(row, "O"),
            n_camiones=_float(row, "P"),
        ))
    return result


# ── Punto de entrada ───────────────────────────────────────────────────────────

def leer_excel(ruta: str | Path) -> dict:
    """
    Lee el archivo .xlsm y devuelve un dict listo para state.dict_a_estado().
    """
    with zipfile.ZipFile(ruta) as z:
        ss = _shared_strings(z)
        rels = _sheet_rels(z)
        wb_sheets = _workbook_sheets(z)

        def sheet(nombre: str) -> dict:
            rid = wb_sheets.get(nombre)
            if not rid:
                return {}
            path = rels.get(rid, "")
            if not path:
                return {}
            return _read_sheet(z, path, ss)

        # Leer en orden de dependencia
        proyecto = _leer_proyecto(sheet("Proyecto"))

        combustibles = _leer_combustibles(sheet("COM"))
        precio_gasoil = next(
            (c.costo for c in combustibles if "gas oil" in c.descripcion.lower()),
            1491.28,
        )

        equipos = _leer_equipos(sheet("EQ"), proyecto, precio_gasoil)
        mo_jorn = _leer_mo_jornalizada(sheet("MO"))
        mo_mens = _leer_mo_mensualizada(sheet("MO"))
        materiales = _leer_materiales(sheet("MAT"), proyecto)
        subcontratos = _leer_subcontratos(sheet("SUB"), proyecto)
        items = _leer_items(sheet("Items"))
        datos_cd = _leer_datos_cd(sheet("Datos CD"))
        gastos_generales = _leer_gastos_generales(sheet("Datos GG"))
        transportes = _leer_transporte(sheet("Tpte"))

    return {
        "proyecto": proyecto.model_dump(),
        "equipos": [e.model_dump() for e in equipos],
        "mo_jornalizada": [m.model_dump() for m in mo_jorn],
        "mo_mensualizada": [m.model_dump() for m in mo_mens],
        "materiales": [m.model_dump() for m in materiales],
        "combustibles": [c.model_dump() for c in combustibles],
        "subcontratos": [s.model_dump() for s in subcontratos],
        "auxiliares": [],
        "transportes": [t.model_dump() for t in transportes],
        "items": [i.model_dump() for i in items],
        "datos_cd": [d.model_dump() for d in datos_cd],
        "gastos_generales": [g.model_dump() for g in gastos_generales],
    }
