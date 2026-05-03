import { useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  Button, Col, Divider, InputNumber, Popconfirm, Row, Select,
  Space, Spin, Table, Tag, Typography, message,
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
  const t = tipo.toLowerCase()
  if (t.includes('equipo'))       return estado.equipos.map(e => e.nombre)
  if (t.includes('mano') || t.includes('mo')) return [
    ...estado.mo_jornalizada.map(m => m.funcion),
    ...estado.mo_mensualizada.map(m => m.funcion),
  ]
  if (t.includes('material'))     return estado.materiales.map(m => m.descripcion)
  if (t.includes('combustible'))  return estado.combustibles.map(c => c.descripcion)
  if (t.includes('subcontrat'))   return estado.subcontratos.map(s => s.descripcion)
  if (t.includes('auxiliar') || t.includes('elaborado')) return estado.auxiliares.map(a => a.descripcion)
  if (t.includes('tpte') || t.includes('transport'))     return estado.transportes.map(t => t.descripcion)
  return []
}

const EMPTY_CD: DatoCD = {
  item_id: '', tarea: '', tarea_unidad: '', incidencia: 1, rendimiento: 1,
  tipo_recurso: 'Equipos', recurso: '', cuantia: 0, comentario: '',
  cuantia_por_unidad: 0, costo_unitario: 0,
}

