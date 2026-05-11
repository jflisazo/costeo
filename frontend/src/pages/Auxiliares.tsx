import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Alert, Button, Collapse, Input, Popconfirm, Space, Spin, Table, Typography, message,
} from 'antd'
import { PlusOutlined, DeleteOutlined, SyncOutlined, EditOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { useProyecto, usePatch, useRecalcular } from '../hooks/useProyecto'
import type { Auxiliar, DatoCD } from '../types'

const { Title, Text } = Typography
const fmt = (n: number) => n.toLocaleString('es-AR', { maximumFractionDigits: 4 })

export default function Auxiliares() {
  const { id } = useParams<{ id: string }>()
  const pid = Number(id)
  const navigate = useNavigate()
  const { data: rec, isLoading } = useProyecto(pid)
  const patch = usePatch(pid)
  const recalc = useRecalcular(pid)
  const [rows, setRows] = useState<Auxiliar[]>([])
  const [init, setInit] = useState(false)

  if (isLoading || !rec) return <Spin />
  if (!init) { setRows(rec.estado.auxiliares); setInit(true) }

  const datosCD = rec.estado.datos_cd

  const recursosDe = (desc: string): DatoCD[] =>
    datosCD.filter(d => d.item_aux === 'Aux' && d.item_id === desc)

  const guardar = async () => {
    await patch.mutateAsync({ seccion: 'auxiliares', data: rows })
    await recalc.mutateAsync()
    message.success('Auxiliares guardados y recalculados.')
  }

  const recCols: ColumnsType<DatoCD> = [
    { title: 'Tarea', dataIndex: 'tarea', width: 130 },
    { title: 'Uni', dataIndex: 'tarea_unidad', width: 60 },
    { title: 'Incid.', dataIndex: 'incidencia', width: 70, align: 'right',
      render: v => fmt(v) },
    { title: 'Rendim.', dataIndex: 'rendimiento', width: 80, align: 'right',
      render: v => fmt(v) },
    { title: 'Tipo', dataIndex: 'tipo_recurso', width: 130 },
    { title: 'Recurso', dataIndex: 'recurso', width: 180 },
    { title: 'Cuantía', dataIndex: 'cuantia', width: 80, align: 'right',
      render: v => fmt(v) },
    { title: 'Q/unid', dataIndex: 'cuantia_por_unidad', width: 90, align: 'right',
      render: v => fmt(v) },
    { title: 'CU $', dataIndex: 'costo_unitario', width: 90, align: 'right',
      render: v => <strong>{fmt(v)}</strong> },
  ]

  const items = rows.map((aux, ai) => {
    const recursos = recursosDe(aux.descripcion)
    return {
      key: String(ai),
      label: (
        <span>
          <strong>{aux.descripcion || '(sin nombre)'}</strong>
          {' · '}{aux.unidad}
          {' · costo: '}<strong>{fmt(aux.costo)}</strong>
          <Popconfirm title="¿Eliminar auxiliar?" onConfirm={() => setRows(prev => prev.filter((_, i) => i !== ai))}>
            <Button size="small" danger type="link" icon={<DeleteOutlined />}
              onClick={e => e.stopPropagation()} style={{ marginLeft: 8 }} />
          </Popconfirm>
        </span>
      ),
      children: (
        <>
          <Space style={{ marginBottom: 8 }}>
            <Input size="small" style={{ width: 220 }} placeholder="Descripción" value={aux.descripcion}
              onChange={e => setRows(prev => prev.map((a, i) => i === ai ? { ...a, descripcion: e.target.value } : a))} />
            <Input size="small" style={{ width: 90 }} placeholder="Unidad" value={aux.unidad}
              onChange={e => setRows(prev => prev.map((a, i) => i === ai ? { ...a, unidad: e.target.value } : a))} />
            <Button size="small" icon={<EditOutlined />} onClick={() => navigate(`/p/${pid}/items`)}>
              Editar recursos en Datos CD
            </Button>
          </Space>
          {recursos.length === 0
            ? <Text type="secondary">Sin recursos cargados. Agregalos en la página de Datos CD (filtro "Aux").</Text>
            : <Table dataSource={recursos} columns={recCols}
                rowKey={r => `${r.item_id}|${r.tarea}|${r.tipo_recurso}|${r.recurso}`}
                size="small" pagination={false} scroll={{ x: 1050 }} />}
        </>
      ),
    }
  })

  return (
    <>
      <Title level={3}>⚗️ Auxiliares y Elaborados</Title>
      <Alert type="info" showIcon style={{ marginBottom: 12 }}
        message="Los recursos de cada auxiliar se editan ahora en la página de Datos CD (filtro Aux)."
        description="Acá podés crear/eliminar auxiliares y cambiarles nombre o unidad." />
      <Space style={{ marginBottom: 12 }}>
        <Button icon={<PlusOutlined />}
          onClick={() => setRows(prev => [...prev, { tipo: 'Auxiliar', descripcion: '', unidad: '', recursos: [], costo: 0 }])}>
          Agregar auxiliar
        </Button>
        <Button type="primary" icon={<SyncOutlined />}
          onClick={guardar} loading={patch.isPending || recalc.isPending}>
          Guardar y Recalcular
        </Button>
      </Space>
      <Collapse items={items} />
    </>
  )
}
