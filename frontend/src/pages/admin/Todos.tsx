import { useState } from 'react'
import {
  useAdminTodos,
  useDeleteAdminTodo,
  useUpdateAdminTodo,
} from '@/hooks/useAdmin'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'
import { Search, Trash2, Eye, Pencil, Loader2, ChevronDown, ChevronUp } from 'lucide-react'
import { TodoPriority, TodoStatus } from '@/types'
import { formatDateLocal, formatDateOnly, dateToLocalISO, formatDateTimeLocal, localDatetimeToISO } from '@/lib/date'
import type { AdminTodo, AdminTodoFilters, AdminTodoUpdateData } from '@/types'

const priorityLabels: Record<string, string> = {
  NONE: 'Nenhuma',
  LOW: 'Baixa',
  MEDIUM: 'Média',
  HIGH: 'Alta',
}

const statusLabels: Record<string, string> = {
  TODO: 'A fazer',
  IN_PROGRESS: 'Em andamento',
  DONE: 'Concluída',
  ARCHIVED: 'Arquivada',
}

const orderByLabels: Record<string, string> = {
  created_at: 'Criação',
  updated_at: 'Atualização',
  due_date: 'Data limite',
  priority: 'Prioridade',
  status: 'Status',
}

export function AdminTodos() {
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [priorityFilter, setPriorityFilter] = useState('all')
  const [userUuidFilter, setUserUuidFilter] = useState('')
  const [createdAfter, setCreatedAfter] = useState('')
  const [createdBefore, setCreatedBefore] = useState('')
  const [orderBy, setOrderBy] = useState('created_at')
  const [orderDesc, setOrderDesc] = useState(true)
  const [page, setPage] = useState(0)
  const limit = 20

  const { data, isLoading } = useAdminTodos({
    search: search || undefined,
    status: statusFilter !== 'all' ? (statusFilter as TodoStatus) : undefined,
    priority: priorityFilter !== 'all' ? (priorityFilter as TodoPriority) : undefined,
    user_uuid: userUuidFilter || undefined,
    created_after: createdAfter ? dateToLocalISO(createdAfter) : undefined,
    created_before: createdBefore ? dateToLocalISO(createdBefore) : undefined,
    order_by: orderBy as AdminTodoFilters['order_by'],
    order_desc: orderDesc,
    offset: page * limit,
    limit,
  })

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold">Tarefas</h1>

      <div className="mb-4 space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <Label className="text-sm text-muted-foreground whitespace-nowrap">Buscar:</Label>
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Nome da tarefa..."
              aria-label="Buscar tarefas"
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(0) }}
              className="pl-9"
            />
          </div>
          <Label className="text-sm text-muted-foreground whitespace-nowrap">UUID:</Label>
          <div className="relative w-56">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="UUID do usuário..."
              aria-label="Filtrar por UUID do usuário"
              value={userUuidFilter}
              onChange={(e) => { setUserUuidFilter(e.target.value); setPage(0) }}
              className="pl-9"
            />
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Label className="text-sm text-muted-foreground whitespace-nowrap">Status:</Label>
          <Select
            value={statusFilter}
            onValueChange={(v) => { setStatusFilter(v); setPage(0) }}
          >
            <SelectTrigger className="w-40" aria-label="Filtrar por status">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos</SelectItem>
              <SelectItem value="TODO">A fazer</SelectItem>
              <SelectItem value="IN_PROGRESS">Em andamento</SelectItem>
              <SelectItem value="DONE">Concluída</SelectItem>
              <SelectItem value="ARCHIVED">Arquivada</SelectItem>
            </SelectContent>
          </Select>
          <Label className="text-sm text-muted-foreground whitespace-nowrap">Prioridade:</Label>
          <Select
            value={priorityFilter}
            onValueChange={(v) => { setPriorityFilter(v); setPage(0) }}
          >
            <SelectTrigger className="w-40" aria-label="Filtrar por prioridade">
              <SelectValue placeholder="Prioridade" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todas</SelectItem>
              <SelectItem value="NONE">Nenhuma</SelectItem>
              <SelectItem value="LOW">Baixa</SelectItem>
              <SelectItem value="MEDIUM">Média</SelectItem>
              <SelectItem value="HIGH">Alta</SelectItem>
            </SelectContent>
          </Select>
          <Label className="text-sm text-muted-foreground whitespace-nowrap">Ordenar:</Label>
          <Select
            value={orderBy}
            onValueChange={(v) => { setOrderBy(v); setPage(0) }}
          >
            <SelectTrigger className="w-40" aria-label="Ordenar por">
              <SelectValue placeholder="Ordenar por" />
            </SelectTrigger>
            <SelectContent>
              {Object.entries(orderByLabels).map(([value, label]) => (
                <SelectItem key={value} value={value}>{label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button
            variant="outline"
            size="icon"
            onClick={() => { setOrderDesc(!orderDesc); setPage(0) }}
            aria-label={orderDesc ? 'Ordem decrescente' : 'Ordem crescente'}
          >
            {orderDesc ? <ChevronDown className="h-4 w-4" /> : <ChevronUp className="h-4 w-4" />}
          </Button>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Label className="text-sm text-muted-foreground whitespace-nowrap">Criado entre:</Label>
          <Input
            type="date"
            value={createdAfter}
            onChange={(e) => { setCreatedAfter(e.target.value); setPage(0) }}
            className="w-40"
            aria-label="Data inicial"
          />
          <span className="text-muted-foreground">e</span>
          <Input
            type="date"
            value={createdBefore}
            onChange={(e) => { setCreatedBefore(e.target.value); setPage(0) }}
            className="w-40"
            aria-label="Data final"
          />
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-8">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <>
          <div className="overflow-x-auto rounded-lg border">
            <table className="w-full">
              <caption className="sr-only">Lista de tarefas</caption>
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="px-4 py-3 text-left text-sm font-medium">Nome</th>
                  <th className="px-4 py-3 text-left text-sm font-medium">Status</th>
                  <th className="px-4 py-3 text-left text-sm font-medium">Prioridade</th>
                  <th className="px-4 py-3 text-left text-sm font-medium">Usuário</th>
                  <th className="px-4 py-3 text-left text-sm font-medium">Criado</th>
                  <th className="px-4 py-3 text-right text-sm font-medium">Ações</th>
                </tr>
              </thead>
              <tbody>
                {data?.result.map((todo) => (
                  <TodoRow key={todo.uuid_} todo={todo} />
                ))}
                {data?.result.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">
                      Nenhuma tarefa encontrada.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {data && (
            <div className="mt-4 flex items-center justify-between text-sm text-muted-foreground">
              <span>Exibindo {data.result.length} de {data.total}</span>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page === 0}
                  onClick={() => setPage((p) => p - 1)}
                >
                  Anterior
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={(page + 1) * limit >= data.total}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Próximo
                </Button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}

function TodoRow({ todo }: { todo: AdminTodo }) {
  const [detailsOpen, setDetailsOpen] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const [deleteOpen, setDeleteOpen] = useState(false)
  const deleteTodo = useDeleteAdminTodo()

  return (
    <>
      <tr className="border-b last:border-0 hover:bg-muted/50">
        <td className="px-4 py-3 text-sm font-medium">{todo.name}</td>
        <td className="px-4 py-3">
          <Badge variant={todo.status === 'DONE' ? 'default' : 'secondary'}>
            {statusLabels[todo.status]}
          </Badge>
        </td>
        <td className="px-4 py-3">
          {todo.priority !== 'NONE' && (
            <Badge variant="outline">
              {priorityLabels[todo.priority]}
            </Badge>
          )}
        </td>
        <td className="px-4 py-3 text-sm">
          {todo.username || (
            <span className="font-mono text-xs text-muted-foreground">
              {todo.user_uuid.slice(0, 8)}...
            </span>
          )}
        </td>
        <td className="px-4 py-3 text-sm">
          {formatDateLocal(todo.created_at)}
        </td>
        <td className="px-4 py-3 text-right">
          <Button variant="ghost" size="icon" onClick={() => setDetailsOpen(true)} aria-label="Ver detalhes">
            <Eye className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" onClick={() => setEditOpen(true)} aria-label={`Editar ${todo.name}`}>
            <Pencil className="h-4 w-4" />
          </Button>
          <AlertDialog open={deleteOpen} onOpenChange={setDeleteOpen}>
            <AlertDialogTrigger asChild>
              <Button variant="ghost" size="icon" aria-label={`Excluir ${todo.name}`}>
                <Trash2 className="h-4 w-4 text-destructive" />
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Excluir tarefa</AlertDialogTitle>
                <AlertDialogDescription>
                  Tem certeza que deseja excluir &quot;{todo.name}&quot;?
                  Esta ação não pode ser desfeita.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel disabled={deleteTodo.isPending}>Cancelar</AlertDialogCancel>
                <AlertDialogAction
                  disabled={deleteTodo.isPending}
                  onClick={() => {
                    deleteTodo.mutate(todo.uuid_, {
                      onSuccess: () => setDeleteOpen(false),
                    })
                  }}
                >
                  {deleteTodo.isPending ? (
                    <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Excluindo...</>
                  ) : 'Excluir'}
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </td>
      </tr>
      <Dialog open={detailsOpen} onOpenChange={setDetailsOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{todo.name}</DialogTitle>
          </DialogHeader>
          <div className="grid gap-3 text-sm">
            <div>
              <span className="font-medium">Descrição:</span>{' '}
              {todo.description || '(sem descrição)'}
            </div>
            <div>
              <span className="font-medium">Status:</span>{' '}
              {statusLabels[todo.status]}
            </div>
            <div>
              <span className="font-medium">Prioridade:</span>{' '}
              {priorityLabels[todo.priority] || 'Nenhuma'}
            </div>
            <div>
              <span className="font-medium">Usuário:</span>{' '}
              {todo.username || todo.user_uuid}
            </div>
            <div>
              <span className="font-medium">Criado:</span>{' '}
              {formatDateLocal(todo.created_at)}
            </div>
            <div>
              <span className="font-medium">Atualizado:</span>{' '}
              {formatDateLocal(todo.updated_at)}
            </div>
            {todo.due_date && (
              <div>
                <span className="font-medium">Data limite:</span>{' '}
                {formatDateOnly(todo.due_date)}
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
      <TodoEditDialog
        todo={todo}
        open={editOpen}
        onOpenChange={setEditOpen}
      />
    </>
  )
}

function TodoEditDialog({
  todo,
  open,
  onOpenChange,
}: {
  todo: AdminTodo
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  const [name, setName] = useState(todo.name)
  const [description, setDescription] = useState(todo.description ?? '')
  const [status, setStatus] = useState(todo.status)
  const [priority, setPriority] = useState(todo.priority)
  const [dueDate, setDueDate] = useState(formatDateTimeLocal(todo.due_date))
  const updateTodo = useUpdateAdminTodo()

  function handleSubmit() {
    const data: AdminTodoUpdateData = {}
    if (name !== todo.name) data.name = name
    if (description !== (todo.description ?? '')) data.description = description || null
    if (status !== todo.status) data.status = status
    if (priority !== todo.priority) data.priority = priority
    const newDueDate = dueDate ? localDatetimeToISO(dueDate) : null
    if (newDueDate !== todo.due_date) data.due_date = newDueDate

    if (Object.keys(data).length === 0) {
      onOpenChange(false)
      return
    }

    updateTodo.mutate(
      { uuid: todo.uuid_, data },
      { onSuccess: () => onOpenChange(false) },
    )
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Editar {todo.name}</DialogTitle>
        </DialogHeader>
        <div className="grid gap-4">
          <div className="grid gap-2">
            <Label htmlFor="name">Nome</Label>
            <Input
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="description">Descrição</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="status">Status</Label>
            <Select value={status} onValueChange={(v) => setStatus(v as TodoStatus)}>
              <SelectTrigger id="status">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="TODO">A fazer</SelectItem>
                <SelectItem value="IN_PROGRESS">Em andamento</SelectItem>
                <SelectItem value="DONE">Concluída</SelectItem>
                <SelectItem value="ARCHIVED">Arquivada</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="grid gap-2">
            <Label htmlFor="priority">Prioridade</Label>
            <Select value={priority} onValueChange={(v) => setPriority(v as TodoPriority)}>
              <SelectTrigger id="priority">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="NONE">Nenhuma</SelectItem>
                <SelectItem value="LOW">Baixa</SelectItem>
                <SelectItem value="MEDIUM">Média</SelectItem>
                <SelectItem value="HIGH">Alta</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="grid gap-2">
            <Label htmlFor="due_date">Data limite</Label>
            <Input
              id="due_date"
              type="datetime-local"
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={updateTodo.isPending}>
            Cancelar
          </Button>
          <Button onClick={handleSubmit} disabled={updateTodo.isPending}>
            {updateTodo.isPending ? (
              <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Salvando...</>
            ) : 'Salvar'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
