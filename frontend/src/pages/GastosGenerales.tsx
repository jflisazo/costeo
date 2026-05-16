import { useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  Button, InputNumber, Popconfirm, Select, Space, Spin, Table, Tag, Typography, message,
} from 'antd'
import { PlusOutlined, DeleteOutlined, SyncOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { useProyecto, usePatch, useRecalcular } from '../hooks/useProyecto'
import type { GastoGeneral } from '../types'

const { Title, Text } = Typography
const fmt = (n: number) => n.toLocaleString('es-AR', { maximumFractionDigits: 2 })

const EMPTY: GastoGeneral = {
  id: 0, tipo: 'Item', categoria: '', recurso: '', unidad: '', moneda: '$AR',
  cantidad: 1, mes_inicio: 1, meses: 1, amort_perc: 1.0,
  costo_unitario: 0, aux: '', comentario: '', total: 0,
}

const MONEDAS = ['$AR', 'USD', 'EUR']

export default function GastosGenerales() {
  const { id } = useParams<{ id: string }>()
  const pid = Number(id)
  const { data: rec, isLoading } = useProyecto(pid)
  const patch = usePatch(pid)
  const recalc = useRecalcular(pid)
  const [rows, setRows] = useState<GastoGeneral[]>([])
  const [init, setInit] = useState(false)

  if (isLoading || !rec) return <Spin />
  if (!init) { setRows(rec.estado.gastos_generales); setInit(true) }

  const upd = (i: number, f: keyof GastoGeneral, v: unknown) =>
    setRows(prev => prev.map((r, j) => j === i ? { ...r, [f]: v } : r))

  const nextId = () => (rows.reduce((m, r) => Math.max(m, r.id), 0) || 0) + 1

  const add = () => setRows(prev => [...prev, { ...EMPTY, id: nextId() }])
  const del = (i: number) => setRows(prev => prev.filter((_, j) => j !== i))

  const guardar = async () => {
    await patch.mutateAsync({ seccion: 'gastos_generales', data: rows })
    const res = await recalc.mutateAsync()
    setRows(res.estado.gastos_generales)
    message.success('Gastos generales guardados y recalculados.')
  }

  // El recurso puede ser cualquier texto pero ayudamos con sugerencias de MO mensualizada
  const moMens = rec.estado.mo_mensualizada.map(m => m.funcion)

  const totalGG = rows.filter(r => r.tipo === 'Item').reduce((s, r) => s + r.total, 0)
  const itemRows = rows.filter(r => r.tipo === 'Item')

  const cols: ColumnsType<GastoGeneral> = [
    { title: 'ID', dataIndex: 'id', width: 60, fixed: 'left',
      render: (v, _, i) => (
        <InputNumber size="small" style={{ width: 50 }} value={v}
          onChange={val => upd(i, 'id', val ?? 0)} />
      ) },
    { title: 'Tipo', dataIndex: 'tipo', width: 90, fixed: 'left',
      render: (v, _, i) => (
        <Select size="small" style={{ width: 80 }} value={v}
          onChange={val => upd(i, 'tipo', val)}
          options={[{ value: 'Título' }, { value: 'Item' }]} />
      ) },
    { title: 'Item (Categoría)', dataIndex: 'categoria', width: 170,
      render: (v, _, i) => (
        <input className="ant-input ant-input-sm" style={{ width: 160 }}
          value={v} onChange={e => upd(i, 'categoria', e.target.value)} />
      ) },
    { title: 'Recurso', dataIndex: 'recurso', width: 200,
      render: (v, row, i) => row.tipo === 'Item'
        ? <Select size="small" mode="tags" maxCount={1} style={{ width: 190 }}
            value={v ? [v] : []}
            options={moMens.map(o => ({ value: o, label: o }))}
            onChange={vals => upd(i, 'recurso', vals[0] ?? '')} />
        : null },
    { title: 'Unidad', dataIndex: 'unidad', width: 80,
      render: (v, row, i) => row.tipo === 'Item'
        ? <input className="ant-input ant-input-sm" style={{ width: 70 }}
            value={v} onChange={e => upd(i, 'unidad', e.target.value)} />
        : null },
    { title: 'Moneda', dataIndex: 'moneda', width: 80,
      render: (v, row, i) => row.tipo === 'Item'
        ? <Select size="small" style={{ width: 70 }} value={v}
            onChange={val => upd(i, 'moneda', val)}
            options={MONEDAS.map(m => ({ value: m }))} />
        : null },
    { title: 'Cantidad', dataIndex: 'cantidad', width: 90,
      render: (v, row, i) => row.tipo === 'Item'
        ? <InputNumber size="small" style={{ width: 80 }} value={v} step={1}
            onChange={val => upd(i, 'cantidad', val ?? 0)} />
        : null },
    { title: 'Comienzo', dataIndex: 'mes_inicio', width: 90,
      render: (v, row, i) => row.tipo === 'Item'
        ? <InputNumber size="small" style={{ width: 80 }} value={v} step={1} min={1}
            onChange={val => upd(i, 'mes_inicio', val ?? 1)} />
        : null },
    { title: 'Meses', dataIndex: 'meses', width: 80,
      render: (v, row, i) => row.tipo === 'Item'
        ? <InputNumber size="small" style={{ width: 70 }} value={v} step={1} min={0}
            onChange={val => upd(i, 'meses', val ?? 0)} />
        : null },
    { title: 'Amort%', dataIndex: 'amort_perc', width: 85,
      render: (v, row, i) => row.tipo === 'Item'
        ? <InputNumber size="small" style={{ width: 75 }} value={v * 100} step={10}
            onChange={val => upd(i, 'amort_perc', (val ?? 100) / 100)} />
        : null },
    { title: 'Costo', dataIndex: 'costo_unitario', width: 130,
      render: (v, row, i) => row.tipo === 'Item'
        ? <InputNumber size="small" style={{ width: 120 }} value={v} step={100}
            onChange={val => upd(i, 'costo_unitario', val ?? 0)} />
        : null },
    { title: 'Aux', dataIndex: 'aux', width: 130,
      render: (v, _, i) => (
        <input className="ant-input ant-input-sm" style={{ width: 120 }}
          value={v} onChange={e => upd(i, 'aux', e.target.value)} />
      ) },
    { title: 'Comentario', dataIndex: 'comentario', width: 180,
      render: (v, _, i) => (
        <input className="ant-input ant-input-sm" style={{ width: 170 }}
          value={v} onChange={e => upd(i, 'comentario', e.target.value)} />
      ) },
    { title: 'TOTAL', dataIndex: 'total', width: 140, align: 'right',
      render: (v, row) => row.tipo === 'Item' ? <strong>{fmt(v)}</strong> : null },
    { title: '', width: 40, fixed: 'right',
      render: (_, __, i) => (
        <Popconfirm title="¿Eliminar?" onConfirm={() => del(i)}>
          <Button size="small" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      ) },
  ]

  return (
    <>
      <Title level={3}>💰 Datos GG</Title>
      <Space style={{ marginBottom: 8 }} wrap>
        <Button icon={<PlusOutlined />} onClick={add}>Agregar ítem</Button>
        <Button type="primary" icon={<SyncOutlined />} onClick={guardar}
          loading={patch.isPending || recalc.isPending}>
          Guardar y Recalcular
        </Button>
        <Tag color="blue">Total GG: ${fmt(totalGG)}</Tag>
        <Tag>Filas item: {itemRows.length}</Tag>
        <Text type="secondary" style={{ fontSize: 12 }}>
          Si "Recurso" coincide con una función mensualizada, "Costo" se autocompleta.
        </Text>
      </Space>
      <Table
        dataSource={rows}
        columns={cols}
        rowKey={(_, i) => String(i)}
        size="small"
        pagination={{ pageSize: 100, showSizeChanger: true, pageSizeOptions: [50, 100, 200] }}
        scroll={{ x: 1800 }}
        rowClassName={row => row.tipo === 'Título' ? 'row-titulo' : ''}
      />
    </>
  )
}
