import { useState, useMemo } from 'react'
import { useParams } from 'react-router-dom'
import {
  Button, Col, Input, InputNumber, Row, Space, Spin, Table, Tag, Typography, message,
} from 'antd'
import { SyncOutlined, ReloadOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { useProyecto, usePatch, useRecalcular } from '../hooks/useProyecto'
import type { GanttFila } from '../types'

const { Title, Text } = Typography
const fmt2 = (n: number) => n.toLocaleString('es-AR', { maximumFractionDigits: 2 })
const fmt4 = (n: number) => n.toLocaleString('es-AR', { maximumFractionDigits: 4 })

const N_MESES = 60

function emptyMeses(): number[] { return Array.from({ length: N_MESES }, () => 0) }

function ensure60(meses?: number[]): number[] {
  const arr = Array.isArray(meses) ? meses.slice(0, N_MESES) : []
  while (arr.length < N_MESES) arr.push(0)
  return arr
}

function sumaMeses(meses: number[]): number {
  return meses.reduce((s, x) => s + (x || 0), 0)
}

export default function Gantt() {
  const { id } = useParams<{ id: string }>()
  const pid = Number(id)
  const { data: rec, isLoading } = useProyecto(pid)
  const patch = usePatch(pid)
  const recalc = useRecalcular(pid)

  const [rows, setRows] = useState<GanttFila[]>([])
  const [init, setInit] = useState(false)
  const [busqueda, setBusqueda] = useState('')
  const [plazoVisible, setPlazoVisible] = useState<number>(24)

  if (isLoading || !rec) return <Spin />
  if (!init) {
    const seed = rec.estado.gantt && rec.estado.gantt.length > 0
      ? rec.estado.gantt
      : rec.estado.items.map(it => ({
          tipo: it.tipo, numero: it.numero, item_uid: it.uid,
          descripcion: it.descripcion, unidad: it.unidad, cantidad: it.cantidad,
          meses: emptyMeses(), ctrl: 0,
        }))
    setRows(seed.map(g => ({ ...g, meses: ensure60(g.meses) })))
    setPlazoVisible(Math.max(12, rec.estado.proyecto.plazo_meses || 24))
    setInit(true)
  }

  const setMes = (i: number, mIdx: number, val: number) =>
    setRows(prev => prev.map((r, j) => {
      if (j !== i) return r
      const meses = ensure60(r.meses).slice()
      meses[mIdx] = val
      return { ...r, meses, ctrl: sumaMeses(meses) }
    }))

  const guardar = async () => {
    const payload = rows.map(r => ({ ...r, meses: ensure60(r.meses), ctrl: sumaMeses(ensure60(r.meses)) }))
    await patch.mutateAsync({ seccion: 'gantt', data: payload })
    const res = await recalc.mutateAsync()
    setRows((res.estado.gantt ?? []).map(g => ({ ...g, meses: ensure60(g.meses) })))
    message.success('Gantt guardado.')
  }

  const sincronizar = async () => {
    // Forzar refresco desde items (descartando edición pendiente)
    await recalc.mutateAsync()
    message.success('Sincronizado con Ítems. Recargá la página para ver cambios.')
  }

  const filtradas = useMemo(() => {
    const q = busqueda.trim().toLowerCase()
    return rows.map((r, i) => ({ r, i })).filter(({ r }) =>
      !q || r.numero.toLowerCase().includes(q) || r.descripcion.toLowerCase().includes(q))
  }, [rows, busqueda])

  // Construir columnas de meses dinámicamente
  const mesesCols: ColumnsType<{ r: GanttFila; i: number }> = []
  for (let m = 0; m < plazoVisible; m++) {
    mesesCols.push({
      title: String(m + 1), width: 70, align: 'right',
      render: (_, { r, i }) => r.tipo === 'Item' ? (
        <InputNumber size="small" style={{ width: 62 }}
          value={r.meses?.[m] ?? 0} step={0.05} min={0}
          formatter={(v) => v !== undefined && v !== null ? String(v) : ''}
          onChange={v => setMes(i, m, Number(v ?? 0))} />
      ) : null,
    })
  }

  const cols: ColumnsType<{ r: GanttFila; i: number }> = [
    { title: 'Tipo', dataIndex: 'tipo', width: 80, fixed: 'left',
      render: (_, { r }) => <Text type={r.tipo === 'Título' ? 'secondary' : undefined}>{r.tipo}</Text> },
    { title: 'Nº_Item', width: 270, fixed: 'left',
      render: (_, { r }) => (
        <span>
          <Text code style={{ fontSize: 11 }}>{r.numero}</Text>{' '}
          {r.tipo === 'Título'
            ? <Text strong style={{ color: '#1677ff' }}>{r.descripcion}</Text>
            : r.descripcion}
        </span>
      ) },
    { title: 'Un', dataIndex: 'unidad', width: 60, fixed: 'left' },
    { title: 'Cantidad', dataIndex: 'cantidad', width: 95, fixed: 'left', align: 'right',
      render: (_, { r }) => r.tipo === 'Item' ? fmt2(r.cantidad) : null },
    { title: 'Ctrl', width: 85, fixed: 'left', align: 'right',
      render: (_, { r }) => {
        const s = sumaMeses(ensure60(r.meses))
        const ok = Math.abs(s - 1.0) < 0.001 || (r.tipo === 'Título' && s === 0) || (r.cantidad === 0)
        return r.tipo === 'Item' ? (
          <Tag color={ok ? 'green' : (s === 0 ? 'default' : 'red')}>{fmt4(s)}</Tag>
        ) : null
      } },
    ...mesesCols,
  ]

  return (
    <>
      <Title level={3}>📅 Gantt</Title>
      <Row gutter={16} style={{ marginBottom: 12 }}>
        {[
          { label: 'Filas', value: rows.length },
          { label: 'Ítems con plan', value: rows.filter(r => r.tipo === 'Item' && sumaMeses(ensure60(r.meses)) > 0).length },
          { label: 'Ítems sin plan', value: rows.filter(r => r.tipo === 'Item' && sumaMeses(ensure60(r.meses)) === 0 && r.cantidad > 0).length },
          { label: 'Meses visibles', value: plazoVisible },
        ].map(m => (
          <Col span={6} key={m.label}>
            <div style={{ background: '#f5f5f5', padding: '8px 12px', borderRadius: 6 }}>
              <Text type="secondary" style={{ fontSize: 12 }}>{m.label}</Text><br />
              <Text strong>{m.value}</Text>
            </div>
          </Col>
        ))}
      </Row>

      <Space style={{ marginBottom: 8 }} wrap>
        <Input.Search placeholder="Filtrar por Nº o descripción"
          value={busqueda} onChange={e => setBusqueda(e.target.value)}
          allowClear style={{ width: 320 }} />
        <span>Meses visibles:</span>
        <InputNumber size="small" min={1} max={60} step={1}
          value={plazoVisible} onChange={v => setPlazoVisible(Number(v ?? 24))} />
        <Button icon={<ReloadOutlined />} onClick={sincronizar}>Sincronizar con Ítems</Button>
        <Button type="primary" icon={<SyncOutlined />} onClick={guardar}
          loading={patch.isPending || recalc.isPending}>
          Guardar
        </Button>
        <Text type="secondary" style={{ fontSize: 12 }}>
          Ctrl = suma de meses 1..60. Debería ser 1.0 por ítem con cantidad &gt; 0.
        </Text>
      </Space>

      <Table
        dataSource={filtradas}
        columns={cols}
        rowKey={({ i }) => String(i)}
        size="small"
        pagination={{ pageSize: 50, showSizeChanger: true, pageSizeOptions: [25, 50, 100, 200] }}
        scroll={{ x: 800 + 70 * plazoVisible, y: 520 }}
        rowClassName={({ r }) => r.tipo === 'Título' ? 'row-titulo' : ''}
      />
    </>
  )
}
