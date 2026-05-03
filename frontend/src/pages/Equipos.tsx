import { useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  Button, Drawer, Form, InputNumber, Select, Spin, Table, Tag, Tooltip,
  Typography, message, Popconfirm, Space, Divider,
} from 'antd'
import { PlusOutlined, DeleteOutlined, EditOutlined, SyncOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { useProyecto, usePatch, useRecalcular } from '../hooks/useProyecto'
import type { Equipo } from '../types'

const { Title, Text } = Typography
const METODOS = ['KEOPS', 'DNV', 'Porcentaje', 'Manual_AR']
const MONEDAS = ['USD', 'EUR', '$AR']
const fmt = (n: number) => n.toLocaleString('es-AR', { maximumFractionDigits: 2 })

export default function Equipos() {
  const { id } = useParams<{ id: string }>()
  const pid = Number(id)
  const { data: rec, isLoading } = useProyecto(pid)
  const patch = usePatch(pid)
  const recalc = useRecalcular(pid)

  const [drawerOpen, setDrawerOpen] = useState(false)
  const [editing, setEditing] = useState<Equipo | null>(null)
  const [editIdx, setEditIdx] = useState<number>(-1)
  const [form] = Form.useForm()

  if (isLoading || !rec) return <Spin />

  const equipos = rec.estado.equipos

  const openNew = () => {
    setEditing(null)
    setEditIdx(-1)
    form.resetFields()
    form.setFieldsValue({
      metodo_costeo: 'DNV', moneda: 'USD', propiedad: 'Propio',
      vida_util_hs: 10000, vr: 35, uso_anual: 2000, k_rr: 65, porcentaje: 4,
    })
    setDrawerOpen(true)
  }

  const openEdit = (eq: Equipo, idx: number) => {
    setEditing(eq)
    setEditIdx(idx)
    form.setFieldsValue({
      ...eq,
      vr: eq.vr * 100,
      porcentaje: eq.porcentaje * 100,
    })
    setDrawerOpen(true)
  }

  const handleDelete = async (idx: number) => {
    const next = equipos.filter((_, i) => i !== idx)
    await patch.mutateAsync({ seccion: 'equipos', data: next })
    await recalc.mutateAsync()
    message.success('Equipo eliminado y recalculado.')
  }

  const onDrawerSave = async () => {
    const vals = await form.validateFields()
    const eq: Equipo = {
      nombre: vals.nombre, marca: vals.marca ?? '', modelo: vals.modelo ?? '',
      potencia: vals.potencia ?? 0, moneda: vals.moneda, precio: vals.precio ?? 0,
      k_combustible: vals.k_combustible ?? 0, propiedad: vals.propiedad,
      vida_util_hs: vals.vida_util_hs ?? 10000,
      vr: (vals.vr ?? 35) / 100,
      uso_anual: vals.uso_anual ?? 2000,
      k_rr: (vals.k_rr ?? 65) / 100,
      metodo_costeo: vals.metodo_costeo,
      porcentaje: (vals.porcentaje ?? 4) / 100,
      ratio_ai: editing?.ratio_ai ?? 0,
      ratio_rr: editing?.ratio_rr ?? 0,
      cotiz_base: editing?.cotiz_base ?? 1,
      cu_ai: vals.cu_ai ?? editing?.cu_ai ?? 0,
      cu_rr: vals.cu_rr ?? editing?.cu_rr ?? 0,
      cu_comb: editing?.cu_comb ?? 0,
      costo_hora: editing?.costo_hora ?? 0,
    }
    const next = editIdx >= 0
      ? equipos.map((e, i) => (i === editIdx ? eq : e))
      : [...equipos, eq]
    await patch.mutateAsync({ seccion: 'equipos', data: next })
    await recalc.mutateAsync()
    setDrawerOpen(false)
    message.success('Equipo guardado y recalculado.')
  }

  const columns: ColumnsType<Equipo> = [
    { title: 'Equipo', dataIndex: 'nombre', width: 180, ellipsis: true },
    { title: 'Marca', dataIndex: 'marca', width: 100 },
    { title: 'Método', dataIndex: 'metodo_costeo', width: 90,
      render: v => <Tag color={v === 'KEOPS' ? 'blue' : v === 'DNV' ? 'green' : 'default'}>{v}</Tag> },
    { title: 'Moneda', dataIndex: 'moneda', width: 70 },
    { title: 'Precio', dataIndex: 'precio', width: 110, align: 'right',
      render: v => fmt(v) },
    { title: 'A+I $/hs', dataIndex: 'cu_ai', width: 100, align: 'right',
      render: v => fmt(v) },
    { title: 'R&R $/hs', dataIndex: 'cu_rr', width: 100, align: 'right',
      render: v => fmt(v) },
    { title: 'Comb $/hs', dataIndex: 'cu_comb', width: 100, align: 'right',
      render: v => fmt(v) },
    { title: 'TOTAL $/hs', dataIndex: 'costo_hora', width: 110, align: 'right',
      render: v => <strong>{fmt(v)}</strong> },
    {
      title: '', width: 70, align: 'center',
      render: (_, rec, idx) => (
        <Space>
          <Tooltip title="Editar"><Button size="small" icon={<EditOutlined />} onClick={() => openEdit(rec, idx)} /></Tooltip>
          <Popconfirm title="¿Eliminar?" onConfirm={() => handleDelete(idx)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  const metodo = Form.useWatch('metodo_costeo', form)

  return (
    <>
      <Title level={3}>🚜 Equipos</Title>
      <Space style={{ marginBottom: 12 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={openNew}>Agregar equipo</Button>
        <Button icon={<SyncOutlined />} onClick={() => recalc.mutate()} loading={recalc.isPending}>
          Recalcular todo
        </Button>
        <Text type="secondary">{equipos.length} equipos cargados</Text>
      </Space>

      <Table
        dataSource={equipos}
        columns={columns}
        rowKey={(_, i) => String(i)}
        size="small"
        pagination={false}
        scroll={{ x: 950 }}
      />

      <Drawer
        title={editing ? `Editar: ${editing.nombre}` : 'Nuevo equipo'}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        width={480}
        extra={
          <Button type="primary" onClick={onDrawerSave} loading={patch.isPending || recalc.isPending}>
            Guardar y recalcular
          </Button>
        }
      >
        <Form form={form} layout="vertical">
          <Form.Item name="nombre" label="Nombre" rules={[{ required: true }]}>
            <input className="ant-input" />
          </Form.Item>
          <Form.Item name="marca" label="Marca"><input className="ant-input" /></Form.Item>
          <Form.Item name="modelo" label="Modelo"><input className="ant-input" /></Form.Item>

          <Divider>Precio</Divider>
          <Form.Item name="moneda" label="Moneda">
            <Select options={MONEDAS.map(m => ({ value: m }))} />
          </Form.Item>
          <Form.Item name="precio" label="Precio (en moneda)">
            <InputNumber style={{ width: '100%' }} step={1000} />
          </Form.Item>
          <Form.Item name="potencia" label="Potencia (HP)">
            <InputNumber style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="k_combustible" label="K combustible (lt/HP·hs)">
            <InputNumber style={{ width: '100%' }} step={0.001} precision={4} />
          </Form.Item>
          <Form.Item name="propiedad" label="Propiedad">
            <Select options={[{ value: 'Propio' }, { value: 'Alquilado' }]} />
          </Form.Item>

          <Divider>Método de costeo</Divider>
          <Form.Item name="metodo_costeo" label="Método">
            <Select options={METODOS.map(m => ({ value: m }))} />
          </Form.Item>

          {metodo === 'KEOPS' && editing && (
            <Text type="secondary" style={{ display: 'block', marginBottom: 16 }}>
              ratio_ai = {editing.ratio_ai.toFixed(6)} · ratio_rr = {editing.ratio_rr.toFixed(6)}<br />
              cotiz_base = {editing.cotiz_base.toLocaleString('es-AR')}
            </Text>
          )}

          {metodo === 'DNV' && (
            <>
              <Form.Item name="vida_util_hs" label="Vida útil (hs)">
                <InputNumber style={{ width: '100%' }} step={500} />
              </Form.Item>
              <Form.Item name="vr" label="Valor residual (%)">
                <InputNumber style={{ width: '100%' }} step={1} />
              </Form.Item>
              <Form.Item name="uso_anual" label="Uso anual (hs)">
                <InputNumber style={{ width: '100%' }} step={100} />
              </Form.Item>
              <Form.Item name="k_rr" label="K_RR (%)">
                <InputNumber style={{ width: '100%' }} step={1} />
              </Form.Item>
            </>
          )}

          {metodo === 'Porcentaje' && (
            <>
              <Form.Item name="porcentaje" label="% anual s/precio">
                <InputNumber style={{ width: '100%' }} step={0.5} />
              </Form.Item>
              <Form.Item name="uso_anual" label="Uso anual (hs)">
                <InputNumber style={{ width: '100%' }} step={100} />
              </Form.Item>
            </>
          )}

          {metodo === 'Manual_AR' && (
            <>
              <Form.Item name="cu_ai" label="A+I ($/hs)">
                <InputNumber style={{ width: '100%' }} step={100} />
              </Form.Item>
              <Form.Item name="cu_rr" label="R&R ($/hs)">
                <InputNumber style={{ width: '100%' }} step={100} />
              </Form.Item>
            </>
          )}
        </Form>
      </Drawer>
    </>
  )
}
