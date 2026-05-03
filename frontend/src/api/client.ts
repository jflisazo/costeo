import axios from 'axios'
import type { ProyectoInfo, ProyectoRecord } from '../types'

const http = axios.create({ baseURL: '/api' })

export const api = {
  listarProyectos: () =>
    http.get<ProyectoInfo[]>('/proyectos').then(r => r.data),

  crearProyecto: (nombre: string) =>
    http.post<ProyectoRecord>('/proyectos', { nombre }).then(r => r.data),

  obtenerProyecto: (id: number) =>
    http.get<ProyectoRecord>(`/proyectos/${id}`).then(r => r.data),

  eliminarProyecto: (id: number) =>
    http.delete(`/proyectos/${id}`),

  patchSeccion: (id: number, seccion: string, data: unknown) =>
    http.patch<ProyectoRecord>(`/proyectos/${id}/${seccion}`, data).then(r => r.data),

  recalcular: (id: number) =>
    http.post<ProyectoRecord>(`/proyectos/${id}/recalcular`).then(r => r.data),

  importarExcel: (id: number, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return http.post<ProyectoRecord>(`/proyectos/${id}/importar-excel`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(r => r.data)
  },

  importarJson: (id: number, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return http.post<ProyectoRecord>(`/proyectos/${id}/importar-json`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(r => r.data)
  },
}
