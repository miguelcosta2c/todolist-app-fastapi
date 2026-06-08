import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { listTodos, getTodo, createTodo, updateTodo, deleteTodo } from '@/api/todos'
import type { TodoCreate, TodoListFilters, TodoUpdate } from '@/types'
import { toast } from 'sonner'

const TODOS_KEY = 'todos'

export function useTodos(filters: TodoListFilters = {}) {
  return useQuery({
    queryKey: [TODOS_KEY, filters],
    queryFn: () => listTodos(filters),
  })
}

export function useTodo(uuid: string) {
  return useQuery({
    queryKey: [TODOS_KEY, uuid],
    queryFn: () => getTodo(uuid),
    enabled: !!uuid,
  })
}

export function useCreateTodo() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: TodoCreate) => createTodo(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [TODOS_KEY] })
      toast.success('Tarefa criada com sucesso')
    },
    onError: () => {
      toast.error('Erro ao criar tarefa')
    },
  })
}

export function useUpdateTodo() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ uuid, data }: { uuid: string; data: TodoUpdate }) =>
      updateTodo(uuid, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [TODOS_KEY] })
      queryClient.invalidateQueries({ queryKey: [TODOS_KEY, variables.uuid] })
      toast.success('Tarefa atualizada com sucesso')
    },
    onError: () => {
      toast.error('Erro ao atualizar tarefa')
    },
  })
}

export function useDeleteTodo() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (uuid: string) => deleteTodo(uuid),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [TODOS_KEY] })
      toast.success('Tarefa excluída com sucesso')
    },
    onError: () => {
      toast.error('Erro ao excluir tarefa')
    },
  })
}
