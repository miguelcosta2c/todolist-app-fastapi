import { NavLink } from 'react-router-dom'
import { LayoutDashboard, Users, ListTodo, KeyRound } from 'lucide-react'

const links = [
  { to: '/admin', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/admin/users', label: 'Usuários', icon: Users },
  { to: '/admin/todos', label: 'Tarefas', icon: ListTodo },
  { to: '/admin/tokens', label: 'Tokens', icon: KeyRound },
]

export function AdminSidebar() {
  return (
    <aside className="w-56 shrink-0">
      <nav className="space-y-1">
        {links.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/admin'}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
              }`
            }
          >
            <Icon className="h-4 w-4" />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
