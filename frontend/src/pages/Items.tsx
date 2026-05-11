import { useState, useMemo } from 'react'
import { useParams } from 'react-router-dom'
import {
  Button, Col, Input, InputNumber, Popconfirm, Row, Segmented, Select,
  Space, Spin, Table, Typography, message,
} from 'antd'
import { PlusOutlined, DeleteOutlined, SyncOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { useProyecto, usePatch, useRecalcular } from '../hooks/useProyecto'
import type { DatoCD, Item, ProyectoEstado } from '../types'

const { Title, Text } = Typography
const fmt = (n: number) => n.toLocaleString('es-AR', { maximumFractionDigits: 2 })
const fmt4 = (n: number) => n.toLocaleString('es-AR', { maximumFractionDigits: 4 })

const TIPOS_RECURSO = [
  'Equipos', 'Mano de Obra', 'Materiales', 'Combustibles',
  'Subcontratos', 'Auxiliares', 'Tpte Interno',
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

const EMPTY_CD: DatoCD = {
  item_aux: 'Item', item_id: '', tarea: '', tarea_unidad: '',
  incidencia: 1, rendimiento: 1, tipo_recurso: 'Equipos', recurso: '',
  cuantia: 0, comentario: '', cuantia_por_unidad: 0, costo_unitario: 0,
}

type Filtro = 'Todo' | 'Item' | 'Aux'

export default function Items() {
  const { id } = useParams<{ id: string }>()
  const pid = Number(id)
  const { data: rec, isLoading } = useProyecto(pid)
  const patch = usePatch(pid)
  const recalc = useRecalcular(pid)

  const [cdRows, setCdRows] = useState<DatoCD[]>([])
  const [cdInit, setCdInit] = useState(false)
  const [filtro, setFiltro] = useState<Filtro>('Todo')
  const [busqueda, setBusqueda] = useState('')

  if (isLoading || !rec) return <Spin />

  const estado = rec.estado
  const { items } = estado

  if (!cdInit) {
    // Normalizar filas que vienen sin item_aux (proyectos antiguos)
    const norm = estado.datos_cd.map(d => ({ ...d, item_aux: d.item_aux ?? 'Item' }))
    setCdRows(norm)
    setCdInit(true)
  }

  const itemsObra = items.filter(i => i.tipo === 'Item')
  const auxList = estado.auxiliares

  const itemOpciones = (iaux: 'Item' | 'Aux') =>
    iaux === 'Item'
      ? itemsObra.map(i => ({ value: i.numero, label: `${i.numero} — ${i.descripcion}` }))
      : auxList.map(a => ({ value: a.descripcion, label: a.descripcion }))

  const filasFiltradas = useMemo(() => {
    const q = busqueda.trim().toLowerCase()
    return cdRows
      .map((r, idx) => ({ row: r, idx }))
      .filter(({ row }) => filtro === 'Todo' || row.item_aux === filtro)
      .filter(({ row }) => !q ||
        row.item_id.toLowerCase().includes(q) ||
        row.tarea.toLowerCase().includes(q) ||
        row.recurso.toLowerCase().includes(q))
  }, [cdRows, filtro, busqueda])

  const updCD = (globalIdx: number, f: keyof DatoCD, v: unknown) => {
    setCdRows(prev => prev.map((r, j) => j === globalIdx ? { ...r, [f]: v } : r))
  }

  const addCD = () => {
    const base: DatoCD = { ...EMPTY_CD, item_aux: filtro === 'Aux' ? 'Aux' : 'Item' }
    setCdRows(prev => [...prev, base])
  }

  const delCD = (globalIdx: number) => {
    setCdRows(prev => prev.filter((_, j) => j !== globalIdx))
  }

  const guardar = async () => {
    await patch.mutateAsync({ seccion: 'datos_cd', data: cdRows })
    const result = await recalc.mutateAsync()
    const norm = result.estado.datos_cd.map(d => ({ ...d, item_aux: d.item_aux ?? 'Item' }))
    setCdRows(norm)
    message.success('Datos CD guardados y recalculados.')
  }

  const itemCols: ColumnsType<Item> = [
    { title: '#', dataIndex: 'numero', width: 130, ellipsis: true,
      render: (v, row) => row.tipo === 'Título'
        ? <Text strong style={{ color: '#1677ff' }}>{v}</Text>
        : <Text code style={{ fontSize: 11 }}>{v}</Text> },
    { title: 'Descripción', dataIndex: 'descripcion', ellipsis: true,
      render: (v, row) => row.tipo === 'Título' ? <Text strong>{v}</Text> : v },
    { title: 'Unid.', dataIndex: 'unidad', width: 60 },
    { title: 'Cantidad', dataIndex: 'cantidad', width: 90, align: 'right', render: v => fmt(v) },
    { title: 'CU Costo', dataIndex: 'costo_unitario', width: 110, align: 'right', render: v => fmt(v) },
    { title: 'Total Costo', dataIndex: 'costo_total', width: 120, align: 'right',
      render: v => <strong>{fmt(v)}</strong> },
    { title: 'CU Precio', dataIndex: 'precio_unitario', width: 110, align: 'right', render: v => fmt(v) },
    { title: 'Total Precio', dataIndex: 'precio_total', width: 120, align: 'right',
      render: v => <Text type="success"><strong>{fmt(v)}</strong></Text> },
  ]

  type FilaCD = { row: DatoCD; idx: number }
  const cdCols: ColumnsType<FilaCD> = [
    { title: 'Item/Aux', width: 90,
      render: (_, { row, idx }) => (
        <Select size="small" style={{ width: 80 }} value={row.item_aux}
          onChange={val => { updCD(idx, 'item_aux', val); updCD(idx, 'item_id', '') }}
          options={[{ value: 'Item' }, { value: 'Aux' }]} />
      ) },
    { title: 'Item', width: 200,
      render: (_, { row, idx }) => {
        const opts = itemOpciones(row.item_aux)
        return <Select size="small" style={{ width: 190 }} value={row.item_id || undefined}
          showSearch optionFilterProp="label"
          onChange={val => updCD(idx, 'item_id', val)}
          options={opts} />
      } },
    { title: 'Tarea', width: 140,
      render: (_, { row, idx }) => (
        <Input size="small" style={{ width: 130 }} value={row.tarea}
          onChange={e => updCD(idx, 'tarea', e.target.value)} />
      ) },
    { title: 'Uni', width: 65,
      render: (_, { row, idx }) => (
        <Input size="small" style={{ width: 55 }} value={row.tarea_unidad}
          onChange={e => updCD(idx, 'tarea_unidad', e.target.value)} />
      ) },
    { title: 'Incid.', width: 80,
      render: (_, { row, idx }) => (
        <InputNumber size="small" style={{ width: 70 }} value={row.incidencia} step={0.1}
          onChange={v => updCD(idx, 'incidencia', v ?? 1)} />
      ) },
    { title: 'Rendim.', width: 85,
      render: (_, { row, idx }) => (
        <InputNumber size="small" style={{ width: 75 }} value={row.rendimiento} step={0.5}
          onChange={v => updCD(idx, 'rendimiento', v ?? 1)} />
      ) },
    { title: 'Tipo', width: 140,
      render: (_, { row, idx }) => (
        <Select size="small" style={{ width: 130 }} value={row.tipo_recurso}
          onChange={val => { updCD(idx, 'tipo_recurso', val); updCD(idx, 'recurso', '') }}
          options={TIPOS_RECURSO.map(t => ({ value: t }))} />
      ) },
    { title: 'Recurso', width: 200,
      render: (_, { row, idx }) => {
        const opts = recursosOpciones(row.tipo_recurso, estado)
        return <Select size="small" style={{ width: 190 }} value={row.recurso || undefined}
          showSearch optionFilterProp="label"
          onChange={val => updCD(idx, 'recurso', val)}
          options={opts.map(o => ({ value: o, label: o }))} />
      } },
    { title: 'Cuantía', width: 90,
      render: (_, { row, idx }) => (
        <InputNumber size="small" style={{ width: 80 }} value={row.cuantia} step={0.1}
          onChange={v => updCD(idx, 'cuantia', v ?? 0)} />
      ) },
    { title: 'Q/unid', width: 90, align: 'right',
      render: (_, { row }) => fmt4(row.cuantia_por_unidad) },
    { title: 'CU $', width: 100, align: 'right',
      render: (_, { row }) => <strong>{fmt4(row.costo_unitario)}</strong> },
    { title: 'Comentario', width: 160,
      render: (_, { row, idx }) => (
        <Input size="small" style={{ width: 150 }} value={row.comentario}
          onChange={e => updCD(idx, 'comentario', e.target.value)} />
      ) },
    { title: '', width: 40, fixed: 'right',
      render: (_, { idx }) =>
        <Popconfirm title="¿Eliminar fila?" onConfirm={() => delCD(idx)}>
          <Button size="small" danger icon={<DeleteOutlined />} />
        </Popconfirm> },
  ]

  const costoCD = itemsObra.reduce((s, i) => s + i.costo_total, 0)
  const precioTotal = itemsObra.reduce((s, i) => s + i.precio_total, 0)

  return (
    <>
      <Title level={3}>📐 Ítems y Costos Directos</Title>

      <Row gutter={16} style={{ marginBottom: 12 }}>
        {[
          { label: 'Ítems de obra', value: itemsObra.length },
          { label: 'Filas Datos CD', value: cdRows.length },
          { label: 'Costo Directo Total', value: `$${fmt(costoCD)}` },
          { label: 'Precio Total', value: `$${fmt(precioTotal)}` },
        ].map(m => (
          <Col span={6} key={m.label}>
            <div style={{ background: '#f5f5f5', padding: '8px 12px', borderRadius: 6 }}>
              <Text type="secondary" style={{ fontSize: 12 }}>{m.label}</Text><br />
              <Text strong>{m.value}</Text>
            </div>
          </Col>
        ))}
      </Row>

      <Table
        dataSource={items}
        columns={itemCols}
        rowKey={row => row.uid || `${row.tipo}-${row.numero}`}
        size="small"
        pagination={false}
        scroll={{ x: 860, y: 280 }}
        rowClassName={row => row.tipo === 'Título' ? 'row-titulo' : ''}
      />

      <Title level={4} style={{ marginTop: 24 }}>Datos CD</Title>
      <Space style={{ marginBottom: 8 }} wrap>
        <Segmented value={filtro} onChange={v => setFiltro(v as Filtro)}
          options={['Todo', 'Item', 'Aux']} />
        <Input.Search placeholder="Filtrar por ítem, tarea o recurso"
          value={busqueda} onChange={e => setBusqueda(e.target.value)}
          allowClear style={{ width: 320 }} />
        <Button icon={<PlusOutlined />} onClick={addCD}>Agregar fila</Button>
        <Button type="primary" icon={<SyncOutlined />}
          onClick={guardar} loading={patch.isPending || recalc.isPending}>
          Guardar y Recalcular
        </Button>
      </Space>

      <Table
        dataSource={filasFiltradas}
        columns={cdCols}
        rowKey={({ idx }) => String(idx)}
        size="small"
        pagination={{ pageSize: 50, showSizeChanger: true, pageSizeOptions: [25, 50, 100, 200] }}
        scroll={{ x: 1500 }}
        summary={pageRows => {
          const sumCU = pageRows.reduce((s, { row }) => s + row.costo_unitario, 0)
          return (
            <Table.Summary.Row>
              <Table.Summary.Cell index={0} colSpan={10} align="right">
                <strong>Σ CU (filas visibles):</strong>
              </Table.Summary.Cell>
              <Table.Summary.Cell index={10} align="right">
                <strong>{fmt4(sumCU)}</strong>
              </Table.Summary.Cell>
              <Table.Summary.Cell index={11} colSpan={2} />
            </Table.Summary.Row>
          )
        }}
      />
    </>
  )
}
