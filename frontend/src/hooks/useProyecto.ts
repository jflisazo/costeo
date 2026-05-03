import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'

export const QK = (id: number) => ['proyecto', id] as const

export function useProyecto(id: number) {
  return useQuery({
    queryKey: QK(id),
    queryFn: () => api.obtenerProyecto(id),
    enabled: id > 0,
  })
}

export function usePatch(proyectoId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ seccion, data }: { seccion: string; data: unknown }) =>
      api.patchSeccion(proyectoId, seccion, data),
    onSuccess: rec => qc.setQueryData(QK(proyectoId), rec),
  })
}

export function useRecalcular(proyectoId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => api.recalcular(proyectoId),
    onSuccess: rec => qc.setQueryData(QK(proyectoId), rec),
  })
}

export function useImportarExcel(proyectoId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (file: File) => api.importarExcel(proyectoId, file),
    onSuccess: rec => qc.setQueryData(QK(proyectoId), rec),
  })
}

export function useImportarJson(proyectoId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (file: File) => api.importarJson(proyectoId, file),
    onSuccess: rec => qc.setQueryData(QK(proyectoId), rec),
  })
}
