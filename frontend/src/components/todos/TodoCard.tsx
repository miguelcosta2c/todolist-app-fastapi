import { useState } from "react";
import { Link } from "react-router-dom";
import type { Todo } from "@/types";
import { TodoPriority, TodoStatus } from "@/types";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { useDeleteTodo, useUpdateTodo } from "@/hooks/useTodos";
import { cn } from "@/lib/utils";
import { formatDateOnly } from "@/lib/date";
import { Pencil, Trash2, Calendar, Circle, CheckCircle2 } from "lucide-react";

const statusLabels: Record<TodoStatus, string> = {
  [TodoStatus.TODO]: "A Fazer",
  [TodoStatus.IN_PROGRESS]: "Em Andamento",
  [TodoStatus.DONE]: "Concluído",
  [TodoStatus.ARCHIVED]: "Arquivado",
};

const priorityLabels: Record<TodoPriority, string> = {
  [TodoPriority.NONE]: "",
  [TodoPriority.LOW]: "Baixa",
  [TodoPriority.MEDIUM]: "Média",
  [TodoPriority.HIGH]: "Alta",
};

const priorityVariants: Record<
  TodoPriority,
  "default" | "secondary" | "destructive" | "outline"
> = {
  [TodoPriority.NONE]: "outline",
  [TodoPriority.LOW]: "secondary",
  [TodoPriority.MEDIUM]: "default",
  [TodoPriority.HIGH]: "destructive",
};

const statusVariants: Record<TodoStatus, "default" | "secondary" | "outline"> =
  {
    [TodoStatus.TODO]: "outline",
    [TodoStatus.IN_PROGRESS]: "default",
    [TodoStatus.DONE]: "secondary",
    [TodoStatus.ARCHIVED]: "outline",
  };

const priorityBorder: Record<TodoPriority, string> = {
  [TodoPriority.NONE]: "border-l",
  [TodoPriority.LOW]: "border-l-4 border-l-emerald-500",
  [TodoPriority.MEDIUM]: "border-l-4 border-l-amber-500",
  [TodoPriority.HIGH]: "border-l-4 border-l-rose-500",
};

interface TodoCardProps {
  todo: Todo;
}

export function TodoCard({ todo }: TodoCardProps) {
  const [dialogOpen, setDialogOpen] = useState(false);
  const deleteTodo = useDeleteTodo();
  const updateTodo = useUpdateTodo();

  function formatDate(dateStr: string | null) {
    return formatDateOnly(dateStr);
  }

  function handleDelete() {
    deleteTodo.mutate(todo.uuid_, {
      onSuccess: () => setDialogOpen(false),
    });
  }

  function handleToggleDone() {
    const nextStatus =
      todo.status === TodoStatus.DONE ? TodoStatus.TODO : TodoStatus.DONE;
    updateTodo.mutate({ uuid: todo.uuid_, data: { status: nextStatus } });
  }

  const isToggling = updateTodo.isPending;

  const isDone = todo.status === TodoStatus.DONE;

  return (
    <Card
      className={cn(
        priorityBorder[todo.priority],
        isDone ? "opacity-60" : "",
        "transition-opacity duration-300",
      )}
    >
      <CardHeader className="pb-2">
        <div className="flex items-start gap-3">
          <button
            type="button"
            className="mt-0.5 shrink-0 text-muted-foreground hover:text-primary transition-colors"
            onClick={handleToggleDone}
            disabled={isToggling}
            aria-label={
              isDone ? "Marcar como pendente" : "Marcar como concluído"
            }
          >
            {isDone ? (
              <CheckCircle2 className="h-5 w-5 text-emerald-500" />
            ) : (
              <Circle className="h-5 w-5" />
            )}
          </button>
          <div className="flex-1 min-w-0">
            <CardTitle
              className={cn(
                "text-base",
                isDone ? "line-through text-muted-foreground" : "",
              )}
            >
              {todo.name}
            </CardTitle>
          </div>
          <div className="flex items-center gap-1 shrink-0">
            <Button variant="ghost" size="icon" asChild aria-label="Editar">
              <Link to={`/todos/${todo.uuid_}/edit`}>
                <Pencil className="h-4 w-4" />
              </Link>
            </Button>
            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="ghost" size="icon" aria-label="Excluir">
                  <Trash2 className="h-4 w-4 text-destructive" />
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Excluir tarefa</DialogTitle>
                  <DialogDescription>
                    Tem certeza que deseja excluir &ldquo;{todo.name}&rdquo;?
                    Esta ação não pode ser desfeita.
                  </DialogDescription>
                </DialogHeader>
                <DialogFooter>
                  <Button
                    variant="outline"
                    onClick={() => setDialogOpen(false)}
                  >
                    Cancelar
                  </Button>
                  <Button
                    variant="destructive"
                    onClick={handleDelete}
                    disabled={deleteTodo.isPending}
                  >
                    {deleteTodo.isPending ? "Excluindo..." : "Excluir"}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </div>
      </CardHeader>
      {todo.description && (
        <CardContent className="pb-2 pt-0">
          <p className="text-sm text-muted-foreground line-clamp-2">
            {todo.description}
          </p>
        </CardContent>
      )}
      <CardFooter className="flex flex-wrap gap-2">
        <Badge variant={statusVariants[todo.status]}>
          {statusLabels[todo.status]}
        </Badge>
        {todo.priority !== TodoPriority.NONE && (
          <Badge variant={priorityVariants[todo.priority]}>
            {priorityLabels[todo.priority]}
          </Badge>
        )}
        {todo.due_date && (
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <Calendar className="h-3 w-3" />
            {formatDate(todo.due_date)}
          </div>
        )}
      </CardFooter>
    </Card>
  );
}
