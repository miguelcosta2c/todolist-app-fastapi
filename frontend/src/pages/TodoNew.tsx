import { useNavigate } from 'react-router-dom'
import { useCreateTodo } from '@/hooks/useTodos'
import { TodoForm, type TodoFormData } from '@/components/todos/TodoForm'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

export function TodoNew() {
  const navigate = useNavigate()
  const createTodo = useCreateTodo()

  async function onSubmit(data: TodoFormData) {
    await createTodo.mutateAsync({
      name: data.name,
      description: data.description || undefined,
      priority: data.priority,
      due_date: data.due_date || null,
    })
    navigate('/')
  }

  return (
    <div className="mx-auto max-w-2xl">
      <Card>
        <CardHeader>
          <CardTitle>Nova Tarefa</CardTitle>
        </CardHeader>
        <CardContent>
          <TodoForm
            onSubmit={onSubmit}
            isSubmitting={createTodo.isPending}
            mode="create"
          />
        </CardContent>
      </Card>
    </div>
  )
}
