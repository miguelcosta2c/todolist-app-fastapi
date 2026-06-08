import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryProvider } from "@/providers/QueryProvider";
import { AuthProvider } from "@/providers/AuthProvider";
import { ThemeProvider } from "@/providers/ThemeProvider";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { ProtectedRoute } from "@/components/layout/ProtectedRoute";
import { AdminRoute } from "@/components/layout/AdminRoute";
import { Layout } from "@/components/layout/Layout";
import { AdminLayout } from "@/components/admin/AdminLayout";
import { Login } from "@/pages/Login";
import { Register } from "@/pages/Register";
import { Dashboard } from "@/pages/Dashboard";
import { TodoNew } from "@/pages/TodoNew";
import { TodoEdit } from "@/pages/TodoEdit";
import { AdminDashboard } from "@/pages/admin/Dashboard";
import { AdminUsers } from "@/pages/admin/Users";
import { AdminTodos } from "@/pages/admin/Todos";
import { AdminTokens } from "@/pages/admin/Tokens";
import { Toaster } from "@/components/ui/sonner";
import { Button } from "@/components/ui/button";
import { FileQuestion } from "lucide-react";
import { Link } from "react-router-dom";

function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 p-8">
      <FileQuestion className="h-16 w-16 text-muted-foreground" />
      <h1 className="text-2xl font-bold">Página não encontrada</h1>
      <p className="text-sm text-muted-foreground">
        A página que você procura não existe.
      </p>
      <Button asChild>
        <Link to="/">Voltar ao início</Link>
      </Button>
    </div>
  );
}

export function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <QueryProvider>
          <AuthProvider>
            <BrowserRouter>
              <Routes>
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
                <Route element={<ProtectedRoute />}>
                  <Route element={<Layout />}>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/todos/new" element={<TodoNew />} />
                    <Route path="/todos/:uuid/edit" element={<TodoEdit />} />
                    <Route element={<AdminRoute />}>
                      <Route element={<AdminLayout />}>
                        <Route path="/admin" element={<AdminDashboard />} />
                        <Route path="/admin/users" element={<AdminUsers />} />
                        <Route path="/admin/todos" element={<AdminTodos />} />
                        <Route path="/admin/tokens" element={<AdminTokens />} />
                      </Route>
                    </Route>
                  </Route>
                </Route>
                <Route path="/404" element={<NotFound />} />
                <Route path="*" element={<NotFound />} />
              </Routes>
            </BrowserRouter>
            <Toaster />
          </AuthProvider>
        </QueryProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}
