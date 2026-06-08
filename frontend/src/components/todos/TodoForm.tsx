import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { TodoPriority } from "@/types";
import { Loader2 } from "lucide-react";

const todoSchema = z.object({
  name: z.string().min(1, "Nome é obrigatório").max(100),
  description: z.string().max(500).optional(),
  priority: z.nativeEnum(TodoPriority),
  due_date: z.string().optional(),
});

export type TodoFormData = z.infer<typeof todoSchema>;

interface TodoFormProps {
  defaultValues?: Partial<TodoFormData>;
  onSubmit: (data: TodoFormData) => Promise<void>;
  isSubmitting: boolean;
  mode: "create" | "edit";
}

export function TodoForm({
  defaultValues,
  onSubmit,
  isSubmitting,
  mode,
}: TodoFormProps) {
  const navigate = useNavigate();
  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<TodoFormData>({
    resolver: zodResolver(todoSchema),
    defaultValues: {
      name: "",
      description: "",
      priority: TodoPriority.NONE,
      due_date: "",
      ...defaultValues,
    },
  });

  // eslint-disable-next-line react-hooks/incompatible-library
  const priority = watch("priority");

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div className="space-y-2">
        <Label htmlFor="name">Nome</Label>
        <Input id="name" placeholder="Nome da tarefa" {...register("name")} />
        {errors.name && (
          <p className="text-sm text-destructive">{errors.name.message}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="description">Descrição</Label>
        <Textarea
          id="description"
          placeholder="Descrição da tarefa (opcional)"
          rows={4}
          {...register("description")}
        />
        {errors.description && (
          <p className="text-sm text-destructive">
            {errors.description.message}
          </p>
        )}
      </div>

      <div className="space-y-2">
        <Label>Prioridade</Label>
        <Select
          value={priority}
          onValueChange={(value) => setValue("priority", value as TodoPriority)}
        >
          <SelectTrigger>
            <SelectValue placeholder="Selecione a prioridade" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={TodoPriority.NONE}>Nenhuma</SelectItem>
            <SelectItem value={TodoPriority.LOW}>Baixa</SelectItem>
            <SelectItem value={TodoPriority.MEDIUM}>Média</SelectItem>
            <SelectItem value={TodoPriority.HIGH}>Alta</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="due_date">Data de Vencimento</Label>
        <Input id="due_date" type="date" {...register("due_date")} />
      </div>

      <div className="flex gap-4">
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          {mode === "create" ? "Criar Tarefa" : "Salvar Alterações"}
        </Button>
        <Button type="button" variant="outline" onClick={() => navigate("/")}>
          Cancelar
        </Button>
      </div>
    </form>
  );
}
