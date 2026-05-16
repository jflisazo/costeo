export interface Proyecto {
  empresa: string
  obra: string
  comitente: string
  plazo_meses: number
  moneda_oferta: string
  mes_base: string
  cotizaciones: Record<string, number>
  calculo: string
  plazo_pago: number
  anticipo: number
  horas_mes_eq: number
  tasa_anual: number
  vida_util_hs: number
  efi_mo: number
  incr_mo: number
  coef_oferta: number
}

export interface Equipo {
  nombre: string
  marca: string
  modelo: string
  potencia: number
  moneda: string
  precio: number
  k_combustible: number
  propiedad: string
  vida_util_hs: number
  vr: number
  uso_anual: number
  k_rr: number
  metodo_costeo: string
  porcentaje: number
  ratio_ai: number
  ratio_rr: number
  cotiz_base: number
  cu_ai: number
  cu_rr: number
  cu_comb: number
  costo_hora: number
}

export interface MOJornalizada {
  funcion: string
  id: number
  moneda: string
  bruto: number
  aguinaldo: number
  vacaciones: number
  cargas_sociales: number
  bolsillo: number
  viatico: number
  horas_mes: number
  costo_hora: number
}

export interface MOMensualizada {
  funcion: string
  moneda: string
  neto: number
  bruto: number
  aguinaldo: number
  dias_vacaciones: number
  vacaciones: number
  cargas_sociales: number
  prop_despido: number
  costo_mes: number
}

export interface Material {
  numero: number
  descripcion: string
  unidad: string
  moneda: string
  proveedor: string
  origen: string
  distancia_km: number
  costo_origen: number
  costo_flete: number
  otros: number
  perc_perdida: number
  costo: number
}

export interface Combustible {
  descripcion: string
  unidad: string
  moneda: string
  proveedor: string
  costo_origen: number
  otros: number
  costo: number
}

export interface Subcontrato {
  numero: number
  descripcion: string
  unidad: string
  moneda: string
  proveedor: string
  costo_or: number
  otros: number
  costo: number
}

export interface RecursoAux {
  tarea: string
  tarea_unidad: string
  incidencia: number
  rendimiento: number
  tipo_recurso: string
  recurso: string
  cuantia: number
  comentario: string
  cuantia_por_unidad: number
  costo_unitario: number
}

export interface Auxiliar {
  tipo: string
  descripcion: string
  unidad: string
  recursos: RecursoAux[]
  costo: number
}

export interface CicloTransporte {
  descripcion: string
  unidad: string
  equipo: string
  capacidad: number
  distancia_km: number
  rendimiento_base: number
  vel_ida: number
  vel_vuelta: number
  tiempo_espera: number
  tiempo_carga: number
  tiempo_descarga: number
  hs_dia: number
  tiempo_viaje_min: number
  tiempo_ciclo_min: number
  rend_dia: number
  n_camiones: number
  costo: number
}

export interface DatoCD {
  item_aux: 'Item' | 'Aux'
  item_id: string
  item_uid?: string
  tarea: string
  tarea_unidad: string
  incidencia: number
  rendimiento: number
  tipo_recurso: string
  recurso: string
  cuantia: number
  perc_hs_paro: number
  perc_esf_rr: number
  perc_esf_go: number
  comentario: string
  // calculados
  unidad_recurso: string
  costo_recurso: number
  cu_tarea: number
  cuantia_por_unidad: number
  costo_unitario: number
}

export interface Item {
  tipo: 'Título' | 'Item'
  numero: string
  uid?: string
  descripcion: string
  unidad: string
  cantidad: number
  grupo: string
  sub_grupo: string
  margen: number
  costo_unitario: number
  costo_total: number
  precio_unitario: number
  precio_total: number
}

export interface GastoGeneral {
  id: number
  tipo: 'Título' | 'Item'
  categoria: string
  recurso: string
  unidad: string
  moneda: string
  cantidad: number
  mes_inicio: number
  meses: number
  amort_perc: number
  costo_unitario: number
  aux: string
  comentario: string
  total: number
}

export interface PlanTrabajo {
  item_id: string
  descripcion: string
  distribucion: number[]
}

export interface GanttFila {
  tipo: 'Título' | 'Item'
  numero: string
  item_uid?: string
  descripcion: string
  unidad: string
  cantidad: number
  meses: number[]      // longitud 60
  ctrl: number
}

export interface ProyectoEstado {
  proyecto: Proyecto
  equipos: Equipo[]
  mo_jornalizada: MOJornalizada[]
  mo_mensualizada: MOMensualizada[]
  materiales: Material[]
  combustibles: Combustible[]
  subcontratos: Subcontrato[]
  auxiliares: Auxiliar[]
  transportes: CicloTransporte[]
  items: Item[]
  datos_cd: DatoCD[]
  gastos_generales: GastoGeneral[]
  plan_trabajos: PlanTrabajo[]
  gantt: GanttFila[]
}

export interface ProyectoRecord {
  id: number
  nombre: string
  estado: ProyectoEstado
  updated_at: string | null
}

export interface ProyectoInfo {
  id: number
  nombre: string
  updated_at: string | null
}
