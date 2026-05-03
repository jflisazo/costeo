import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { Button, InputNumber, Popconfirm, Select, Space, Spin, Table, Typography, message } from 'antd'
import { PlusOutlined, DeleteOutlined, SyncOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { useProyecto, usePatch, useRecalcular } from '../hooks/useProyecto'
import type { Material } from '../types'

const { Title } = Typography
const fmt = (n: number) => n.toLocaleString('es-AR', { maximumFractionDigits: 2 })

const EMPTY: Material = {
  numero: 0, descripcion: '', unidad: '', moneda: '$AR', proveedor: '', origen: '',
  distancia_km: 0, costo_origen: 0, costo_flete: 0, otros: 0, perc_perdida: 0, costo: 0,
}

export default function Materiales() {
  const { id } = useParams<{ id: string }>()
  const pid = Number(id)
  const { data: rec, isLoading } = useProyecto(pid)
  const patch = usePatch(pid)
  const recalc = useRecalcular(pid)
  const [rows, setRows] = useState<Material[]>([])
  const [init, setInit] = useState(false)

  if (isLoading || !rec) return <Spin />
  if (!init) { setRows(rec.estado.materiales); setInit(true) }

  const upd = (i: number, f: keyof Material, v: unknown) =>
    setRows(prev => prev.map((r, j) => j === i ? { ...r, [f]: v } : r))

  const guardar = async () => {
    await patch.mutateAsync({ seccion: 'materiales', data: rows })
    await recalc.mutateAsync()
    message.success('Materiales guardados y recalculados.')
  }

  const cols: ColumnsType<Material> = [
    { title: '#', dataIndex: 'numero', width: 50,
      render: (v, _, i) => <InputNumber size="small" style={{ width: 50 }} value={v} onChange={val => upd(i, 'numero', val ?? 0)} /> },
    { title: 'Descripción', dataIndex: 'descripcion', width: 200,
      render: (v, _, i) => <input className="ant-input ant-input-sm" style={{ width: 190 }} value={v} onChange={e => upd(i, 'descripcion', e.target.value)} /> },
    { title: 'Unid.', dataIndex: 'unidad', width: 70,
      render: (v, _, i) => <input className="ant-input ant-input-sm" style={{ width: 60 }} value={v} onChange={e => upd(i, 'unidad', e.target.value)} /> },
    { title: 'Mon.', dataIndex: 'moneda', width: 80,
      render: (v, _, i) => (
        <Select size="small" style={{ width: 75 }} value={v} onChange={val => upd(i, 'moneda', val)}
          options={['$AR','USD','EUR'].map(m => ({ value: m }))} />
      ) },
    { title: 'Costo origen', dataIndex: 'costo_origen', width: 110,
      render: (v, _, i) => <InputNumber size="small" style={{ width: 100 }} value={v} step={10} onChange={val => upd(i, 'costo_origen', val ?? 0)} /> },
    { title: 'Dist. km', dataIndex: 'distancia_km', width: 90,
      render: (v, _, i) => <InputNumber size="small" style={{ width: 80 }} value={v} onChange={val => upd(i, 'distancia_km', val ?? 0)} /> },
    { title: 'Flete $/km', dataIndex: 'costo_flete', width: 100,
      render: (v, _, i) => <InputNumber size="small" style={{ width: 90 }} value={v} step={10} onChange={val => upd(i, 'costo_flete', val ?? 0)} /> },
    { title: 'Otros', dataIndex: 'otros', width: 90,
      render: (v, _, i) => <InputNumber size="small" style={{ width: 80 }} value={v} onChange={val => upd(i, 'otros', val ?? 0)} /> },
    { title: '% Pérdida', dataIndex: 'perc_perdida', width: 90,
      render: (v, _, i) => <InputNumber size="small" style={{ width: 80 }} value={v} step={0.5} onChange={val => upd(i, 'perc_perdida', val ?? 0)} /> },
    { title: 'COSTO', dataIndex: 'costo', width: 100, align: 'right',
      render: v => <strong>{fmt(v)}</strong> },
    { title: '', width: 40, render: (_, __, i) =>
      <Popconfirm title="¿Eliminar?" onConfirm={() => setRows(prev => prev.filter((_, j) => j !== i))}>
        <Button size="small" danger icon={<DeleteOutlined />} />
      </Popconfirm> },
  ]

  return (
    <>
      <Title level={3}>📦 Materiales</Title>
      <Space style={{ marginBottom: 8 }}>
        <Button icon={<PlusOutlined />} onClick={() => setRows(prev => [...prev, { ...EMPTY }])}>Agregar</Button>
        <Button type="primary" icon={<SyncOutlined />} onClick={guardar} loading={patch.isPending || recalc.isPending}>
          Guardar y Recalcular
        </Button>
      </Space>
      <Table dataSource={rows} columns={cols} rowKey={(_, i) => String(i)} size="small" pagination={false} scroll={{ x: 1000 }} />
    </>
  )
}
