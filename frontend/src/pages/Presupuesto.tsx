import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { Card, Col, Row, Slider, Spin, Table, Tag, Typography } from 'antd'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  LineChart, Line, ResponsiveContainer,
} from 'recharts'
import type { ColumnsType } from 'antd/es/table'
import { useProyecto } from '../hooks/useProyecto'
import type { Item } from '../types'

const { Title, Text } = Typography
const fmt = (n: number) => n.toLocaleString('es-AR', { maximumFractionDigits: 0 })
const fmtPct = (n: number) => `${n.toFixed(1)}%`

export default function Presupuesto() {
  const { id } = useParams<{ id: string }>()
  const pid = Number(id)
  const { data: rec, isLoading } = useProyecto(pid)

  if (isLoading || !rec) return <Spin />

  const { items, gastos_generales, plan_trabajos, proyecto } = rec.estado
  const itemsObra = items.filter(i => i.tipo === 'Item')
  const costoCD = itemsObra.reduce((s, i) => s + i.costo_total, 0)
  const totalGG = gastos_generales.filter(g => g.tipo === 'Item').reduce((s, g) => s + g.total, 0)
  const costoTotal = costoCD + totalGG

  // Margen derivado de los precios almacenados (importados del Excel / ingresados)
  const precioStored = itemsObra.reduce((s, i) => s + i.precio_total, 0)
  const margenFromData = costoTotal > 0 ? (precioStored / costoTotal - 1) * 100 : 0

  // Slider parte del margen implícito en los datos
  const [margenGlobal, setMargenGlobal] = useState(() => Math.round(margenFromData * 10) / 10)

  // Precio de oferta = costo total × (1 + margen_global)
  const precioOferta = costoTotal * (1 + margenGlobal / 100)

  // Coeficiente de oferta por unidad de CD: precio_unitario = CU_cd * coef_oferta
  const coefOferta = costoCD > 0 ? precioOferta / costoCD : 1

  const itemCols: ColumnsType<Item> = [
    { title: '#', dataIndex: 'numero', width: 130, ellipsis: true,
      render: (v, row) => row.tipo === 'Título'
        ? <Text strong style={{ color: '#1677ff' }}>{v}</Text>
        : <Text code style={{ fontSize: 11 }}>{v}</Text> },
    { title: 'Descripción', dataIndex: 'descripcion', ellipsis: true,
      render: (v, row) => row.tipo === 'Título' ? <Text strong>{v}</Text> : v },
    { title: 'Unid.', dataIndex: 'unidad', width: 60 },
    { title: 'Cantidad', dataIndex: 'cantidad', width: 90, align: 'right', render: v => fmt(v) },
    { title: 'CU costo', dataIndex: 'costo_unitario', width: 110, align: 'right', render: v => fmt(v) },
    { title: 'Total costo', dataIndex: 'costo_total', width: 120, align: 'right',
      render: v => <strong>{fmt(v)}</strong> },
    { title: 'CU oferta', width: 110, align: 'right',
      render: (_, row) => row.tipo === 'Item' ? fmt(row.costo_unitario * coefOferta) : null },
    { title: 'Total oferta', width: 120, align: 'right',
      render: (_, row) => row.tipo === 'Item'
        ? <Text type="success"><strong>{fmt(row.costo_total * coefOferta)}</strong></Text>
        : null },
  ]

  // Plan de trabajos → monthly bar chart
  const meses = proyecto.plazo_meses
  const chartData = Array.from({ length: meses }, (_, m) => {
    const label = `M${m + 1}`
    const costoMes = plan_trabajos.reduce((s, pt) => {
      const item = itemsObra.find(i => i.numero === pt.item_id)
      if (!item) return s
      const frac = pt.distribucion[m] ?? 0
      return s + item.costo_total * frac
    }, 0)
    return { mes: label, costo: Math.round(costoMes) }
  })

  let acum = 0
  const chartDataConCurva = chartData.map(d => {
    acum += d.costo
    return { ...d, acumulado: Math.round(acum) }
  })

  return (
    <>
      <Title level={3}>Presupuesto</Title>

      <Row gutter={16} style={{ marginBottom: 16 }}>
        {[
          { label: 'Costo Directo', value: `$${fmt(costoCD)}`, color: '#1677ff' },
          { label: 'Gastos Generales', value: `$${fmt(totalGG)}`, color: '#fa8c16' },
          { label: 'Costo Total', value: `$${fmt(costoTotal)}`, color: '#f5222d' },
          { label: 'Precio Oferta', value: `$${fmt(precioOferta)}`, color: '#52c41a' },
          { label: 'Margen s/Costo', value: fmtPct(margenGlobal), color: '#722ed1' },
        ].map(m => (
          <Col span={4} key={m.label}>
            <Card size="small" style={{ borderTop: `3px solid ${m.color}` }}>
              <Text type="secondary" style={{ fontSize: 11 }}>{m.label}</Text><br />
              <Text strong style={{ fontSize: 14, color: m.color }}>{m.value}</Text>
            </Card>
          </Col>
        ))}
      </Row>

      <Card size="small" style={{ marginBottom: 16 }}>
        <Row align="middle" gutter={16}>
          <Col flex="none"><Text>Margen global sobre costo total:</Text></Col>
          <Col flex="auto">
            <Slider
              min={0} max={40} step={0.5}
              value={margenGlobal}
              onChange={setMargenGlobal}
              tooltip={{ formatter: v => `${v}%` }}
            />
          </Col>
          <Col flex="none" style={{ minWidth: 60 }}>
            <Text strong style={{ color: '#722ed1' }}>{fmtPct(margenGlobal)}</Text>
          </Col>
        </Row>
      </Card>

      <Table
        dataSource={items}
        columns={itemCols}
        rowKey={(_, i) => String(i)}
        size="small"
        pagination={false}
        scroll={{ x: 840 }}
        rowClassName={row => row.tipo === 'Título' ? 'row-titulo' : ''}
        summary={() => (
          <Table.Summary.Row>
            <Table.Summary.Cell index={0} colSpan={5} align="right"><strong>TOTAL CD:</strong></Table.Summary.Cell>
            <Table.Summary.Cell index={5} align="right"><strong>${fmt(costoCD)}</strong></Table.Summary.Cell>
            <Table.Summary.Cell index={6} align="right"><strong>TOTAL OFERTA:</strong></Table.Summary.Cell>
            <Table.Summary.Cell index={7} align="right"><strong>${fmt(precioOferta)}</strong></Table.Summary.Cell>
          </Table.Summary.Row>
        )}
        style={{ marginBottom: 24 }}
      />

      <Row gutter={16} style={{ marginBottom: 8 }}>
        <Col>
          <Text type="secondary">
            Coef. GG: {costoCD > 0 ? (costoTotal / costoCD).toFixed(4) : '—'} ·
            Coef. oferta: {costoCD > 0 ? coefOferta.toFixed(4) : '—'}
          </Text>
        </Col>
      </Row>

      {chartDataConCurva.some(d => d.costo > 0) && (
        <>
          <Title level={4}>Distribución mensual del costo directo</Title>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={chartDataConCurva} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="mes" tick={{ fontSize: 11 }} />
              <YAxis yAxisId="left" tickFormatter={v => `$${(v / 1e9).toFixed(1)}B`} />
              <YAxis yAxisId="right" orientation="right" tickFormatter={v => `$${(v / 1e9).toFixed(1)}B`} />
              <Tooltip formatter={(v: number) => `$${fmt(v)}`} />
              <Legend />
              <Bar yAxisId="left" dataKey="costo" name="Costo mensual" fill="#1677ff" />
              <Line yAxisId="right" type="monotone" dataKey="acumulado" name="Curva S" stroke="#f5222d" dot={false} strokeWidth={2} />
            </BarChart>
          </ResponsiveContainer>
        </>
      )}
    </>
  )
}
