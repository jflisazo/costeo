import { useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  Button, Collapse, InputNumber, Popconfirm, Select,
  Space, Spin, Table, Typography, message,
} from 'antd'
import { PlusOutlined, DeleteOutlined, SyncOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { useProyecto, usePatch, useRecalcular } from '../hooks/useProyecto'
import type { Auxiliar, RecursoAux } from '../types'

const { Title } = Typography
const fmt = (n: number) => n.toLocaleString('es-AR', { maximumFractionDigits: 4 })
const TIPOS = ['Equipos', 'Mano de Obra', 'Materiales', 'Combustibles', 'Subcontratos', 'Auxiliares', 'Tpte Interno']

const EMPTY_REC: RecursoAux = {
  tarea: '', tarea_unidad: '', incidencia: 1, rendimiento: 1,
  tipo_recurso: 'Materiales', recurso: '', cuantia: 0, comentario: '',
  cuantia_por_unidad: 0, costo_unitario: 0,
}

export default function Auxiliares() {
  const { id } = useParams<{ id: string }>()
  const pid = Number(id)
  const { data: rec, isLoading } = useProyecto(pid)
  const patch = usePatch(pid)
  const recalc = useRecalcular(pid)
  const [rows, setRows] = useState<Auxiliar[]>([])
  const [init, setInit] = useState(false)

  if (isLoading || !rec) return <Spin />
  if (!init) { setRows(rec.estado.auxiliares); setInit(true) }

  const guardar = async () => {
    await patch.mutateAsync({ seccion: 'auxiliares', data: rows })
    await recalc.mutateAsync()
    message.success('Auxiliares guardados y recalculados.')
  }

  const updRec = (auxIdx: number, recIdx: number, f: keyof RecursoAux, v: unknown) =>
    setRows(prev => prev.map((a, ai) => {
      if (ai !== auxIdx) return a
      return { ...a, recursos: a.recursos.map((r, ri) => ri === recIdx ? { ...r, [f]: v } : r) }
    }))

  const addRec = (auxIdx: number) =>
    setRows(prev => prev.map((a, ai) =>
      ai === auxIdx ? { ...a, recursos: [...a.recursos, { ...EMPTY_REC }] } : a))

  const delRec = (auxIdx: number, recIdx: number) =>
    setRows(prev => prev.map((a, ai) =>
      ai === auxIdx ? { ...a, recursos: a.recursos.filter((_, ri) => ri !== recIdx) } : a))

  const recCols = (auxIdx: number): ColumnsType<RecursoAux> => [
    { title: 'Tarea', dataIndex: 'tarea', width: 130,
      render: (v, _, i) => <input className="ant-input ant-input-sm" style={{ width: 120 }} value={v} onChange={e => updRec(auxIdx, i, 'tarea', e.target.value)} /> },
    { title: 'Tipo recurso', dataIndex: 'tipo_recurso', width: 140,
      render: (v, _, i) => <Select size="small" style={{ width: 130 }} value={v} onChange={val => updRec(auxIdx, i, 'tipo_recurso', val)} options={TIPOS.map(t => ({ value: t }))} /> },
    { title: 'Recurso', dataIndex: 'recurso', width: 160,
      render: (v, _, i) => <input className="ant-input ant-input-sm" style={{ width: 150 }} value={v} onChange={e => updRec(auxIdx, i, 'recurso', e.target.value)} /> },
    { title: 'Cuantía', dataIndex: 'cuantia', width: 90,
      render: (v, _, i) => <InputNumber size="small" style={{ width: 80 }} value={v} step={0.1} onChange={val => updRec(auxIdx, i, 'cuantia', val ?? 0)} /> },
    { title: 'Rendim.', dataIndex: 'rendimiento', width: 90,
      render: (v, _, i) => <InputNumber size="small" style={{ width: 80 }} value={v} step={0.1} onChange={val => updRec(auxIdx, i, 'rendimiento', val ?? 1)} /> },
    { title: 'Incid.', dataIndex: 'incidencia', width: 80,
      render: (v, _, i) => <InputNumber size="small" style={{ width: 70 }} value={v} step={0.1} onChange={val => updRec(auxIdx, i, 'incidencia', val ?? 1)} /> },
    { title: 'CU', dataIndex: 'costo_unitario', width: 90, align: 'right', render: v => fmt(v) },
    { title: '', width: 40, render: (_, __, i) =>
      <Popconfirm title="¿Eliminar?" onConfirm={() => delRec(auxIdx, i)}>
        <Button size="small" danger icon={<DeleteOutlined />} />
      </Popconfirm> },
  ]

  const items = rows.map((aux, ai) => ({
    key: String(ai),
    label: (
      <span>
        <strong>{aux.descripcion || '(sin nombre)'}</strong>
        {' · '}{aux.unidad}
        {' · costo: '}<strong>{fmt(aux.costo)}</strong>
        <Popconfirm title="¿Eliminar auxiliar?" onConfirm={() => setRows(prev => prev.filter((_, i) => i !== ai))}>
          <Button size="small" danger type="link" icon={<DeleteOutlined />} onClick={e => e.stopPropagation()} style={{ marginLeft: 8 }} />
        </Popconfirm>
      </span>
    ),
    children: (
      <>
        <Space style={{ marginBottom: 8 }}>
          <input className="ant-input ant-input-sm" style={{ width: 180 }} placeholder="Descripción" value={aux.descripcion}
            onChange={e => setRows(prev => prev.map((a, i) => i === ai ? { ...a, descripcion: e.target.value } : a))} />
          <input className="ant-input ant-input-sm" style={{ width: 80 }} placeholder="Unidad" value={aux.unidad}
            onChange={e => setRows(prev => prev.map((a, i) => i === ai ? { ...a, unidad: e.target.value } : a))} />
          <Button size="small" icon={<PlusOutlined />} onClick={() => addRec(ai)}>Agregar recurso</Button>
        </Space>
        <Table dataSource={aux.recursos} columns={recCols(ai)} rowKey={(_, i) => String(i)} size="small" pagination={false} scroll={{ x: 750 }} />
      </>
    ),
  }))

  return (
    <>
      <Title level={3}>⚗️ Auxiliares y Elaborados</Title>
      <Space style={{ marginBottom: 12 }}>
        <Button icon={<PlusOutlined />} onClick={() => setRows(prev => [...prev, { tipo: 'Auxiliar', descripcion: '', unidad: '', recursos: [], costo: 0 }])}>
          Agregar auxiliar
        </Button>
        <Button type="primary" icon={<SyncOutlined />} onClick={guardar} loading={patch.isPending || recalc.isPending}>
          Guardar y Recalcular
        </Button>
      </Space>
      <Collapse items={items} />
    </>
  )
}
