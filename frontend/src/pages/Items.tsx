import { useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  Button, Col, Input, InputNumber, Popconfirm, Row, Select, Space, Spin,
  Table, Typography, message,
} from 'antd'
import { PlusOutlined, DeleteOutlined, SyncOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { useProyecto, usePatch, useRecalcular } from '../hooks/useProyecto'
import type { Item } from '../types'

const { Title, Text } = Typography
const fmt = (n: number) => n.toLocaleString('es-AR', { maximumFractionDigits: 2 })

const EMPTY: Item = {
  tipo: 'Item', numero: '', descripcion: '', unidad: '', cantidad: 0,
  grupo: '', sub_grupo: '', margen: 0,
  costo_unitario: 0, costo_total: 0, precio_unitario: 0, precio_total: 0,
}

export default function Items() {
  const { id } = useParams<{ id: string }>()
  const pid = Number(id)
  const { data: rec, isLoading } = useProyecto(pid)
  const patch = usePatch(pid)
  const recalc = useRecalcular(pid)
  const [rows, setRows] = useState<Item[]>([])
  const [init, setInit] = useState(false)
  const [filtro, setFiltro] = useState('')

  if (isLoading || !rec) return <Spin />
  if (!init) { setRows(rec.estado.items); setInit(true) }

  const upd = (i: number, f: keyof Item, v: unknown) =>
    setRows(prev => prev.map((r, j) => j === i ? { ...r, [f]: v } : r))

  const add = () => setRows(prev => [...prev, { ...EMPTY }])
  const del = (i: number) => setRows(prev => prev.filter((_, j) => j !== i))

  const guardar = async () => {
    await patch.mutateAsync({ seccion: 'items', data: rows })
    const res = await recalc.mutateAsync()
    setRows(res.estado.items)
    message.success('Ítems guardados y recalculados.')
  }

  const q = filtro.trim().toLowerCase()
  const rowsFiltradas = q
    ? rows.map((r, i) => ({ r, i })).filter(({ r }) =>
        r.numero.toLowerCase().includes(q) ||
        r.descripcion.toLowerCase().includes(q) ||
        (r.grupo || '').toLowerCase().includes(q))
    : rows.map((r, i) => ({ r, i }))

  const itemsObra = rows.filter(r => r.tipo === 'Item')
  const totalCosto = itemsObra.reduce((s, i) => s + i.costo_total, 0)
  const totalPrecio = itemsObra.reduce((s, i) => s + i.precio_total, 0)

  const cols: ColumnsType<{ r: Item; i: number }> = [
    { title: 'Tipo', width: 90, fixed: 'left',
      render: (_, { r, i }) => (
        <Select size="small" style={{ width: 80 }} value={r.tipo}
          onChange={v => upd(i, 'tipo', v)}
          options={[{ value: 'Título' }, { value: 'Item' }]} />
      ) },
    { title: 'Nº', width: 130, fixed: 'left',
      render: (_, { r, i }) => (
        <Input size="small" style={{ width: 125 }} value={r.numero}
          onChange={e => upd(i, 'numero', e.target.value)} />
      ) },
    { title: 'Descripción', width: 320,
      render: (_, { r, i }) => (
        <Input size="small" value={r.descripcion}
          onChange={e => upd(i, 'descripcion', e.target.value)} />
      ) },
    { title: 'Un', width: 75,
      render: (_, { r, i }) => (
        <Input size="small" style={{ width: 65 }} value={r.unidad}
          onChange={e => upd(i, 'unidad', e.target.value)} />
      ) },
    { title: 'Cantidad', width: 110,
      render: (_, { r, i }) => r.tipo === 'Item' ? (
        <InputNumber size="small" style={{ width: 100 }} value={r.cantidad}
          step={1} onChange={v => upd(i, 'cantidad', v ?? 0)} />
      ) : null },
    { title: 'Grupo', width: 130,
      render: (_, { r, i }) => (
        <Input size="small" style={{ width: 120 }} value={r.grupo}
          onChange={e => upd(i, 'grupo', e.target.value)} />
      ) },
    { title: 'Subgrupo', width: 130,
      render: (_, { r, i }) => (
        <Input size="small" style={{ width: 120 }} value={r.sub_grupo}
          onChange={e => upd(i, 'sub_grupo', e.target.value)} />
      ) },
    { title: 'CU Costo', dataIndex: 'costo_unitario', width: 110, align: 'right',
      render: (_, { r }) => r.tipo === 'Item' ? fmt(r.costo_unitario) : null },
    { title: 'Total Costo', dataIndex: 'costo_total', width: 130, align: 'right',
      render: (_, { r }) => r.tipo === 'Item' ? <strong>{fmt(r.costo_total)}</strong> : null },
    { title: 'CU Precio', dataIndex: 'precio_unitario', width: 110, align: 'right',
      render: (_, { r }) => r.tipo === 'Item' ? fmt(r.precio_unitario) : null },
    { title: 'Total Precio', dataIndex: 'precio_total', width: 130, align: 'right',
      render: (_, { r }) => r.tipo === 'Item'
        ? <Text type="success"><strong>{fmt(r.precio_total)}</strong></Text> : null },
    { title: '', width: 40, fixed: 'right',
      render: (_, { i }) => (
        <Popconfirm title="¿Eliminar fila?" onConfirm={() => del(i)}>
          <Button size="small" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      ) },
  ]

  return (
    <>
      <Title level={3}>📐 Ítems</Title>
      <Row gutter={16} style={{ marginBottom: 12 }}>
        {[
          { label: 'Ítems de obra', value: itemsObra.length },
          { label: 'Filas totales', value: rows.length },
          { label: 'Costo Directo Total', value: `$${fmt(totalCosto)}` },
          { label: 'Precio Total', value: `$${fmt(totalPrecio)}` },
        ].map(m => (
          <Col span={6} key={m.label}>
            <div style={{ background: '#f5f5f5', padding: '8px 12px', borderRadius: 6 }}>
              <Text type="secondary" style={{ fontSize: 12 }}>{m.label}</Text><br />
              <Text strong>{m.value}</Text>
            </div>
          </Col>
        ))}
      </Row>

      <Space style={{ marginBottom: 12 }} wrap>
        <Input.Search placeholder="Filtrar por Nº, descripción o grupo"
          value={filtro} onChange={e => setFiltro(e.target.value)}
          allowClear style={{ width: 320 }} />
        <Button icon={<PlusOutlined />} onClick={add}>Agregar ítem</Button>
        <Button type="primary" icon={<SyncOutlined />} onClick={guardar}
          loading={patch.isPending || recalc.isPending}>
          Guardar y Recalcular
        </Button>
        <Text type="secondary" style={{ fontSize: 12 }}>
          Los campos CU/Total se calculan al guardar a partir de Datos CD.
        </Text>
      </Space>

      <Table
        dataSource={rowsFiltradas}
        columns={cols}
        rowKey={({ i }) => String(i)}
        size="small"
        pagination={{ pageSize: 100, showSizeChanger: true, pageSizeOptions: [50, 100, 200] }}
        scroll={{ x: 1600 }}
        rowClassName={({ r }) => r.tipo === 'Título' ? 'row-titulo' : ''}
      />
    </>
  )
}
