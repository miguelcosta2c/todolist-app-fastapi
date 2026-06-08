import { Outlet } from 'react-router-dom'
import { AdminSidebar } from './AdminSidebar'

export function AdminLayout() {
  return (
    <div className="flex min-h-[calc(100vh-4rem)] gap-6 p-6">
      <AdminSidebar />
      <main className="flex-1">
        <Outlet />
      </main>
    </div>
  )
}
