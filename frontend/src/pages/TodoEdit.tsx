import { useParams, useNavigate } from 'react-router-dom'
import { useTodo, useUpdateTodo } from '@/hooks/useTodos'
import { TodoForm, type TodoFormData } from '@/components/todos/TodoForm'
import { toDateInputValue } from '@/lib/date'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

export function TodoEdit() {
  const { uuid } = useParams<{ uuid: string }>()
  const navigate = useNavigate()
  const { data: todo, isLoading } = useTodo(uuid || '')
  const updateTodo = useUpdateTodo()

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    )
  }

  if (!todo) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        Tarefa não encontrada
      </div>
    )
  }

  async function onSubmit(data: TodoFormData) {
    if (!uuid) return
    await updateTodo.mutateAsync({
      uuid,
      data: {
        name: data.name,
        description: data.description,
        priority: data.priority,
        due_date: data.due_date || null,
      },
    })
    navigate('/')
  }

  return (
    <div className="mx-auto max-w-2xl">
      <Card>
        <CardHeader>
          <CardTitle>Editar Tarefa</CardTitle>
        </CardHeader>
        <CardContent>
          <TodoForm
            defaultValues={{
              name: todo.name,
              description: todo.description || '',
              priority: todo.priority,
              due_date: toDateInputValue(todo.due_date),
            }}
            onSubmit={onSubmit}
            isSubmitting={updateTodo.isPending}
            mode="edit"
          />
        </CardContent>
      </Card>
    </div>
  )
}
