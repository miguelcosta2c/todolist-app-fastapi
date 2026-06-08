import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  listAdminUsers,
  getAdminUser,
  updateAdminUser,
  deleteAdminUser,
  listAdminTodos,
  updateAdminTodo,
  deleteAdminTodo,
  listTokens,
  revokeToken,
  deleteToken,
} from '@/api/admin'
import type {
  AdminTodoUpdateData,
  AdminUserFilters,
  AdminUserUpdateData,
  AdminTodoFilters,
  AdminTokenFilters,
} from '@/types'
import { toast } from 'sonner'

export function useAdminUsers(filters: AdminUserFilters = {}) {
  return useQuery({
    queryKey: ['admin-users', filters],
    queryFn: () => listAdminUsers(filters),
  })
}

export function useAdminUser(uuid: string) {
  return useQuery({
    queryKey: ['admin-users', uuid],
    queryFn: () => getAdminUser(uuid),
    enabled: !!uuid,
  })
}

export function useUpdateAdminUser() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      uuid,
      data,
    }: {
      uuid: string
      data: AdminUserUpdateData
    }) => updateAdminUser(uuid, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-users'] })
      toast.success('Usuário atualizado com sucesso')
    },
    onError: () => {
      toast.error('Erro ao atualizar usuário')
    },
  })
}

export function useDeleteAdminUser() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (uuid: string) => deleteAdminUser(uuid),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-users'] })
      toast.success('Usuário removido com sucesso')
    },
    onError: () => {
      toast.error('Erro ao remover usuário')
    },
  })
}

export function useAdminTodos(filters: AdminTodoFilters = {}) {
  return useQuery({
    queryKey: ['admin-todos', filters],
    queryFn: () => listAdminTodos(filters),
  })
}

export function useUpdateAdminTodo() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      uuid,
      data,
    }: {
      uuid: string
      data: AdminTodoUpdateData
    }) => updateAdminTodo(uuid, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-todos'] })
      toast.success('Tarefa atualizada com sucesso')
    },
    onError: () => {
      toast.error('Erro ao atualizar tarefa')
    },
  })
}

export function useDeleteAdminTodo() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (uuid: string) => deleteAdminTodo(uuid),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-todos'] })
      toast.success('Tarefa excluída com sucesso')
    },
    onError: () => {
      toast.error('Erro ao excluir tarefa')
    },
  })
}

export function useAdminTokens(filters: AdminTokenFilters = {}) {
  return useQuery({
    queryKey: ['admin-tokens', filters],
    queryFn: () => listTokens(filters),
  })
}

export function useRevokeToken() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => revokeToken(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-tokens'] })
      toast.success('Token revogado com sucesso')
    },
    onError: () => {
      toast.error('Erro ao revogar token')
    },
  })
}

export function useDeleteAdminToken() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => deleteToken(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-tokens'] })
      toast.success('Token excluído com sucesso')
    },
    onError: () => {
      toast.error('Erro ao excluir token')
    },
  })
}
