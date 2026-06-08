import { useAdminUsers } from '@/hooks/useAdmin'
import { useAdminTodos } from '@/hooks/useAdmin'
import { useAdminTokens } from '@/hooks/useAdmin'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Users, ListTodo, KeyRound, Loader2 } from 'lucide-react'

export function AdminDashboard() {
  const { data: users, isLoading: usersLoading } = useAdminUsers({ limit: 1 })
  const { data: todos, isLoading: todosLoading } = useAdminTodos({ limit: 1 })
  const { data: tokens, isLoading: tokensLoading } = useAdminTokens({ limit: 1 })

  const stats = [
    {
      title: 'Usuários',
      value: users?.total,
      icon: Users,
      loading: usersLoading,
    },
    {
      title: 'Tarefas',
      value: todos?.total,
      icon: ListTodo,
      loading: todosLoading,
    },
    {
      title: 'Tokens',
      value: tokens?.total,
      icon: KeyRound,
      loading: tokensLoading,
    },
  ]

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold">Painel Admin</h1>
      <div className="grid gap-4 md:grid-cols-3">
        {stats.map(({ title, value, icon: Icon, loading }) => (
          <Card key={title}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">{title}</CardTitle>
              <Icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex h-9 items-center">
                  <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                </div>
              ) : (
                <div className="text-2xl font-bold">{value ?? 0}</div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
