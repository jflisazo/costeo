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
  cantidad: 1, mes_inicio: 1, meses: 1, amort_perc: 1.0, costo_unitario: 0, comentario: '', total: 0,
}

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

  const guardar = async () => {
    await patch.mutateAsync({ seccion: 'gastos_generales', data: rows })
    await recalc.mutateAsync()
    message.success('Gastos generales guardados y recalculados.')
  }

  const totalGG = rows.filter(r => r.tipo === 'Item').reduce((s, r) => s + r.total, 0)

  const cols: ColumnsType<GastoGeneral> = [
    { title: 'Tipo', dataIndex: 'tipo', width: 80,
      render: (v, _, i) => (
        <Select size="small" style={{ width: 74 }} value={v} onChange={val => upd(i, 'tipo', val)}
          options={[{ value: 'Título' }, { value: 'Item' }]} />
      ) },
    { title: 'Categoría', dataIndex: 'categoria', width: 140,
      render: (v, row, i) => row.tipo === 'Título'
        ? <Text strong>{v || '(título)'}</Text>
        : <input className="ant-input ant-input-sm" style={{ width: 130 }} value={v} onChange={e => upd(i, 'categoria', e.target.value)} /> },
    { title: 'Recurso', dataIndex: 'recurso', width: 180,
      render: (v, row, i) => row.tipo === 'Item'
        ? <input className="ant-input ant-input-sm" style={{ width: 170 }} value={v} onChange={e => upd(i, 'recurso', e.target.value)} />
        : null },
    { title: 'Unid.', dataIndex: 'unidad', width: 70,
      render: (v, row, i) => row.tipo === 'Item'
        ? <input className="ant-input ant-input-sm" style={{ width: 60 }} value={v} onChange={e => upd(i, 'unidad', e.target.value)} />
        : null },
    { title: 'CU', dataIndex: 'costo_unitario', width: 110,
      render: (v, row, i) => row.tipo === 'Item'
        ? <InputNumber size="small" style={{ width: 100 }} value={v} step={100} onChange={val => upd(i, 'costo_unitario', val ?? 0)} />
        : null },
    { title: 'Cant.', dataIndex: 'cantidad', width: 80,
      render: (v, row, i) => row.tipo === 'Item'
        ? <InputNumber size="small" style={{ width: 70 }} value={v} step={1} onChange={val => upd(i, 'cantidad', val ?? 1)} />
        : null },
    { title: 'Meses', dataIndex: 'meses', width: 75,
      render: (v, row, i) => row.tipo === 'Item'
        ? <InputNumber size="small" style={{ width: 65 }} value={v} step={1} onChange={val => upd(i, 'meses', val ?? 1)} />
        : null },
    { title: 'Amort.%', dataIndex: 'amort_perc', width: 85,
      render: (v, row, i) => row.tipo === 'Item'
        ? <InputNumber size="small" style={{ width: 75 }} value={v * 100} step={10}
            onChange={val => upd(i, 'amort_perc', (val ?? 100) / 100)} />
        : null },
    { title: 'TOTAL', dataIndex: 'total', width: 110, align: 'right',
      render: (v, row) => row.tipo === 'Item' ? <strong>{fmt(v)}</strong> : null },
    { title: '', width: 40, render: (_, __, i) =>
      <Popconfirm title="¿Eliminar?" onConfirm={() => setRows(prev => prev.filter((_, j) => j !== i))}>
        <Button size="small" danger icon={<DeleteOutlined />} />
      </Popconfirm> },
  ]

  return (
    <>
      <Title level={3}>💰 Gastos Generales</Title>
      <Space style={{ marginBottom: 8 }} wrap>
        <Button icon={<PlusOutlined />} onClick={() => setRows(prev => [...prev, { ...EMPTY, id: Date.now() }])}>
          Agregar ítem
        </Button>
        <Button type="primary" icon={<SyncOutlined />} onClick={guardar} loading={patch.isPending || recalc.isPending}>
          Guardar y Recalcular
        </Button>
        <Tag color="blue">Total GG: ${fmt(totalGG)}</Tag>
      </Space>
      <Table
        dataSource={rows}
        columns={cols}
        rowKey={(_, i) => String(i)}
        size="small"
        pagination={false}
        scroll={{ x: 950 }}
        rowClassName={row => row.tipo === 'Título' ? 'row-titulo' : ''}
        summary={() => (
          <Table.Summary.Row>
            <Table.Summary.Cell index={0} colSpan={8} align="right"><strong>Total GG:</strong></Table.Summary.Cell>
            <Table.Summary.Cell index={8} align="right"><strong>${fmt(totalGG)}</strong></Table.Summary.Cell>
            <Table.Summary.Cell index={9} />
          </Table.Summary.Row>
        )}
      />
    </>
  )
}
