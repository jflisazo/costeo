import { useParams } from 'react-router-dom'
import {
  Button, Card, Col, Divider, Form, InputNumber, Row, Select, Spin, Typography, message,
} from 'antd'
import { SyncOutlined } from '@ant-design/icons'
import { useProyecto, usePatch, useRecalcular } from '../hooks/useProyecto'
import type { Proyecto } from '../types'

const { Title } = Typography

export default function ProyectoPage() {
  const { id } = useParams<{ id: string }>()
  const pid = Number(id)
  const { data: rec, isLoading } = useProyecto(pid)
  const patch = usePatch(pid)
  const recalc = useRecalcular(pid)
  const [form] = Form.useForm()

  if (isLoading || !rec) return <Spin />

  const p = rec.estado.proyecto

  const onFinish = async (vals: Record<string, unknown>) => {
    const nuevo: Proyecto = {
      ...p,
      empresa:      vals.empresa as string ?? p.empresa,
      obra:         vals.obra as string ?? p.obra,
      comitente:    vals.comitente as string ?? p.comitente,
      plazo_meses:  vals.plazo_meses as number,
      moneda_oferta: vals.moneda_oferta as string,
      mes_base:     vals.mes_base as string ?? p.mes_base,
      cotizaciones: { USD: vals.usd as number, EUR: vals.eur as number },
      plazo_pago:   vals.plazo_pago as number,
      anticipo:     (vals.anticipo as number) / 100,
      horas_mes_eq: vals.horas_mes_eq as number,
      tasa_anual:   (vals.tasa_anual as number) / 100,
      vida_util_hs: vals.vida_util_hs as number,
    }
    await patch.mutateAsync({ seccion: 'proyecto', data: nuevo })
    const hasData = rec.estado.equipos.length > 0 || rec.estado.materiales.length > 0
    if (hasData) {
      await recalc.mutateAsync()
      message.success('Proyecto guardado y costos recalculados en cascada.')
    } else {
      message.success('Proyecto guardado.')
    }
  }

  return (
    <>
      <Title level={3}>📋 Datos del Proyecto</Title>
      <Form
        form={form}
        layout="vertical"
        initialValues={{
          empresa:      p.empresa,
          obra:         p.obra,
          comitente:    p.comitente,
          plazo_meses:  p.plazo_meses,
          moneda_oferta: p.moneda_oferta,
          mes_base:     p.mes_base,
          usd: p.cotizaciones.USD ?? 1460,
          eur: p.cotizaciones.EUR ?? 1715,
          plazo_pago:   p.plazo_pago,
          anticipo:     p.anticipo * 100,
          horas_mes_eq: p.horas_mes_eq,
          tasa_anual:   p.tasa_anual * 100,
          vida_util_hs: p.vida_util_hs,
        }}
        onFinish={onFinish}
      >
        <Card title="Parámetros del contrato" style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={8}><Form.Item name="empresa" label="Empresa"><input className="ant-input" /></Form.Item></Col>
            <Col span={8}><Form.Item name="comitente" label="Comitente"><input className="ant-input" /></Form.Item></Col>
            <Col span={8}><Form.Item name="obra" label="Obra"><input className="ant-input" /></Form.Item></Col>
          </Row>
          <Row gutter={16}>
            <Col span={6}><Form.Item name="plazo_meses" label="Plazo (meses)"><InputNumber min={1} style={{ width: '100%' }} /></Form.Item></Col>
            <Col span={6}>
              <Form.Item name="moneda_oferta" label="Moneda oferta">
                <Select options={[{ value: '$AR' }, { value: 'USD' }]} />
              </Form.Item>
            </Col>
            <Col span={6}><Form.Item name="mes_base" label="Mes base (YYYY-MM)"><input className="ant-input" placeholder="2024-01" /></Form.Item></Col>
            <Col span={6}><Form.Item name="plazo_pago" label="Plazo pago (días)"><InputNumber style={{ width: '100%' }} /></Form.Item></Col>
          </Row>
          <Row gutter={16}>
            <Col span={6}><Form.Item name="anticipo" label="Anticipo (%)"><InputNumber min={0} max={100} style={{ width: '100%' }} /></Form.Item></Col>
          </Row>
        </Card>

        <Card title="Cotizaciones de monedas" style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={8}><Form.Item name="usd" label="USD ($/AR por dólar)"><InputNumber min={0} step={10} style={{ width: '100%' }} /></Form.Item></Col>
            <Col span={8}><Form.Item name="eur" label="EUR ($/AR por euro)"><InputNumber min={0} step={10} style={{ width: '100%' }} /></Form.Item></Col>
          </Row>
        </Card>

        <Card title="Parámetros DNV" style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={8}><Form.Item name="horas_mes_eq" label="HS/mes equipo"><InputNumber min={0} style={{ width: '100%' }} /></Form.Item></Col>
            <Col span={8}><Form.Item name="tasa_anual" label="Tasa anual (%)"><InputNumber min={0} step={0.5} style={{ width: '100%' }} /></Form.Item></Col>
            <Col span={8}><Form.Item name="vida_util_hs" label="Vida útil default (hs)"><InputNumber min={0} step={500} style={{ width: '100%' }} /></Form.Item></Col>
          </Row>
        </Card>

        <Button
          type="primary"
          htmlType="submit"
          icon={<SyncOutlined />}
          loading={patch.isPending || recalc.isPending}
          size="large"
        >
          Guardar y Recalcular todo
        </Button>
      </Form>

      {rec.estado.equipos.length > 0 && (
        <>
          <Divider />
          <Row gutter={16}>
            {[
              { label: 'USD', value: `$${(p.cotizaciones.USD ?? 0).toLocaleString('es-AR')}` },
              { label: 'EUR', value: `$${(p.cotizaciones.EUR ?? 0).toLocaleString('es-AR')}` },
              { label: 'Equipos', value: rec.estado.equipos.length },
              { label: 'Ítems de obra', value: rec.estado.items.filter(i => i.tipo === 'Item').length },
            ].map(m => (
              <Col span={6} key={m.label}>
                <Card size="small"><strong>{m.label}</strong><br />{m.value}</Card>
              </Col>
            ))}
          </Row>
        </>
      )}
    </>
  )
}
