import { apiClient } from "./client";
import type {
  AdminTodo,
  AdminUser,
  AdminUserList,
  AdminUserFilters,
  AdminUserUpdateData,
  AdminTodoFilters,
  AdminTodoList,
  AdminTodoUpdateData,
  AdminTokenList,
  AdminTokenFilters,
} from "@/types";

/**
 * Helper to convert a flat filters object into a URLSearchParams instance,
 * removing undefined, null, or empty string values automatically.
 */
function buildQueryParams(filters: object): URLSearchParams {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value !== undefined && value !== null && value !== "") {
      params.append(key, String(value));
    }
  }
  return params;
}

/* ============================================================================
   Admin User Endpoints
   ============================================================================ */

export async function listAdminUsers(
  filters: AdminUserFilters = {},
): Promise<AdminUserList> {
  const params = buildQueryParams(filters);
  const { data } = await apiClient.get<AdminUserList>(`/admin/users?${params}`);
  return data;
}

export async function getAdminUser(uuid: string): Promise<AdminUser> {
  const { data } = await apiClient.get<AdminUser>(`/admin/users/${uuid}`);
  return data;
}

export async function updateAdminUser(
  uuid: string,
  data: AdminUserUpdateData,
): Promise<AdminUser> {
  const { data: response } = await apiClient.patch<AdminUser>(
    `/admin/users/${uuid}`,
    data,
  );
  return response;
}

export async function deleteAdminUser(uuid: string): Promise<void> {
  await apiClient.delete(`/admin/users/${uuid}`);
}

/* ============================================================================
   Admin Todo Endpoints
   ============================================================================ */

export async function listAdminTodos(
  filters: AdminTodoFilters = {},
): Promise<AdminTodoList> {
  const params = buildQueryParams(filters);
  const { data } = await apiClient.get<AdminTodoList>(`/admin/todos?${params}`);
  return data;
}

export async function updateAdminTodo(
  uuid: string,
  data: AdminTodoUpdateData,
): Promise<AdminTodo> {
  const { data: response } = await apiClient.patch<AdminTodo>(
    `/admin/todos/${uuid}`,
    data,
  );
  return response;
}

export async function deleteAdminTodo(uuid: string): Promise<void> {
  await apiClient.delete(`/admin/todos/${uuid}`);
}

/* ============================================================================
   Admin Token Endpoints
   ============================================================================ */

export async function listTokens(
  filters: AdminTokenFilters = {},
): Promise<AdminTokenList> {
  const params = buildQueryParams(filters);
  const { data } = await apiClient.get<AdminTokenList>(
    `/admin/tokens/?${params}`,
  );
  return data;
}

export async function revokeToken(id: number): Promise<void> {
  await apiClient.patch(`/admin/tokens/${id}/revoke`);
}

export async function deleteToken(id: number): Promise<void> {
  await apiClient.delete(`/admin/tokens/${id}`);
}