export default function Items() {
  const { id } = useParams<{ id: string }>()
  const pid = Number(id)
  const { data: rec, isLoading } = useProyecto(pid)
  const patch = usePatch(pid)
  const recalc = useRecalcular(pid)

  const [selectedItem, setSelectedItem] = useState<string | null>(null)
  const [cdRows, setCdRows] = useState<DatoCD[]>([])
  const [cdInit, setCdInit] = useState(false)

  if (isLoading || !rec) return <Spin />

  const { items, datos_cd } = rec.estado

  if (!cdInit) { setCdRows(datos_cd); setCdInit(true) }

  const selectedCD = cdRows.filter(d => d.item_id === selectedItem)

  const updCD = (i: number, f: keyof DatoCD, v: unknown) => {
    const globalIdx = cdRows.indexOf(selectedCD[i])
    setCdRows(prev => prev.map((r, j) => j === globalIdx ? { ...r, [f]: v } : r))
  }

  const addCD = () => {
    if (!selectedItem) return
    setCdRows(prev => [...prev, { ...EMPTY_CD, item_id: selectedItem }])
  }

  const delCD = (i: number) => {
    const globalIdx = cdRows.indexOf(selectedCD[i])
    setCdRows(prev => prev.filter((_, j) => j !== globalIdx))
  }

  const guardarCD = async () => {
    await patch.mutateAsync({ seccion: 'datos_cd', data: cdRows })
    const result = await recalc.mutateAsync()
    setCdRows(result.estado.datos_cd)
    message.success('Datos CD guardados y recalculados.')
  }

  const itemCols: ColumnsType<Item> = [
    { title: '#', dataIndex: 'numero', width: 130, ellipsis: true,
      render: (v, row) => row.tipo === 'Título'
        ? <Text strong style={{ color: '#1677ff' }}>{v}</Text>
        : <Text code style={{ fontSize: 11 }}>{v}</Text> },
    { title: 'Descripción', dataIndex: 'descripcion', ellipsis: true,
      render: (v, row) => row.tipo === 'Título'
        ? <Text strong>{v}</Text>
        : v },
    { title: 'Unid.', dataIndex: 'unidad', width: 60 },
    { title: 'Cantidad', dataIndex: 'cantidad', width: 90, align: 'right', render: v => fmt(v) },
    { title: 'CU Costo', dataIndex: 'costo_unitario', width: 110, align: 'right', render: v => fmt(v) },
    { title: 'Total Costo', dataIndex: 'costo_total', width: 120, align: 'right',
      render: v => <strong>{fmt(v)}</strong> },
    { title: 'CU Precio', dataIndex: 'precio_unitario', width: 110, align: 'right', render: v => fmt(v) },
    { title: 'Total Precio', dataIndex: 'precio_total', width: 120, align: 'right',
      render: v => <Text type="success"><strong>{fmt(v)}</strong></Text> },
  ]

  const cdCols = (estado: ProyectoEstado): ColumnsType<DatoCD> => [
    { title: 'Tarea', dataIndex: 'tarea', width: 130,
      render: (v, _, i) => <input className="ant-input ant-input-sm" style={{ width: 120 }} value={v} onChange={e => updCD(i, 'tarea', e.target.value)} /> },
    { title: 'Unid.', dataIndex: 'tarea_unidad', width: 70,
      render: (v, _, i) => <input className="ant-input ant-input-sm" style={{ width: 60 }} value={v} onChange={e => updCD(i, 'tarea_unidad', e.target.value)} /> },
    { title: 'Incid.', dataIndex: 'incidencia', width: 80,
      render: (v, _, i) => <InputNumber size="small" style={{ width: 70 }} value={v} step={0.1} onChange={val => updCD(i, 'incidencia', val ?? 1)} /> },
    { title: 'Rendim.', dataIndex: 'rendimiento', width: 90,
      render: (v, _, i) => <InputNumber size="small" style={{ width: 80 }} value={v} step={0.5} onChange={val => updCD(i, 'rendimiento', val ?? 1)} /> },
    { title: 'Tipo recurso', dataIndex: 'tipo_recurso', width: 140,
      render: (v, _, i) => (
        <Select size="small" style={{ width: 130 }} value={v}
          onChange={val => { updCD(i, 'tipo_recurso', val); updCD(i, 'recurso', '') }}
          options={TIPOS_RECURSO.map(t => ({ value: t }))} />
      ) },
    { title: 'Recurso', dataIndex: 'recurso', width: 170,
      render: (v, row, i) => {
        const opts = recursosOpciones(row.tipo_recurso, estado)
        return opts.length > 0
          ? <Select size="small" style={{ width: 160 }} value={v || undefined} showSearch
              onChange={val => updCD(i, 'recurso', val)}
              options={opts.map(o => ({ value: o, label: o }))} />
          : <input className="ant-input ant-input-sm" style={{ width: 160 }} value={v} onChange={e => updCD(i, 'recurso', e.target.value)} />
      } },
    { title: 'Cuantía/día', dataIndex: 'cuantia', width: 100,
      render: (v, _, i) => <InputNumber size="small" style={{ width: 90 }} value={v} step={0.1} onChange={val => updCD(i, 'cuantia', val ?? 0)} /> },
    { title: 'Q/unid', dataIndex: 'cuantia_por_unidad', width: 90, align: 'right', render: v => fmt4(v) },
    { title: 'CU $/unid', dataIndex: 'costo_unitario', width: 100, align: 'right',
      render: v => <strong>{fmt4(v)}</strong> },
    { title: '', width: 40, render: (_, __, i) =>
      <Popconfirm title="¿Eliminar fila?" onConfirm={() => delCD(i)}>
        <Button size="small" danger icon={<DeleteOutlined />} />
      </Popconfirm> },
  ]

  const costoCD = items.filter(i => i.tipo === 'Item').reduce((s, i) => s + i.costo_total, 0)
  const precioTotal = items.filter(i => i.tipo === 'Item').reduce((s, i) => s + i.precio_total, 0)

  return (
    <>
      <Title level={3}>📐 Ítems y Costos Directos</Title>

      <Row gutter={16} style={{ marginBottom: 12 }}>
        {[
          { label: 'Ítems de obra', value: items.filter(i => i.tipo === 'Item').length },
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

      <Text type="secondary">Hacé clic en un ítem para editar sus recursos (Datos CD)</Text>

      <Table
        dataSource={items}
        columns={itemCols}
        rowKey={(_, i) => String(i)}
        size="small"
        pagination={false}
        scroll={{ x: 860 }}
        rowClassName={row => row.tipo === 'Título' ? 'row-titulo' : ''}
        onRow={row => ({
          onClick: () => row.tipo === 'Item' && setSelectedItem(row.numero),
          style: {
            cursor: row.tipo === 'Item' ? 'pointer' : 'default',
            background: row.numero === selectedItem ? '#e6f4ff' : undefined,
          },
        })}
        style={{ marginTop: 8 }}
      />

      {selectedItem && (
        <>
          <Divider />
          <Space style={{ marginBottom: 8 }}>
            <Tag color="blue">
              {items.find(i => i.numero === selectedItem)?.descripcion ?? selectedItem}
            </Tag>
            <Button icon={<PlusOutlined />} size="small" onClick={addCD}>Agregar recurso</Button>
            <Button
              type="primary" icon={<SyncOutlined />} size="small"
              onClick={guardarCD}
              loading={patch.isPending || recalc.isPending}
            >
              Guardar y Recalcular
            </Button>
          </Space>

          <Table
            dataSource={selectedCD}
            columns={cdCols(rec.estado)}
            rowKey={(_, i) => String(i)}
            size="small"
            pagination={false}
            scroll={{ x: 1050 }}
            summary={() => (
              <Table.Summary.Row>
                <Table.Summary.Cell index={0} colSpan={8} align="right">
                  <strong>CU total del ítem:</strong>
                </Table.Summary.Cell>
                <Table.Summary.Cell index={8} align="right">
                  <strong>{fmt4(selectedCD.reduce((s, r) => s + r.costo_unitario, 0))}</strong>
                </Table.Summary.Cell>
                <Table.Summary.Cell index={9} />
              </Table.Summary.Row>
            )}
          />
        </>
      )}
    </>
  )
}
