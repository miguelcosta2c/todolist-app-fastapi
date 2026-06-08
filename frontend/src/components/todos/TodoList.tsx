import { useEffect, useMemo, useRef, useState } from "react";
import { useTodos } from "@/hooks/useTodos";
import { TodoCard } from "./TodoCard";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { TodoPriority, TodoStatus } from "@/types";
import {
  Search,
  ListTodo,
  X,
  Filter,
  Loader2,
  CheckCircle2,
  Circle,
} from "lucide-react";
import { Label } from "@/components/ui/label";

export function TodoList() {
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [priorityFilter, setPriorityFilter] = useState<string>("all");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search);
    }, 300);
    return () => clearTimeout(timer);
  }, [search]);

  const filters = useMemo(
    () => ({
      search: debouncedSearch || undefined,
      status: statusFilter !== "all" ? (statusFilter as TodoStatus) : undefined,
      priority:
        priorityFilter !== "all" ? (priorityFilter as TodoPriority) : undefined,
    }),
    [debouncedSearch, statusFilter, priorityFilter],
  );

  const { data, isLoading } = useTodos(filters);

  const total = data?.total ?? 0;

  // 🔥 Ajuste nas checagens: comparando contra o valor do objeto (TodoStatus.TODO)
  const todoCount =
    data?.result.filter((t) => t.status === TodoStatus.TODO).length ?? 0;
  const inProgressCount =
    data?.result.filter((t) => t.status === TodoStatus.IN_PROGRESS).length ?? 0;
  const doneCount =
    data?.result.filter((t) => t.status === TodoStatus.DONE).length ?? 0;

  function clearFilters() {
    setSearch("");
    setDebouncedSearch("");
    setStatusFilter("all");
    setPriorityFilter("all");
    inputRef.current?.focus();
  }

  const hasActiveFilters =
    Boolean(debouncedSearch) ||
    statusFilter !== "all" ||
    priorityFilter !== "all";

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-3 gap-3">
        <div className="flex items-center gap-2 rounded-lg border bg-card p-3 text-sm">
          <ListTodo className="h-4 w-4 text-muted-foreground" />
          <span className="text-muted-foreground">Total</span>
          <span className="ml-auto font-semibold">{total}</span>
        </div>
        <div className="flex items-center gap-2 rounded-lg border bg-card p-3 text-sm">
          <Circle className="h-4 w-4 text-amber-500" />
          <span className="text-muted-foreground">A fazer ({todoCount})</span>
          <span className="ml-auto font-semibold">
            {inProgressCount ? `+${inProgressCount} ⏳` : ""}
          </span>
        </div>
        <div className="flex items-center gap-2 rounded-lg border bg-card p-3 text-sm">
          <CheckCircle2 className="h-4 w-4 text-emerald-500" />
          <span className="text-muted-foreground">Concluídas</span>
          <span className="ml-auto font-semibold">{doneCount}</span>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <Label className="text-sm text-muted-foreground whitespace-nowrap">Buscar:</Label>
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            ref={inputRef}
            placeholder="Nome da tarefa..."
            className="pl-9 pr-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          {search && (
            <button
              type="button"
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              onClick={() => {
                setSearch("");
                setDebouncedSearch("");
                inputRef.current?.focus();
              }}
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>

        <Label className="text-sm text-muted-foreground whitespace-nowrap">Status:</Label>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-full sm:w-40">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos</SelectItem>
            <SelectItem value={TodoStatus.TODO}>A Fazer</SelectItem>
            <SelectItem value={TodoStatus.IN_PROGRESS}>Em Andamento</SelectItem>
            <SelectItem value={TodoStatus.DONE}>Concluído</SelectItem>
            <SelectItem value={TodoStatus.ARCHIVED}>Arquivado</SelectItem>
          </SelectContent>
        </Select>

        <Label className="text-sm text-muted-foreground whitespace-nowrap">Prioridade:</Label>
        <Select value={priorityFilter} onValueChange={setPriorityFilter}>
          <SelectTrigger className="w-full sm:w-40">
            <SelectValue placeholder="Prioridade" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todas</SelectItem>
            <SelectItem value={TodoPriority.LOW}>Baixa</SelectItem>
            <SelectItem value={TodoPriority.MEDIUM}>Média</SelectItem>
            <SelectItem value={TodoPriority.HIGH}>Alta</SelectItem>
          </SelectContent>
        </Select>

        {hasActiveFilters && (
          <Button variant="ghost" size="icon" onClick={clearFilters}>
            <Filter className="h-4 w-4" />
          </Button>
        )}
      </div>

      {isLoading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : total === 0 ? (
        <div className="flex flex-col items-center gap-3 py-16 text-muted-foreground">
          <ListTodo className="h-16 w-16" />
          <p className="text-lg font-medium">Nenhuma tarefa encontrada</p>
          <p className="text-sm">
            {hasActiveFilters
              ? "Tente ajustar os filtros ou a busca."
              : 'Crie sua primeira tarefa clicando em "Nova Tarefa".'}
          </p>
        </div>
      ) : (
        <>
          <p className="text-sm text-muted-foreground">
            Exibindo {data?.result.length} de {total} tarefa{total !== 1 && "s"}
          </p>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {data?.result.map((todo) => (
              <TodoCard key={todo.uuid_} todo={todo} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
