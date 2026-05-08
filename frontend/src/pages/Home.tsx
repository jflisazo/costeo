import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Button, Card, Input, List, Modal, Typography, Popconfirm, Spin, Empty,
} from 'antd'
import { PlusOutlined, FolderOpenOutlined, DeleteOutlined } from '@ant-design/icons'
import { api } from '../api/client'
import type { ProyectoInfo } from '../types'

const { Title, Text } = Typography

export default function Home() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [modalOpen, setModalOpen] = useState(false)
  const [nuevoNombre, setNuevoNombre] = useState('')

  const { data: proyectos = [], isLoading } = useQuery({
    queryKey: ['proyectos'],
    queryFn: api.listarProyectos,
  })

  const crear = useMutation({
    mutationFn: (nombre: string) => api.crearProyecto(nombre),
    onSuccess: rec => {
      qc.invalidateQueries({ queryKey: ['proyectos'] })
      setModalOpen(false)
      setNuevoNombre('')
      navigate(`/p/${rec.id}/proyecto`)
    },
  })

  const eliminar = useMutation({
    mutationFn: (id: number) => api.eliminarProyecto(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['proyectos'] }),
  })

  return (
    <div style={{ maxWidth: 640, margin: '60px auto', padding: '0 16px' }}>
      <Title level={2}>🏗️ Costeo de Obra Civil</Title>

      <Card
        title="Proyectos"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
            Nuevo proyecto
          </Button>
        }
      >
        {isLoading ? (
          <Spin />
        ) : proyectos.length === 0 ? (
          <Empty description="No hay proyectos. Creá uno para comenzar." />
        ) : (
          <List<ProyectoInfo>
            dataSource={proyectos}
            renderItem={p => (
              <List.Item
                actions={[
                  <Button
                    key="open"
                    type="link"
                    icon={<FolderOpenOutlined />}
                    onClick={() => navigate(`/p/${p.id}/proyecto`)}
                  >
                    Abrir
                  </Button>,
                  <Popconfirm
                    key="del"
                    title="¿Eliminar proyecto?"
                    onConfirm={() => eliminar.mutate(p.id)}
                  >
                    <Button type="link" danger icon={<DeleteOutlined />} />
                  </Popconfirm>,
                ]}
              >
                <List.Item.Meta
                  title={p.nombre}
                  description={
                    p.updated_at
                      ? `Última modificación: ${new Date(p.updated_at).toLocaleString('es-AR')}`
                      : ''
                  }
                />
              </List.Item>
            )}
          />
        )}
      </Card>

      <Modal
        title="Nuevo proyecto"
        open={modalOpen}
        onOk={() => nuevoNombre.trim() && crear.mutate(nuevoNombre.trim())}
        onCancel={() => { setModalOpen(false); setNuevoNombre('') }}
        confirmLoading={crear.isPending}
        okText="Crear"
      >
        <Input
          placeholder="Nombre del proyecto"
          value={nuevoNombre}
          onChange={e => setNuevoNombre(e.target.value)}
          onPressEnter={() => nuevoNombre.trim() && crear.mutate(nuevoNombre.trim())}
          autoFocus
        />
        <Text type="secondary" style={{ fontSize: 12 }}>
          Ej: JM-Seccion-A1yA2
        </Text>
      </Modal>
    </div>
  )
}
