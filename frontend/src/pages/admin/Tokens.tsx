import { useState } from 'react'
import { useAdminTokens, useRevokeToken, useDeleteAdminToken } from '@/hooks/useAdmin'
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
import { Search, Ban, Trash2, Loader2, ChevronDown, ChevronUp } from 'lucide-react'
import { formatDateLocal, dateToLocalISO } from '@/lib/date'
import type { AdminToken, AdminTokenFilters } from '@/types'

const orderByLabels: Record<string, string> = {
  id: 'ID',
  user_uuid: 'Usuário',
  is_revoked: 'Revogado',
  expires_at: 'Expiração',
  created_at: 'Criação',
}

export function AdminTokens() {
  const [userUuidFilter, setUserUuidFilter] = useState('')
  const [revokedFilter, setRevokedFilter] = useState('all')
  const [expiresAfter, setExpiresAfter] = useState('')
  const [expiresBefore, setExpiresBefore] = useState('')
  const [createdAfter, setCreatedAfter] = useState('')
  const [createdBefore, setCreatedBefore] = useState('')
  const [orderBy, setOrderBy] = useState('created_at')
  const [orderDesc, setOrderDesc] = useState(true)
  const [page, setPage] = useState(0)
  const limit = 20

  const { data, isLoading } = useAdminTokens({
    user_uuid: userUuidFilter || undefined,
    is_revoked:
      revokedFilter === 'revoked'
        ? true
        : revokedFilter === 'active'
          ? false
          : undefined,
    expires_after: expiresAfter ? dateToLocalISO(expiresAfter) : undefined,
    expires_before: expiresBefore ? dateToLocalISO(expiresBefore) : undefined,
    created_after: createdAfter ? dateToLocalISO(createdAfter) : undefined,
    created_before: createdBefore ? dateToLocalISO(createdBefore) : undefined,
    order_by: orderBy as AdminTokenFilters['order_by'],
    order_desc: orderDesc,
    offset: page * limit,
    limit,
  })

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold">Tokens</h1>

      <div className="mb-4 space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <Label className="text-sm text-muted-foreground whitespace-nowrap">UUID:</Label>
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="UUID do usuário..."
              aria-label="Buscar por UUID do usuário"
              value={userUuidFilter}
              onChange={(e) => { setUserUuidFilter(e.target.value); setPage(0) }}
              className="pl-9"
            />
          </div>
          <Label className="text-sm text-muted-foreground whitespace-nowrap">Status:</Label>
          <Select
            value={revokedFilter}
            onValueChange={(v) => { setRevokedFilter(v); setPage(0) }}
          >
            <SelectTrigger className="w-40" aria-label="Filtrar por status do token">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos</SelectItem>
              <SelectItem value="active">Ativos</SelectItem>
              <SelectItem value="revoked">Revogados</SelectItem>
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
          <Label className="text-sm text-muted-foreground whitespace-nowrap">Expira entre:</Label>
          <Input
            type="date"
            value={expiresAfter}
            onChange={(e) => { setExpiresAfter(e.target.value); setPage(0) }}
            className="w-40"
            aria-label="Data expiração inicial"
          />
          <span className="text-muted-foreground">e</span>
          <Input
            type="date"
            value={expiresBefore}
            onChange={(e) => { setExpiresBefore(e.target.value); setPage(0) }}
            className="w-40"
            aria-label="Data expiração final"
          />
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Label className="text-sm text-muted-foreground whitespace-nowrap">Criado entre:</Label>
          <Input
            type="date"
            value={createdAfter}
            onChange={(e) => { setCreatedAfter(e.target.value); setPage(0) }}
            className="w-40"
            aria-label="Data criação inicial"
          />
          <span className="text-muted-foreground">e</span>
          <Input
            type="date"
            value={createdBefore}
            onChange={(e) => { setCreatedBefore(e.target.value); setPage(0) }}
            className="w-40"
            aria-label="Data criação final"
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
              <caption className="sr-only">Lista de tokens</caption>
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="px-4 py-3 text-left text-sm font-medium">ID</th>
                  <th className="px-4 py-3 text-left text-sm font-medium">Usuário</th>
                  <th className="px-4 py-3 text-left text-sm font-medium">Status</th>
                  <th className="px-4 py-3 text-left text-sm font-medium">Expira em</th>
                  <th className="px-4 py-3 text-left text-sm font-medium">Criado</th>
                  <th className="px-4 py-3 text-right text-sm font-medium">Ações</th>
                </tr>
              </thead>
              <tbody>
                {data?.result.map((token: AdminToken) => (
                  <TokenRow key={token.id} token={token} />
                ))}
                {data?.result.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">
                      Nenhum token encontrado.
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

function TokenRow({ token }: { token: AdminToken }) {
  const [revokeOpen, setRevokeOpen] = useState(false)
  const [deleteOpen, setDeleteOpen] = useState(false)
  const revokeToken = useRevokeToken()
  const deleteToken = useDeleteAdminToken()

  const isExpired = new Date(token.expires_at) < new Date()

  return (
    <tr className="border-b last:border-0 hover:bg-muted/50">
      <td className="px-4 py-3 text-sm">{token.id}</td>
      <td className="px-4 py-3 text-sm font-mono">
        {token.user_uuid.slice(0, 8)}...
      </td>
      <td className="px-4 py-3">
        {token.is_revoked ? (
          <Badge variant="destructive">Revogado</Badge>
        ) : isExpired ? (
          <Badge variant="secondary">Expirado</Badge>
        ) : (
          <Badge variant="default">Ativo</Badge>
        )}
      </td>
      <td className="px-4 py-3 text-sm">
        {formatDateLocal(token.expires_at)}
      </td>
      <td className="px-4 py-3 text-sm">
        {formatDateLocal(token.created_at)}
      </td>
      <td className="px-4 py-3 text-right">
        {!token.is_revoked && (
          <AlertDialog open={revokeOpen} onOpenChange={setRevokeOpen}>
            <AlertDialogTrigger asChild>
              <Button variant="ghost" size="icon" aria-label="Revogar token">
                <Ban className="h-4 w-4 text-destructive" />
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Revogar token</AlertDialogTitle>
                <AlertDialogDescription>
                  Tem certeza que deseja revogar este token? O usuário será forçado a
                  fazer login novamente.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel disabled={revokeToken.isPending}>Cancelar</AlertDialogCancel>
                <AlertDialogAction
                  disabled={revokeToken.isPending}
                  onClick={() => {
                    revokeToken.mutate(token.id, {
                      onSuccess: () => setRevokeOpen(false),
                    })
                  }}
                >
                  {revokeToken.isPending ? (
                    <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Revogando...</>
                  ) : 'Revogar'}
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        )}
        <AlertDialog open={deleteOpen} onOpenChange={setDeleteOpen}>
          <AlertDialogTrigger asChild>
            <Button variant="ghost" size="icon" aria-label="Excluir token">
              <Trash2 className="h-4 w-4 text-destructive" />
            </Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Excluir token</AlertDialogTitle>
              <AlertDialogDescription>
                Tem certeza que deseja excluir permanentemente este token?
                Esta ação não pode ser desfeita.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel disabled={deleteToken.isPending}>Cancelar</AlertDialogCancel>
              <AlertDialogAction
                disabled={deleteToken.isPending}
                onClick={() => {
                  deleteToken.mutate(token.id, {
                    onSuccess: () => setDeleteOpen(false),
                  })
                }}
              >
                {deleteToken.isPending ? (
                  <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Excluindo...</>
                ) : 'Excluir'}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </td>
    </tr>
  )
}
