import { apiClient } from './client'
import type {
  Todo,
  TodoCreate,
  TodoListResponse,
  TodoListFilters,
  TodoUpdate,
} from '@/types'

export async function listTodos(
  filters: TodoListFilters = {},
): Promise<TodoListResponse> {
  const params = new URLSearchParams()
  if (filters.status) params.append('status', filters.status)
  if (filters.priority) params.append('priority', filters.priority)
  if (filters.search) params.append('search', filters.search)
  if (filters.offset !== undefined) params.append('offset', String(filters.offset))
  if (filters.limit !== undefined) params.append('limit', String(filters.limit))

  const response = await apiClient.get<TodoListResponse>(
    `/todos/?${params.toString()}`,
  )
  return response.data
}

export async function getTodo(uuid: string): Promise<Todo> {
  const response = await apiClient.get<Todo>(`/todos/${uuid}`)
  return response.data
}

export async function createTodo(data: TodoCreate): Promise<Todo> {
  const response = await apiClient.post<Todo>('/todos/', data)
  return response.data
}

export async function updateTodo(
  uuid: string,
  data: TodoUpdate,
): Promise<Todo> {
  const response = await apiClient.patch<Todo>(`/todos/${uuid}`, data)
  return response.data
}

export async function deleteTodo(uuid: string): Promise<void> {
  await apiClient.delete(`/todos/${uuid}`)
}
