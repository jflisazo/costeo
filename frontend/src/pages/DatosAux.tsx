import { useState, useMemo } from 'react'
import { useParams } from 'react-router-dom'
import {
  Button, Col, Input, InputNumber, Popconfirm, Row, Select, Space, Spin,
  Table, Typography, message,
} from 'antd'
import { PlusOutlined, DeleteOutlined, SyncOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { useProyecto, usePatch, useRecalcular } from '../hooks/useProyecto'
import type { DatoCD, ProyectoEstado } from '../types'

const { Title, Text } = Typography
const fmt = (n: number) => n.toLocaleString('es-AR', { maximumFractionDigits: 2 })
const fmt4 = (n: number) => n.toLocaleString('es-AR', { maximumFractionDigits: 4 })

const TIPOS_RECURSO = [
  'Equipos', 'Mano de Obra', 'Materiales', 'Combustibles',
  'Subcontratos', 'Auxiliares', 'Elaborados', 'Tpte Interno',
]

function recursosOpciones(tipo: string, estado: ProyectoEstado): string[] {
  const t = (tipo || '').toLowerCase()
  if (t.includes('equipo'))       return estado.equipos.map(e => e.nombre)
  if (t.includes('mano') || t === 'mo') return [
    ...estado.mo_jornalizada.map(m => m.funcion),
    ...estado.mo_mensualizada.map(m => m.funcion),
  ]
  if (t.includes('material'))     return estado.materiales.map(m => m.descripcion)
  if (t.includes('combustible'))  return estado.combustibles.map(c => c.descripcion)
  if (t.includes('subcontrat'))   return estado.subcontratos.map(s => s.descripcion)
  if (t.includes('auxiliar') || t.includes('elaborado')) return estado.auxiliares.map(a => a.descripcion)
  if (t.includes('tpte') || t.includes('transport'))     return estado.transportes.map(tr => tr.descripcion)
  return []
}

const EMPTY: DatoCD = {
  item_aux: 'Aux', item_id: '', tarea: '', tarea_unidad: '',
  incidencia: 1, rendimiento: 1, tipo_recurso: 'Materiales', recurso: '',
  cuantia: 0, perc_hs_paro: 0, perc_esf_rr: 0, perc_esf_go: 0,
  comentario: '',
  unidad_recurso: '', costo_recurso: 0, cu_tarea: 0,
  cuantia_por_unidad: 0, costo_unitario: 0,
}

export default function DatosAux() {
  const { id } = useParams<{ id: string }>()
  const pid = Number(id)
  const { data: rec, isLoading } = useProyecto(pid)
  const patch = usePatch(pid)
  const recalc = useRecalcular(pid)
  const [rows, setRows] = useState<DatoCD[]>([])
  const [init, setInit] = useState(false)
  const [busqueda, setBusqueda] = useState('')

  if (isLoading || !rec) return <Spin />
  if (!init) {
    setRows(rec.estado.datos_cd.filter(d => d.item_aux === 'Aux'))
    setInit(true)
  }

  const estado = rec.estado
  const auxOpciones = estado.auxiliares.map(a => ({
    value: a.descripcion, label: `${a.descripcion} (${a.unidad})`,
  }))

  const upd = (i: number, f: keyof DatoCD, v: unknown) =>
    setRows(prev => prev.map((r, j) => j === i ? { ...r, [f]: v } : r))

  const add = () => setRows(prev => [...prev, { ...EMPTY }])
  const del = (i: number) => setRows(prev => prev.filter((_, j) => j !== i))

  const guardar = async () => {
    const itemRows = estado.datos_cd.filter(d => (d.item_aux ?? 'Item') === 'Item')
    const todos = [...itemRows, ...rows.map(r => ({ ...r, item_aux: 'Aux' as const }))]
    await patch.mutateAsync({ seccion: 'datos_cd', data: todos })
    const res = await recalc.mutateAsync()
    setRows(res.estado.datos_cd.filter(d => d.item_aux === 'Aux'))
    message.success('Datos Aux guardados y recalculados.')
  }

  const filas = useMemo(() => {
    const q = busqueda.trim().toLowerCase()
    return rows.map((r, i) => ({ r, i })).filter(({ r }) =>
      !q || r.item_id.toLowerCase().includes(q) ||
      r.tarea.toLowerCase().includes(q) ||
      r.recurso.toLowerCase().includes(q))
  }, [rows, busqueda])

  const cols: ColumnsType<{ r: DatoCD; i: number }> = [
    { title: 'Auxiliar', width: 220, fixed: 'left',
      render: (_, { r, i }) => (
        <Select size="small" style={{ width: 210 }} value={r.item_id || undefined}
          showSearch optionFilterProp="label" placeholder="Seleccionar auxiliar"
          onChange={v => upd(i, 'item_id', v)}
          options={auxOpciones} />
      ) },
    { title: 'Tarea', width: 160,
      render: (_, { r, i }) => (
        <Input size="small" style={{ width: 150 }} value={r.tarea}
          onChange={e => upd(i, 'tarea', e.target.value)} />
      ) },
    { title: 'Uni', width: 65,
      render: (_, { r, i }) => (
        <Input size="small" style={{ width: 55 }} value={r.tarea_unidad}
          onChange={e => upd(i, 'tarea_unidad', e.target.value)} />
      ) },
    { title: 'Incid.', width: 80,
      render: (_, { r, i }) => (
        <InputNumber size="small" style={{ width: 70 }} value={r.incidencia}
          step={0.1} onChange={v => upd(i, 'incidencia', v ?? 1)} />
      ) },
    { title: 'Rendim.', width: 85,
      render: (_, { r, i }) => (
        <InputNumber size="small" style={{ width: 75 }} value={r.rendimiento}
          step={0.5} onChange={v => upd(i, 'rendimiento', v ?? 1)} />
      ) },
    { title: 'Tipo', width: 130,
      render: (_, { r, i }) => (
        <Select size="small" style={{ width: 120 }} value={r.tipo_recurso}
          onChange={v => { upd(i, 'tipo_recurso', v); upd(i, 'recurso', '') }}
          options={TIPOS_RECURSO.map(t => ({ value: t }))} />
      ) },
    { title: 'Recurso', width: 210,
      render: (_, { r, i }) => {
        const opts = recursosOpciones(r.tipo_recurso, estado)
        return (
          <Select size="small" style={{ width: 200 }} value={r.recurso || undefined}
            showSearch optionFilterProp="label"
            onChange={v => upd(i, 'recurso', v)}
            options={opts.map(o => ({ value: o, label: o }))} />
        )
      } },
    { title: 'Cuantía', width: 90,
      render: (_, { r, i }) => (
        <InputNumber size="small" style={{ width: 80 }} value={r.cuantia}
          step={0.1} onChange={v => upd(i, 'cuantia', v ?? 0)} />
      ) },
    { title: '%Hs paro', width: 95,
      render: (_, { r, i }) => (
        <InputNumber size="small" style={{ width: 85 }} value={r.perc_hs_paro}
          step={0.05} min={0} max={1}
          onChange={v => upd(i, 'perc_hs_paro', v ?? 0)} />
      ) },
    { title: '%Esf.RR', width: 90,
      render: (_, { r, i }) => (
        <InputNumber size="small" style={{ width: 80 }} value={r.perc_esf_rr}
          step={0.05} onChange={v => upd(i, 'perc_esf_rr', v ?? 0)} />
      ) },
    { title: '%Esf.GO', width: 90,
      render: (_, { r, i }) => (
        <InputNumber size="small" style={{ width: 80 }} value={r.perc_esf_go}
          step={0.05} onChange={v => upd(i, 'perc_esf_go', v ?? 0)} />
      ) },
    { title: 'Unid', width: 60, align: 'center',
      render: (_, { r }) => <Text type="secondary">{r.unidad_recurso}</Text> },
    { title: 'Costo $', width: 100, align: 'right',
      render: (_, { r }) => fmt(r.costo_recurso) },
    { title: 'CU Tarea', width: 100, align: 'right',
      render: (_, { r }) => fmt(r.cu_tarea) },
    { title: 'CU $', width: 110, align: 'right',
      render: (_, { r }) => <strong>{fmt4(r.costo_unitario)}</strong> },
    { title: 'Comentarios', width: 180,
      render: (_, { r, i }) => (
        <Input size="small" style={{ width: 170 }} value={r.comentario}
          onChange={e => upd(i, 'comentario', e.target.value)} />
      ) },
    { title: '', width: 40, fixed: 'right',
      render: (_, { i }) => (
        <Popconfirm title="¿Eliminar fila?" onConfirm={() => del(i)}>
          <Button size="small" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      ) },
  ]

  return (
    <>
      <Title level={3}>⚗️ Datos Aux</Title>
      <Row gutter={16} style={{ marginBottom: 12 }}>
        {[
          { label: 'Auxiliares definidos', value: estado.auxiliares.length },
          { label: 'Filas Aux', value: rows.length },
          { label: 'Auxiliares con composición', value: new Set(rows.map(r => r.item_id)).size },
        ].map(m => (
          <Col span={8} key={m.label}>
            <div style={{ background: '#f5f5f5', padding: '8px 12px', borderRadius: 6 }}>
              <Text type="secondary" style={{ fontSize: 12 }}>{m.label}</Text><br />
              <Text strong>{m.value}</Text>
            </div>
          </Col>
        ))}
      </Row>

      <Space style={{ marginBottom: 8 }} wrap>
        <Input.Search placeholder="Filtrar por auxiliar, tarea o recurso"
          value={busqueda} onChange={e => setBusqueda(e.target.value)}
          allowClear style={{ width: 320 }} />
        <Button icon={<PlusOutlined />} onClick={add}>Agregar fila</Button>
        <Button type="primary" icon={<SyncOutlined />} onClick={guardar}
          loading={patch.isPending || recalc.isPending}>
          Guardar y Recalcular
        </Button>
        <Text type="secondary" style={{ fontSize: 12 }}>
          Definí los auxiliares (descripción + unidad) en la página Auxiliares.
        </Text>
      </Space>

      <Table
        dataSource={filas}
        columns={cols}
        rowKey={({ i }) => String(i)}
        size="small"
        pagination={{ pageSize: 50, showSizeChanger: true, pageSizeOptions: [25, 50, 100, 200] }}
        scroll={{ x: 1950 }}
      />
    </>
  )
}
