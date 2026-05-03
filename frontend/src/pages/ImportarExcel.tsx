import { useParams } from 'react-router-dom'
import { Alert, Card, Spin, Tabs, Typography, Upload, message } from 'antd'
import { InboxOutlined } from '@ant-design/icons'
import { useImportarExcel, useImportarJson, useProyecto } from '../hooks/useProyecto'

const { Title, Text } = Typography
const { Dragger } = Upload

export default function ImportarExcel() {
  const { id } = useParams<{ id: string }>()
  const pid = Number(id)
  const { data: rec, isLoading } = useProyecto(pid)
  const importarExcel = useImportarExcel(pid)
  const importarJson = useImportarJson(pid)

  if (isLoading || !rec) return <Spin />

  const handleExcel = (file: File) => {
    importarExcel.mutate(file, {
      onSuccess: result => {
        const e = result.estado
        message.success(
          `Excel importado: ${e.equipos.length} equipos, ${e.materiales.length} materiales, ` +
          `${e.items.filter((i: any) => i.tipo === 'Item').length} ítems.`,
          6,
        )
      },
      onError: (err: any) => {
        message.error(`Error al importar: ${err?.response?.data?.detail ?? err.message}`)
      },
    })
    return false
  }

  const handleJson = (file: File) => {
    importarJson.mutate(file, {
      onSuccess: result => {
        const e = result.estado
        message.success(
          `JSON importado: ${e.equipos.length} equipos, ${e.materiales.length} materiales, ` +
          `${e.items.filter((i: any) => i.tipo === 'Item').length} ítems.`,
          6,
        )
      },
      onError: (err: any) => {
        message.error(`Error al importar: ${err?.response?.data?.detail ?? err.message}`)
      },
    })
    return false
  }

  const estado = rec.estado
  const tieneData = estado.equipos.length > 0

  const tabItems = [
    {
      key: 'excel',
      label: 'Excel (.xlsm)',
      children: (
        <>
          <Alert
            type="info"
            style={{ marginBottom: 16 }}
            message="Formato Excel"
            description={
              <>
                Archivo <code>.xlsm</code> con la estructura del sistema KEOPS/DNV.
                Hojas requeridas: <code>EQ</code>, <code>MO</code>, <code>MAT</code>, <code>COM</code>,{' '}
                <code>SUB</code>, <code>Items</code>, <code>Datos CD</code>, <code>Datos GG</code>, <code>Tpte</code>.
              </>
            }
          />
          <Dragger
            accept=".xlsm,.xlsx"
            beforeUpload={file => handleExcel(file as File)}
            showUploadList={false}
            disabled={importarExcel.isPending}
          >
            <p className="ant-upload-drag-icon"><InboxOutlined /></p>
            <p className="ant-upload-text">Arrastrá o hacé clic para seleccionar el archivo Excel</p>
            <p className="ant-upload-hint">.xlsm (con macros) o .xlsx</p>
          </Dragger>
        </>
      ),
    },
    {
      key: 'json',
      label: 'JSON (backup)',
      children: (
        <>
          <Alert
            type="info"
            style={{ marginBottom: 16 }}
            message="Importar desde JSON"
            description="Restaura un proyecto desde un archivo .json exportado anteriormente."
          />
          <Dragger
            accept=".json"
            beforeUpload={file => handleJson(file as File)}
            showUploadList={false}
            disabled={importarJson.isPending}
          >
            <p className="ant-upload-drag-icon"><InboxOutlined /></p>
            <p className="ant-upload-text">Arrastrá o hacé clic para seleccionar el archivo JSON</p>
            <p className="ant-upload-hint">.json (estado completo del proyecto)</p>
          </Dragger>
        </>
      ),
    },
  ]

  return (
    <>
      <Title level={3}>Importar datos</Title>

      <Alert
        type="warning"
        style={{ marginBottom: 16 }}
        message="Atención: importar reemplaza todos los datos del proyecto actual."
      />

      <Card style={{ maxWidth: 600, marginBottom: 16 }}>
        <Tabs items={tabItems} />
      </Card>

      {tieneData && (
        <Card title="Resumen del proyecto actual" style={{ maxWidth: 600 }}>
          {[
            ['Equipos', estado.equipos.length],
            ['MO jornalizada', estado.mo_jornalizada.length],
            ['MO mensualizada', estado.mo_mensualizada.length],
            ['Materiales', estado.materiales.length],
            ['Combustibles', estado.combustibles.length],
            ['Subcontratos', estado.subcontratos.length],
            ['Transportes', estado.transportes.length],
            ['Ítems de obra', estado.items.filter((i: any) => i.tipo === 'Item').length],
            ['Filas Datos CD', estado.datos_cd.length],
            ['Gastos Generales', estado.gastos_generales.filter((g: any) => g.tipo === 'Item').length],
          ].map(([k, v]) => (
            <div key={String(k)} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid #f0f0f0' }}>
              <Text type="secondary">{k}</Text>
              <Text strong>{v}</Text>
            </div>
          ))}
        </Card>
      )}
    </>
  )
}
