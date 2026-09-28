import { Clapperboard, Film, LogOut, SquarePlus, type LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'
import { Link, NavLink, Outlet, useNavigate } from 'react-router'
import { clearToken } from '@/api/auth'

function Logo({ className = '' }: { className?: string }) {
  return (
    <Link to="/" className={`text-3xl font-bold tracking-tight text-slate ${className}`}>
      Cine<span className="font-extrabold">FILO</span>
    </Link>
  )
}

/** Botão em pílula azul-claro do protótipo (ex.: "Novo pedido"). */
export function PillLink({
  to,
  icon: Icon,
  children,
}: {
  to: string
  icon: LucideIcon
  children: ReactNode
}) {
  return (
    <Link
      to={to}
      className="inline-flex h-10 items-center justify-center gap-2 rounded-full bg-tertiary px-5 text-sm font-medium text-petrol transition hover:bg-tertiary-strong"
    >
      <Icon className="size-5" strokeWidth={1.5} aria-hidden="true" />
      {children}
    </Link>
  )
}

const NAV = [
  { to: '/', label: 'Catálogo', icon: Film, end: true },
  { to: '/filmes/novo', label: 'Novo filme', icon: SquarePlus, end: false },
]

function useLogout() {
  const navigate = useNavigate()
  return () => {
    clearToken()
    navigate('/login', { replace: true })
  }
}

function Sidebar() {
  const logout = useLogout()
  return (
    <aside className="sticky top-0 hidden h-dvh w-60 shrink-0 flex-col gap-10 px-6 py-8 lg:flex">
      <Logo className="self-center" />
      <PillLink to="/filmes/novo" icon={Clapperboard}>
        Novo filme
      </PillLink>
      <nav className="flex flex-col gap-1" aria-label="Navegação principal">
        {NAV.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-full px-4 py-2.5 text-base transition ${
                isActive ? 'bg-secondary text-title' : 'text-muted hover:text-title'
              }`
            }
          >
            <Icon className="size-5" strokeWidth={1.5} aria-hidden="true" />
            {label}
          </NavLink>
        ))}
      </nav>
      <button
        type="button"
        onClick={logout}
        className="mt-auto flex items-center gap-3 rounded-full px-4 py-2.5 text-base text-muted transition hover:text-danger"
      >
        <LogOut className="size-5" strokeWidth={1.5} aria-hidden="true" /> Sair
      </button>
    </aside>
  )
}

/** Navegação do celular: barra fixa embaixo, no alcance do polegar. */
function MobileNav() {
  return (
    <nav
      aria-label="Navegação principal"
      className="fixed inset-x-3 bottom-3 z-40 flex justify-around rounded-full bg-primary/95 p-1.5 shadow-lg ring-1 ring-line backdrop-blur lg:hidden"
    >
      {NAV.map(({ to, label, icon: Icon, end }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          className={({ isActive }) =>
            `flex flex-1 items-center justify-center gap-2 rounded-full py-2.5 text-sm transition ${
              isActive ? 'bg-secondary font-medium text-title' : 'text-muted'
            }`
          }
        >
          <Icon className="size-5" strokeWidth={1.5} aria-hidden="true" />
          {label}
        </NavLink>
      ))}
    </nav>
  )
}

export function Layout() {
  const logout = useLogout()
  return (
    <div className="flex min-h-dvh">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col px-3 pb-24 sm:px-4 lg:pr-8 lg:pb-6">
        <header className="flex items-center justify-between gap-3 py-4 sm:py-6 lg:justify-end">
          <Logo className="text-2xl sm:text-3xl lg:hidden" />
          <div className="flex items-center gap-3">
            <div className="hidden text-right leading-tight sm:block">
              <p className="text-sm font-medium text-title">Administrador</p>
              <p className="text-xs text-muted">Catálogo de filmes</p>
            </div>
            <span className="grid size-10 place-items-center rounded-full bg-tertiary text-sm font-semibold text-petrol sm:size-11">
              AD
            </span>
            <button
              type="button"
              onClick={logout}
              aria-label="Sair"
              className="grid size-10 place-items-center rounded-full text-muted hover:bg-primary hover:text-danger lg:hidden"
            >
              <LogOut className="size-5" strokeWidth={1.5} />
            </button>
          </div>
        </header>
        <main className="flex-1 rounded-3xl bg-primary p-4 shadow-sm sm:p-8">
          <Outlet />
        </main>
        <footer className="pt-6 text-center text-sm text-petrol">
          CineFILO<sup>®</sup> | Onde filmes são vistos, notas acontecem
        </footer>
      </div>
      <MobileNav />
    </div>
  )
}
