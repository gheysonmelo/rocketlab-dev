import { CalendarDays, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

const MONTHS = [
  'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
  'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro',
]
const WEEKDAYS = ['D', 'S', 'T', 'Q', 'Q', 'S', 'S']

const pad = (n: number) => String(n).padStart(2, '0')
const toIso = (year: number, month: number, day: number) => `${year}-${pad(month + 1)}-${pad(day)}`

interface DatePickerProps {
  /** Data ISO (aaaa-mm-dd) ou "" quando vazia. */
  value: string
  onChange: (value: string) => void
  label: string
  /** Ano em que o calendário abre quando não há data (ex.: o ano de lançamento digitado). */
  defaultYear?: number
}

/**
 * Seletor de data no visual do CineFILO. O calendário do <input type="date"> é
 * desenhado pelo navegador e não aceita estilo, então este é um calendário próprio.
 */
export function DatePicker({ value, onChange, label, defaultYear }: DatePickerProps) {
  const [today] = useState(() => new Date())
  const initial = value ? new Date(`${value}T00:00:00`) : null
  const [open, setOpen] = useState(false)
  const [view, setView] = useState(() => ({
    year: initial?.getFullYear() ?? defaultYear ?? today.getFullYear(),
    month: initial?.getMonth() ?? (defaultYear ? 0 : today.getMonth()),
  }))
  const rootRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    const close = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', close)
    return () => document.removeEventListener('mousedown', close)
  }, [open])

  function toggle() {
    if (!open && !value && defaultYear) setView({ year: defaultYear, month: 0 })
    setOpen(!open)
  }

  function shift(months: number) {
    setView(({ year, month }) => {
      const date = new Date(year, month + months, 1)
      return { year: date.getFullYear(), month: date.getMonth() }
    })
  }

  function choose(iso: string) {
    onChange(iso)
    setOpen(false)
  }

  const firstWeekday = new Date(view.year, view.month, 1).getDay()
  const daysInMonth = new Date(view.year, view.month + 1, 0).getDate()
  const cells = [...Array(firstWeekday).fill(null), ...Array.from({ length: daysInMonth }, (_, i) => i + 1)]
  const todayIso = toIso(today.getFullYear(), today.getMonth(), today.getDate())
  const navButton = 'grid size-8 place-items-center rounded-full text-petrol hover:bg-tertiary'

  return (
    <div ref={rootRef} className="relative" onKeyDown={(event) => event.key === 'Escape' && setOpen(false)}>
      <button
        type="button"
        aria-label={label}
        aria-haspopup="dialog"
        aria-expanded={open}
        onClick={toggle}
        className={`flex h-[42px] w-full items-center justify-between gap-2 rounded-2xl border bg-primary px-4 text-left text-sm transition hover:border-petrol/60 focus:outline-none focus-visible:ring-2 focus-visible:ring-tertiary ${
          open ? 'border-petrol ring-2 ring-tertiary' : 'border-line'
        } ${value ? 'text-title' : 'text-muted'}`}
      >
        {initial ? initial.toLocaleDateString('pt-BR') : 'dd/mm/aaaa'}
        <CalendarDays className="size-4 shrink-0 text-petrol" aria-hidden="true" />
      </button>

      {open && (
        <div
          role="dialog"
          aria-label={`Calendário: ${label}`}
          className="absolute left-0 z-30 mt-2 w-72 rounded-3xl border border-line bg-primary p-4 shadow-xl"
        >
          <div className="flex items-center justify-between pb-3">
            <div className="flex">
              <button type="button" className={navButton} onClick={() => shift(-12)} aria-label="Ano anterior">
                <ChevronsLeft className="size-4" />
              </button>
              <button type="button" className={navButton} onClick={() => shift(-1)} aria-label="Mês anterior">
                <ChevronLeft className="size-4" />
              </button>
            </div>
            <span className="text-sm font-semibold text-title">
              {MONTHS[view.month]} {view.year}
            </span>
            <div className="flex">
              <button type="button" className={navButton} onClick={() => shift(1)} aria-label="Próximo mês">
                <ChevronRight className="size-4" />
              </button>
              <button type="button" className={navButton} onClick={() => shift(12)} aria-label="Próximo ano">
                <ChevronsRight className="size-4" />
              </button>
            </div>
          </div>

          <div className="grid grid-cols-7 gap-1 text-center text-xs font-medium text-muted">
            {WEEKDAYS.map((day, index) => (
              <span key={index} className="py-1">
                {day}
              </span>
            ))}
            {cells.map((day, index) => {
              if (day === null) return <span key={`empty-${index}`} />
              const iso = toIso(view.year, view.month, day)
              const selected = iso === value
              return (
                <button
                  key={iso}
                  type="button"
                  onClick={() => choose(iso)}
                  aria-pressed={selected}
                  aria-label={new Date(`${iso}T00:00:00`).toLocaleDateString('pt-BR', { dateStyle: 'long' })}
                  className={`grid aspect-square place-items-center rounded-full text-sm transition ${
                    selected
                      ? 'bg-secondary font-semibold text-title'
                      : iso === todayIso
                        ? 'text-petrol ring-1 ring-petrol/50 hover:bg-tertiary'
                        : 'text-text hover:bg-tertiary'
                  }`}
                >
                  {day}
                </button>
              )
            })}
          </div>

          <div className="mt-3 flex justify-between border-t border-line pt-3 text-sm">
            <button type="button" onClick={() => choose('')} className="rounded-full px-3 py-1 text-muted hover:bg-card">
              Limpar
            </button>
            <button type="button" onClick={() => choose(todayIso)} className="rounded-full px-3 py-1 font-medium text-petrol hover:bg-tertiary">
              Hoje
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
