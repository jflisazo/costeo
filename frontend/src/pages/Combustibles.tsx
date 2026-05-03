import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { Button, InputNumber, Popconfirm, Space, Spin, Table, Typography, message } from 'antd'
import { PlusOutlined, DeleteOutlined, SyncOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { useProyecto, usePatch, useRecalcular } from '../hooks/useProyecto'
import type { Combustible } from '../types'

const { Title } = Typography
const fmt = (n: number) => n.toLocaleString('es-AR', { maximumFractionDigits: 2 })
const EMPTY: Combustible = { descripcion: '', unidad: 'lts', moneda: '$AR', proveedor: '', costo_origen: 0, otros: 0, costo: 0 }

export default function Combustibles() {
  const { id } = useParams<{ id: string }>()
  const pid = Number(id)
  const { data: rec, isLoading } = useProyecto(pid)
  const patch = usePatch(pid)
  const recalc = useRecalcular(pid)
  const [rows, setRows] = useState<Combustible[]>([])
  const [init, setInit] = useState(false)

  if (isLoading || !rec) return <Spin />
  if (!init) { setRows(rec.estado.combustibles); setInit(true) }

  const upd = (i: number, f: keyof Combustible, v: unknown) =>
    setRows(prev => prev.map((r, j) => j === i ? { ...r, [f]: v } : r))

  const guardar = async () => {
    await patch.mutateAsync({ seccion: 'combustibles', data: rows })
    await recalc.mutateAsync()
    message.success('Combustibles guardados y recalculados.')
  }

  const cols: ColumnsType<Combustible> = [
    { title: 'Descripción', dataIndex: 'descripcion', width: 180,
      render: (v, _, i) => <input className="ant-input ant-input-sm" style={{ width: 170 }} value={v} onChange={e => upd(i, 'descripcion', e.target.value)} /> },
    { title: 'Unidad', dataIndex: 'unidad', width: 80,
      render: (v, _, i) => <input className="ant-input ant-input-sm" style={{ width: 70 }} value={v} onChange={e => upd(i, 'unidad', e.target.value)} /> },
    { title: 'Proveedor', dataIndex: 'proveedor', width: 140,
      render: (v, _, i) => <input className="ant-input ant-input-sm" style={{ width: 130 }} value={v} onChange={e => upd(i, 'proveedor', e.target.value)} /> },
    { title: 'Costo origen', dataIndex: 'costo_origen', width: 120,
      render: (v, _, i) => <InputNumber size="small" style={{ width: 110 }} value={v} step={10} onChange={val => upd(i, 'costo_origen', val ?? 0)} /> },
    { title: 'Otros', dataIndex: 'otros', width: 100,
      render: (v, _, i) => <InputNumber size="small" style={{ width: 90 }} value={v} onChange={val => upd(i, 'otros', val ?? 0)} /> },
    { title: 'COSTO', dataIndex: 'costo', width: 100, align: 'right',
      render: v => <strong>{fmt(v)}</strong> },
    { title: '', width: 40, render: (_, __, i) =>
      <Popconfirm title="¿Eliminar?" onConfirm={() => setRows(prev => prev.filter((_, j) => j !== i))}>
        <Button size="small" danger icon={<DeleteOutlined />} />
      </Popconfirm> },
  ]

  return (
    <>
      <Title level={3}>⛽ Combustibles</Title>
      <Space style={{ marginBottom: 8 }}>
        <Button icon={<PlusOutlined />} onClick={() => setRows(prev => [...prev, { ...EMPTY }])}>Agregar</Button>
        <Button type="primary" icon={<SyncOutlined />} onClick={guardar} loading={patch.isPending || recalc.isPending}>
          Guardar y Recalcular
        </Button>
      </Space>
      <Table dataSource={rows} columns={cols} rowKey={(_, i) => String(i)} size="small" pagination={false} />
    </>
  )
}
