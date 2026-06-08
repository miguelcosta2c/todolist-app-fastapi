import { TodoList } from '@/components/todos/TodoList'

export function Dashboard() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Minhas Tarefas</h1>
        <p className="text-muted-foreground">
          Gerencie suas tarefas do dia a dia
        </p>
      </div>
      <TodoList />
    </div>
  )
}
