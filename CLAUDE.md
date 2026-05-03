# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the app

**Streamlit (legacy, Phase 2):**
```bash
cd /home/fernando/costeo
streamlit run app.py        # http://localhost:8501
```

**FastAPI backend (Phase 3):**
```bash
cd /home/fernando/costeo
uvicorn backend.main:app --reload --port 8000
# API docs: http://localhost:8000/docs
```

**React frontend (Phase 3):**
```bash
cd /home/fernando/costeo/frontend
npm install
npm run dev                 # http://localhost:5173
```
Vite proxies `/api/*` → `http://localhost:8000`.

There are no tests or linters configured.

To verify a module compiles without starting Streamlit:
```bash
python -c "from calculos import recalcular_todo; print('ok')"
```

## Architecture

This is a Streamlit app for construction cost estimation ("costeo de obra vial"). It is designed to be migrated to FastAPI + frontend later, so the business logic is kept strictly separate from the UI.

**Layer separation:**
- `models/` — Pydantic v2 dataclasses only. No Streamlit imports, no calculation logic.
- `calculos/` — Pure functions. Input: model instances + scalar params. Output: updated model instances via `model.model_copy(update={...})`. No Streamlit imports.
- `pages/` — Streamlit UI only. Reads/writes `st.session_state`, calls `calculos/` functions.
- `state.py` — The bridge: `init_state()`, `guardar()`, `cargar()`, and the serialize/deserialize helpers.
- `storage/json_store.py` — Saves/loads project state as JSON under `data/<nombre>.json`.
- `importar/excel_reader.py` — Reads the `.xlsm` source file directly as a ZIP archive (xml.etree) to avoid openpyxl slowness on large VBA files.

## Cascade recalculation

`calculos/recalcular.py::recalcular_todo()` is called whenever global parameters (USD cotization, gasoil price, project rates) change. The mandatory order is:

1. Combustibles → 2. MO jornalizada + mensualizada → 3. Equipos → 4. Materiales → 5. Subcontratos → 6. Auxiliares → 7. Transportes → 8. Datos CD → 9. Ítems → 10. Gastos Generales

Breaking this order causes downstream costs to use stale unit prices. `pages/1_Proyecto.py` triggers this cascade on save.

## DatoCD: the core cost formula

`DatoCD` rows are the fact table. Each row ties one resource to one task inside one item:

```python
cuantia_por_unidad = (cuantia / rendimiento) * incidencia
costo_unitario     = cuantia_por_unidad * lookup_costo_recurso(tipo, nombre, ...)
cu_item            = sum(costo_unitario for all rows with item_id == item_id)
```

`lookup_costo_recurso` (in `calculos/costos_directos.py`) does name-based matching against all resource lists. Resource names must match exactly between `DatoCD.recurso` and the name field of the corresponding model (`Equipo.nombre`, `Material.descripcion`, etc.).

## KEOPS equipment costs

KEOPS is an Argentine equipment cost database. The Excel stores pre-calculated $/hr values that cannot be reproduced with a universal formula. At import time, `importar/excel_reader.py` stores:
```python
ratio_ai = cu_ai / (precio * cotiz_usd)
ratio_rr = cu_rr / (precio * cotiz_usd)
cotiz_base = cotiz_usd
```

When the USD cotization changes, `calculos/equipos.py` scales:
```python
cu_ai = ratio_ai * precio * cotiz_nueva
cu_rr = ratio_rr * precio * cotiz_nueva
```

This is why the `Equipo.metodo_costeo` default is `"KEOPS"`, not `"DNV"`.

## Equipment cost methods

`Equipo.metodo_costeo` controls which branch `calc_costo_equipo()` uses:
- `"KEOPS"` — ratio scaling (see above). Fields: `ratio_ai`, `ratio_rr`, `cotiz_base`.
- `"DNV"` — standard Dirección Nacional de Vialidad formula. Fields: `vida_util_hs`, `vr`, `uso_anual`, `k_rr`; `tasa_anual` comes from `Proyecto`.
- `"Porcentaje"` — `cu_ai = precio_ar * porcentaje / uso_anual`. Fields: `porcentaje`, `uso_anual`.
- `"Manual_AR"` — fixed `cu_ai` and `cu_rr` in $AR; only `cu_comb` updates with gasoil price.

## Session state keys

All keys are initialized in `state.py::DEFAULTS`. The full list:
`proyecto`, `equipos`, `mo_jornalizada`, `mo_mensualizada`, `materiales`, `combustibles`, `subcontratos`, `auxiliares`, `transportes`, `items`, `datos_cd`, `gastos_generales`, `plan_trabajos`, `proyecto_nombre`.

Every page must call `init_state()` before accessing session state.
