import { Outlet, useNavigate, useParams, useLocation } from 'react-router-dom'
import { Layout, Menu, Typography, Spin, Tag } from 'antd'
import {
  SettingOutlined, ToolOutlined, TeamOutlined,
  InboxOutlined, FireOutlined, BarsOutlined, FundProjectionScreenOutlined,
  TableOutlined, DollarOutlined, BarChartOutlined, ImportOutlined,
  HomeOutlined, AppstoreOutlined, ExperimentOutlined, CalendarOutlined,
} from '@ant-design/icons'
import { useProyecto } from '../hooks/useProyecto'

const { Sider, Content } = Layout
const { Text } = Typography

const MENU: { key: string; label: string; icon: React.ReactNode }[] = [
  { key: 'proyecto',     label: 'Proyecto',         icon: <SettingOutlined /> },
  { key: 'equipos',      label: 'Equipos',           icon: <ToolOutlined /> },
  { key: 'mo',           label: 'Mano de Obra',      icon: <TeamOutlined /> },
  { key: 'materiales',   label: 'Materiales',        icon: <InboxOutlined /> },
  { key: 'combustibles', label: 'Combustibles',      icon: <FireOutlined /> },
  { key: 'subcontratos', label: 'Subcontratos',      icon: <BarsOutlined /> },
  { key: 'auxiliares',   label: 'Auxiliares',        icon: <FundProjectionScreenOutlined /> },
  { key: 'items',        label: 'Ítems',             icon: <TableOutlined /> },
  { key: 'datos-cd',     label: 'Datos CD',          icon: <AppstoreOutlined /> },
  { key: 'datos-aux',    label: 'Datos Aux',         icon: <ExperimentOutlined /> },
  { key: 'gg',           label: 'Gastos Generales',  icon: <DollarOutlined /> },
  { key: 'gantt',        label: 'Gantt',             icon: <CalendarOutlined /> },
  { key: 'presupuesto',  label: 'Presupuesto',       icon: <BarChartOutlined /> },
  { key: 'importar',     label: 'Importar Excel',    icon: <ImportOutlined /> },
]

export default function AppLayout() {
  const { id } = useParams<{ id: string }>()
  const pid = Number(id)
  const navigate = useNavigate()
  const location = useLocation()
  const { data: rec, isLoading } = useProyecto(pid)

  const parts = location.pathname.split('/')
  const segment = parts[parts.length - 1] ?? 'proyecto'

  if (isLoading) return <Spin size="large" style={{ margin: '20vh auto', display: 'block' }} />

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={210} theme="light" style={{ borderRight: '1px solid #f0f0f0' }}>
        <div style={{ padding: '16px 12px 8px' }}>
          <div
            style={{ cursor: 'pointer', marginBottom: 8 }}
            onClick={() => navigate('/')}
          >
            <HomeOutlined /> <Text type="secondary" style={{ fontSize: 12 }}>Proyectos</Text>
          </div>
          {rec && (
            <Tag color="blue" style={{ width: '100%', textAlign: 'center', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {rec.nombre}
            </Tag>
          )}
          {rec?.estado.proyecto.obra && (
            <Text type="secondary" style={{ fontSize: 11, display: 'block', marginTop: 4 }}>
              {rec.estado.proyecto.obra}
            </Text>
          )}
        </div>
        <Menu
          mode="inline"
          selectedKeys={[segment]}
          onClick={({ key }) => navigate(`/p/${pid}/${key}`)}
          items={MENU}
          style={{ borderRight: 0 }}
        />
      </Sider>
      <Content style={{ padding: '24px', background: '#fafafa', overflowY: 'auto' }}>
        <Outlet />
      </Content>
    </Layout>
  )
}
