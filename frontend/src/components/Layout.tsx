import { Clapperboard, Film, SquarePlus, type LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'
import { Link, NavLink, Outlet } from 'react-router'

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

function Sidebar() {
  return (
    <aside className="hidden w-60 shrink-0 flex-col gap-10 px-6 py-8 lg:flex">
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
    </aside>
  )
}

export function Layout() {
  return (
    <div className="flex min-h-dvh">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col px-4 pb-6 lg:pr-8">
        <header className="flex items-center justify-between py-6 lg:justify-end">
          <div className="lg:hidden">
            <Logo />
          </div>
          <div className="flex items-center gap-3">
            <div className="text-right leading-tight">
              <p className="text-sm font-medium text-title">Administrador</p>
              <p className="text-xs text-muted">Catálogo de filmes</p>
            </div>
            <span className="grid size-11 place-items-center rounded-full bg-tertiary text-sm font-semibold text-petrol">
              AD
            </span>
          </div>
        </header>
        <main className="flex-1 rounded-3xl bg-primary p-5 shadow-sm sm:p-8">
          <Outlet />
        </main>
        <footer className="pt-6 text-center text-sm text-petrol">
          CineFILO<sup>®</sup> | Onde filmes são vistos, notas acontecem
        </footer>
      </div>
    </div>
  )
}
