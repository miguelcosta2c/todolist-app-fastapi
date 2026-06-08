import { useState } from 'react'
import { useAdminUsers, useDeleteAdminUser, useUpdateAdminUser } from '@/hooks/useAdmin'
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
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
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
import { Search, Pencil, Trash2, Loader2, ChevronDown, ChevronUp } from 'lucide-react'
import { formatDateLocal, dateToLocalISO } from '@/lib/date'
import type { AdminUser, AdminUserFilters, AdminUserUpdateData } from '@/types'

const orderByLabels: Record<string, string> = {
  id: 'ID',
  username: 'Username',
  created_at: 'Criação',
  updated_at: 'Atualização',
  deleted_at: 'Exclusão',
}

export function AdminUsers() {
  const [search, setSearch] = useState('')
  const [emailFilter, setEmailFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [adminFilter, setAdminFilter] = useState('all')
  const [includeDeleted, setIncludeDeleted] = useState(false)
  const [createdAfter, setCreatedAfter] = useState('')
  const [createdBefore, setCreatedBefore] = useState('')
  const [orderBy, setOrderBy] = useState('created_at')
  const [orderDesc, setOrderDesc] = useState(true)
  const [page, setPage] = useState(0)
  const limit = 20

  const { data, isLoading } = useAdminUsers({
    username: search || undefined,
    email: emailFilter || undefined,
    status: statusFilter !== 'all' ? statusFilter : undefined,
    is_superuser: adminFilter === 'all' ? undefined : adminFilter === 'yes',
    include_deleted: includeDeleted || undefined,
    created_after: createdAfter ? dateToLocalISO(createdAfter) : undefined,
    created_before: createdBefore ? dateToLocalISO(createdBefore) : undefined,
    order_by: orderBy as AdminUserFilters['order_by'],
    order_desc: orderDesc,
    offset: page * limit,
    limit,
  })

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">Usuários</h1>
        <label className="flex cursor-pointer items-center gap-2">
          <input
            type="checkbox"
            checked={includeDeleted}
            onChange={(e) => { setIncludeDeleted(e.target.checked); setPage(0) }}
            className="peer sr-only"
          />
          <div className="h-5 w-9 rounded-full bg-muted after:block after:h-4 after:w-4 after:rounded-full after:bg-background after:shadow-sm after:transition-all after:content-[''] peer-checked:bg-primary peer-checked:after:translate-x-4" />
          <span className="text-sm text-muted-foreground">Incluir excluídos</span>
        </label>
      </div>

      <div className="mb-4 space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <Label className="text-sm text-muted-foreground whitespace-nowrap">Username:</Label>
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Buscar por username..."
              aria-label="Buscar por username"
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(0) }}
              className="pl-9"
            />
          </div>
          <Label className="text-sm text-muted-foreground whitespace-nowrap">Email:</Label>
          <div className="relative w-48">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Buscar por email..."
              aria-label="Buscar por email"
              value={emailFilter}
              onChange={(e) => { setEmailFilter(e.target.value); setPage(0) }}
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
            <SelectTrigger className="w-36" aria-label="Filtrar por status">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos</SelectItem>
              <SelectItem value="active">Ativo</SelectItem>
              <SelectItem value="inactive">Inativo</SelectItem>
              <SelectItem value="suspended">Suspenso</SelectItem>
              <SelectItem value="pending">Pendente</SelectItem>
            </SelectContent>
          </Select>
          <Label className="text-sm text-muted-foreground whitespace-nowrap">Admin:</Label>
          <Select
            value={adminFilter}
            onValueChange={(v) => { setAdminFilter(v); setPage(0) }}
          >
            <SelectTrigger className="w-40" aria-label="Filtrar por admin">
              <SelectValue placeholder="Admin" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos</SelectItem>
              <SelectItem value="yes">Admin</SelectItem>
              <SelectItem value="no">Não admin</SelectItem>
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
              <caption className="sr-only">Lista de usuários</caption>
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="px-4 py-3 text-left text-sm font-medium">ID</th>
                  <th className="px-4 py-3 text-left text-sm font-medium">Username</th>
                  <th className="px-4 py-3 text-left text-sm font-medium">Email</th>
                  <th className="px-4 py-3 text-left text-sm font-medium">Status</th>
                  <th className="px-4 py-3 text-left text-sm font-medium">Admin</th>
                  <th className="px-4 py-3 text-left text-sm font-medium">Criado</th>
                  <th className="px-4 py-3 text-right text-sm font-medium">Ações</th>
                </tr>
              </thead>
              <tbody>
                {data?.result.map((user) => (
                  <UserRow key={user.uuid_} user={user} />
                ))}
                {data?.result.length === 0 && (
                  <tr>
                    <td colSpan={7} className="px-4 py-8 text-center text-muted-foreground">
                      Nenhum usuário encontrado.
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

function statusBadgeVariant(status: string) {
  if (status === 'deleted') return 'destructive'
  if (status === 'active') return 'default'
  return 'secondary'
}

function statusLabel(status: string) {
  const labels: Record<string, string> = {
    active: 'Ativo',
    inactive: 'Inativo',
    deleted: 'Excluído',
    suspended: 'Suspenso',
    pending: 'Pendente',
  }
  return labels[status] || status
}

function UserRow({ user }: { user: AdminUser }) {
  const [editOpen, setEditOpen] = useState(false)
  const [deleteOpen, setDeleteOpen] = useState(false)
  const deleteUser = useDeleteAdminUser()
  const isDeleted = user.status === 'deleted'

  return (
    <>
      <tr className={`border-b last:border-0 hover:bg-muted/50 ${isDeleted ? 'opacity-50' : ''}`}>
        <td className="px-4 py-3 text-sm">{user.id}</td>
        <td className="px-4 py-3 text-sm font-medium">{user.username}</td>
        <td className="px-4 py-3 text-sm">{user.email}</td>
        <td className="px-4 py-3">
          <Badge variant={statusBadgeVariant(user.status)}>
            {statusLabel(user.status)}
          </Badge>
        </td>
        <td className="px-4 py-3">
          <Badge variant={user.is_superuser ? 'default' : 'secondary'}>
            {user.is_superuser ? 'Sim' : 'Não'}
          </Badge>
        </td>
        <td className="px-4 py-3 text-sm">
          {formatDateLocal(user.created_at)}
        </td>
        <td className="px-4 py-3 text-right">
          <Button variant="ghost" size="icon" onClick={() => setEditOpen(true)} aria-label={`Editar ${user.username}`}>
            <Pencil className="h-4 w-4" />
          </Button>
          {!isDeleted && (
            <AlertDialog open={deleteOpen} onOpenChange={setDeleteOpen}>
              <AlertDialogTrigger asChild>
                <Button variant="ghost" size="icon" aria-label={`Remover ${user.username}`}>
                  <Trash2 className="h-4 w-4 text-destructive" />
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Remover usuário</AlertDialogTitle>
                  <AlertDialogDescription>
                    Tem certeza que deseja remover {user.username}? Esta ação é reversível
                    (soft delete).
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel disabled={deleteUser.isPending}>Cancelar</AlertDialogCancel>
                  <AlertDialogAction
                    disabled={deleteUser.isPending}
                    onClick={() => {
                      deleteUser.mutate(user.uuid_, {
                        onSuccess: () => setDeleteOpen(false),
                      })
                    }}
                  >
                    {deleteUser.isPending ? (
                      <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Removendo...</>
                    ) : 'Remover'}
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          )}
        </td>
      </tr>
      <UserEditDialog
        user={user}
        open={editOpen}
        onOpenChange={setEditOpen}
      />
    </>
  )
}

function UserEditDialog({
  user,
  open,
  onOpenChange,
}: {
  user: AdminUser
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  const [username, setUsername] = useState(user.username)
  const [email, setEmail] = useState(user.email)
  const [newPassword, setNewPassword] = useState('')
  const [status, setStatus] = useState(user.status)
  const [isSuperuser, setIsSuperuser] = useState(user.is_superuser)
  const updateUser = useUpdateAdminUser()

  function handleSubmit() {
    const data: AdminUserUpdateData = {}
    if (username !== user.username) data.username = username
    if (email !== user.email) data.email = email
    if (newPassword) data.new_password = newPassword
    if (status !== user.status) data.status = status
    if (isSuperuser !== user.is_superuser) data.is_superuser = isSuperuser

    if (Object.keys(data).length === 0) {
      onOpenChange(false)
      return
    }

    updateUser.mutate(
      { uuid: user.uuid_, data },
      { onSuccess: () => onOpenChange(false) },
    )
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Editar {user.username}</DialogTitle>
        </DialogHeader>
        <div className="grid gap-4">
          <div className="grid gap-2">
            <Label htmlFor="username">Username</Label>
            <Input
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="password">Nova senha (opcional)</Label>
            <Input
              id="password"
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="Deixe em branco para não alterar"
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="status">Status</Label>
            <Select value={status} onValueChange={setStatus}>
              <SelectTrigger id="status">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="active">Ativo</SelectItem>
                <SelectItem value="inactive">Inativo</SelectItem>
                <SelectItem value="suspended">Suspenso</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <Label className="flex cursor-pointer items-center gap-2">
            <input
              type="checkbox"
              checked={isSuperuser}
              onChange={(e) => setIsSuperuser(e.target.checked)}
              className="peer sr-only"
            />
            <div className="h-5 w-9 rounded-full bg-muted after:block after:h-4 after:w-4 after:rounded-full after:bg-background after:shadow-sm after:transition-all after:content-[''] peer-checked:bg-primary peer-checked:after:translate-x-4" />
            Administrador
          </Label>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={updateUser.isPending}>
            Cancelar
          </Button>
          <Button onClick={handleSubmit} disabled={updateUser.isPending}>
            {updateUser.isPending ? (
              <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Salvando...</>
            ) : 'Salvar'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
