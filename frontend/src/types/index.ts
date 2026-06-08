export interface User {
  uuid_: string;
  email: string;
  username: string;
  is_superuser: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  email: string;
  username: string;
  password: string;
  confirm_password: string;
}

export const TodoStatus = {
  TODO: "TODO",
  IN_PROGRESS: "IN_PROGRESS",
  DONE: "DONE",
  ARCHIVED: "ARCHIVED",
} as const;

export type TodoStatus = (typeof TodoStatus)[keyof typeof TodoStatus];

export const TodoPriority = {
  NONE: "NONE",
  LOW: "LOW",
  MEDIUM: "MEDIUM",
  HIGH: "HIGH",
} as const;

export type TodoPriority = (typeof TodoPriority)[keyof typeof TodoPriority];

export interface Todo {
  uuid_: string;
  name: string;
  description: string | null;
  status: TodoStatus;
  priority: TodoPriority;
  due_date: string | null;
  created_at: string;
  updated_at: string;
  user_uuid: string;
}

export interface TodoCreate {
  name: string;
  description?: string;
  priority?: TodoPriority;
  due_date?: string | null;
}

export interface TodoUpdate {
  name?: string;
  description?: string | null;
  status?: TodoStatus;
  priority?: TodoPriority;
  due_date?: string | null;
}

export interface TodoListResponse {
  result: Todo[];
  total: number;
  offset: number;
  limit: number;
}

export interface TodoListFilters {
  status?: TodoStatus;
  priority?: TodoPriority;
  search?: string;
  offset?: number;
  limit?: number;
}

export interface ApiError {
  detail: string;
}

// =============================
// Admin Types
// =============================

export interface AdminUser {
  id: number;
  uuid_: string;
  username: string;
  email: string;
  status: string;
  is_superuser: boolean;
  last_login_at: string | null;
  deleted_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface AdminUserList {
  result: AdminUser[];
  total: number;
  offset: number;
  limit: number;
}

export interface AdminUserFilters {
  username?: string;
  email?: string;
  status?: string;
  is_superuser?: boolean;
  include_deleted?: boolean;
  created_after?: string;
  created_before?: string;
  order_by?: "id" | "username" | "created_at" | "updated_at" | "deleted_at";
  order_desc?: boolean;
  offset?: number;
  limit?: number;
}

export interface AdminUserUpdateData {
  username?: string;
  email?: string;
  new_password?: string;
  status?: string;
  is_superuser?: boolean;
}

export interface AdminTodo {
  id: number;
  uuid_: string;
  name: string;
  description: string | null;
  status: TodoStatus;
  priority: TodoPriority;
  due_date: string | null;
  user_uuid: string;
  username?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AdminTodoList {
  result: AdminTodo[];
  total: number;
  offset: number;
  limit: number;
}

export interface AdminTodoUpdateData {
  name?: string;
  description?: string | null;
  status?: TodoStatus;
  priority?: TodoPriority;
  due_date?: string | null;
}

export interface AdminTodoFilters {
  status?: TodoStatus;
  priority?: TodoPriority;
  search?: string;
  user_uuid?: string;
  created_after?: string;
  created_before?: string;
  order_by?: "created_at" | "updated_at" | "due_date" | "priority" | "status";
  order_desc?: boolean;
  offset?: number;
  limit?: number;
}

export interface AdminToken {
  id: number;
  user_uuid: string;
  refresh_token: string;
  is_revoked: boolean;
  expires_at: string;
  created_at: string;
}

export interface AdminTokenList {
  result: AdminToken[];
  total: number;
  offset: number;
  limit: number;
}

export interface AdminTokenFilters {
  user_uuid?: string;
  is_revoked?: boolean;
  expires_after?: string;
  expires_before?: string;
  created_after?: string;
  created_before?: string;
  order_by?: "id" | "user_uuid" | "is_revoked" | "expires_at" | "created_at";
  order_desc?: boolean;
  offset?: number;
  limit?: number;
}
