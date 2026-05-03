import { useParams } from 'react-router-dom'
import { Button, InputNumber, Space, Spin, Table, Tabs, Typography, Popconfirm, message } from 'antd'
import { PlusOutlined, DeleteOutlined, SyncOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { useProyecto, usePatch, useRecalcular } from '../hooks/useProyecto'
import type { MOJornalizada, MOMensualizada } from '../types'
import { useState } from 'react'

const { Title } = Typography
const fmt = (n: number) => n.toLocaleString('es-AR', { maximumFractionDigits: 2 })

function useInlineEdit<T>(initial: T[]) {
  const [data, setData] = useState<T[]>(initial)
  const update = (idx: number, field: keyof T, val: unknown) => {
    setData(prev => prev.map((r, i) => i === idx ? { ...r, [field]: val } : r))
  }
  return { data, setData, update }
}

export default function ManoDeObra() {
  const { id } = useParams<{ id: string }>()
  const pid = Number(id)
  const { data: rec, isLoading } = useProyecto(pid)
  const patch = usePatch(pid)
  const recalc = useRecalcular(pid)

  if (isLoading || !rec) return <Spin />

  return (
    <>
      <Title level={3}>👷 Mano de Obra</Title>
      <Tabs items={[
        { key: 'jorn', label: 'Jornalizada', children: <TabJorn pid={pid} rec={rec} patch={patch} recalc={recalc} /> },
        { key: 'mens', label: 'Mensualizada', children: <TabMens pid={pid} rec={rec} patch={patch} recalc={recalc} /> },
      ]} />
    </>
  )
}

function TabJorn({ pid, rec, patch, recalc }: any) {
  const [rows, setRows] = useState<MOJornalizada[]>(rec.estado.mo_jornalizada)

  const upd = (idx: number, f: keyof MOJornalizada, v: unknown) =>
    setRows(prev => prev.map((r, i) => i === idx ? { ...r, [f]: v } : r))

  const addRow = () => setRows(prev => [...prev, {
    funcion: '', id: 0, moneda: '$AR', bruto: 0, aguinaldo: 0,
    vacaciones: 0, cargas_sociales: 0, bolsillo: 0, viatico: 0,
    horas_mes: 200, costo_hora: 0,
  }])

  const del = (idx: number) => setRows(prev => prev.filter((_, i) => i !== idx))

  const guardar = async () => {
    await patch.mutateAsync({ seccion: 'mo_jornalizada', data: rows })
    await recalc.mutateAsync()
    message.success('MO jornalizada guardada y recalculada.')
  }

  const cols: ColumnsType<MOJornalizada> = [
    { title: 'Función', dataIndex: 'funcion', width: 160,
      render: (v, _, i) => <input className="ant-input ant-input-sm" value={v} onChange={e => upd(i, 'funcion', e.target.value)} /> },
    { title: 'Bruto/mes', dataIndex: 'bruto', width: 110,
      render: (v, _, i) => <InputNumber size="small" style={{ width: '100%' }} value={v} onChange={val => upd(i, 'bruto', val ?? 0)} /> },
    { title: 'Aguinaldo', dataIndex: 'aguinaldo', width: 110,
      render: (v, _, i) => <InputNumber size="small" style={{ width: '100%' }} value={v} onChange={val => upd(i, 'aguinaldo', val ?? 0)} /> },
    { title: 'Vacaciones', dataIndex: 'vacaciones', width: 110,
      render: (v, _, i) => <InputNumber size="small" style={{ width: '100%' }} value={v} onChange={val => upd(i, 'vacaciones', val ?? 0)} /> },
    { title: 'Cargas Soc.', dataIndex: 'cargas_sociales', width: 110,
      render: (v, _, i) => <InputNumber size="small" style={{ width: '100%' }} value={v} onChange={val => upd(i, 'cargas_sociales', val ?? 0)} /> },
    { title: 'Viático', dataIndex: 'viatico', width: 100,
      render: (v, _, i) => <InputNumber size="small" style={{ width: '100%' }} value={v} onChange={val => upd(i, 'viatico', val ?? 0)} /> },
    { title: 'HS/mes', dataIndex: 'horas_mes', width: 80,
      render: (v, _, i) => <InputNumber size="small" style={{ width: '100%' }} value={v} onChange={val => upd(i, 'horas_mes', val ?? 200)} /> },
    { title: '$/hs', dataIndex: 'costo_hora', width: 90, align: 'right',
      render: v => <strong>{fmt(v)}</strong> },
    { title: '', width: 40, render: (_, __, i) =>
      <Popconfirm title="¿Eliminar?" onConfirm={() => del(i)}><Button size="small" danger icon={<DeleteOutlined />} /></Popconfirm> },
  ]

  return (
    <>
      <Space style={{ marginBottom: 8 }}>
        <Button icon={<PlusOutlined />} onClick={addRow}>Agregar</Button>
        <Button type="primary" icon={<SyncOutlined />} onClick={guardar} loading={patch.isPending || recalc.isPending}>
          Guardar y Recalcular
        </Button>
      </Space>
      <Table dataSource={rows} columns={cols} rowKey={(_, i) => String(i)} size="small" pagination={false} scroll={{ x: 800 }} />
    </>
  )
}

function TabMens({ pid, rec, patch, recalc }: any) {
  const [rows, setRows] = useState<MOMensualizada[]>(rec.estado.mo_mensualizada)

  const upd = (idx: number, f: keyof MOMensualizada, v: unknown) =>
    setRows(prev => prev.map((r, i) => i === idx ? { ...r, [f]: v } : r))

  const addRow = () => setRows(prev => [...prev, {
    funcion: '', moneda: '$AR', neto: 0, bruto: 0, aguinaldo: 0,
    dias_vacaciones: 14, vacaciones: 0, cargas_sociales: 0, prop_despido: 0, costo_mes: 0,
  }])

  const del = (idx: number) => setRows(prev => prev.filter((_, i) => i !== idx))

  const guardar = async () => {
    await patch.mutateAsync({ seccion: 'mo_mensualizada', data: rows })
    await recalc.mutateAsync()
    message.success('MO mensualizada guardada y recalculada.')
  }

  const cols: ColumnsType<MOMensualizada> = [
    { title: 'Función', dataIndex: 'funcion', width: 160,
      render: (v, _, i) => <input className="ant-input ant-input-sm" value={v} onChange={e => upd(i, 'funcion', e.target.value)} /> },
    { title: 'Bruto/mes', dataIndex: 'bruto', width: 110,
      render: (v, _, i) => <InputNumber size="small" style={{ width: '100%' }} value={v} onChange={val => upd(i, 'bruto', val ?? 0)} /> },
    { title: 'Aguinaldo', dataIndex: 'aguinaldo', width: 110,
      render: (v, _, i) => <InputNumber size="small" style={{ width: '100%' }} value={v} onChange={val => upd(i, 'aguinaldo', val ?? 0)} /> },
    { title: 'Vacaciones', dataIndex: 'vacaciones', width: 110,
      render: (v, _, i) => <InputNumber size="small" style={{ width: '100%' }} value={v} onChange={val => upd(i, 'vacaciones', val ?? 0)} /> },
    { title: 'Cargas Soc.', dataIndex: 'cargas_sociales', width: 110,
      render: (v, _, i) => <InputNumber size="small" style={{ width: '100%' }} value={v} onChange={val => upd(i, 'cargas_sociales', val ?? 0)} /> },
    { title: 'Prop. despido', dataIndex: 'prop_despido', width: 110,
      render: (v, _, i) => <InputNumber size="small" style={{ width: '100%' }} value={v} onChange={val => upd(i, 'prop_despido', val ?? 0)} /> },
    { title: '$/mes', dataIndex: 'costo_mes', width: 100, align: 'right',
      render: v => <strong>{fmt(v)}</strong> },
    { title: '', width: 40, render: (_, __, i) =>
      <Popconfirm title="¿Eliminar?" onConfirm={() => del(i)}><Button size="small" danger icon={<DeleteOutlined />} /></Popconfirm> },
  ]

  return (
    <>
      <Space style={{ marginBottom: 8 }}>
        <Button icon={<PlusOutlined />} onClick={addRow}>Agregar</Button>
        <Button type="primary" icon={<SyncOutlined />} onClick={guardar} loading={patch.isPending || recalc.isPending}>
          Guardar y Recalcular
        </Button>
      </Space>
      <Table dataSource={rows} columns={cols} rowKey={(_, i) => String(i)} size="small" pagination={false} scroll={{ x: 800 }} />
    </>
  )
}
