import { Check, ChevronDown } from 'lucide-react'
import { useEffect, useId, useRef, useState, type KeyboardEvent } from 'react'

export interface SelectOption<T extends string | number> {
  value: T
  label: string
}

interface SelectProps<T extends string | number> {
  value: T
  options: SelectOption<T>[]
  onChange: (value: T) => void
  label: string
  className?: string
  /** Lado em que a lista abre ("top" para campos no rodapé da página). */
  placement?: 'top' | 'bottom'
}

/**
 * Dropdown no visual do CineFILO. A lista de um <select> nativo é desenhada pelo
 * sistema e não aceita estilo, então este é um listbox próprio (padrão ARIA):
 * abre com clique, Enter, espaço ou seta; navega com as setas; Esc fecha.
 */
export function Select<T extends string | number>({
  value,
  options,
  onChange,
  label,
  className = '',
  placement = 'top',
}: SelectProps<T>) {
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(0)
  const rootRef = useRef<HTMLDivElement>(null)
  const listId = useId()
  const selected = options.find((option) => option.value === value)

  // Fecha ao clicar fora.
  useEffect(() => {
    if (!open) return
    const close = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', close)
    return () => document.removeEventListener('mousedown', close)
  }, [open])

  function openList() {
    setActive(Math.max(options.findIndex((option) => option.value === value), 0))
    setOpen(true)
  }

  function choose(index: number) {
    onChange(options[index].value)
    setOpen(false)
  }

  function handleKeyDown(event: KeyboardEvent) {
    if (!open) {
      if (['Enter', ' ', 'ArrowDown', 'ArrowUp'].includes(event.key)) {
        event.preventDefault()
        openList()
      }
      return
    }
    if (event.key === 'Escape') setOpen(false)
    else if (event.key === 'ArrowDown') setActive((index) => Math.min(index + 1, options.length - 1))
    else if (event.key === 'ArrowUp') setActive((index) => Math.max(index - 1, 0))
    else if (event.key === 'Enter' || event.key === ' ') choose(active)
    else return
    event.preventDefault()
  }

  return (
    <div ref={rootRef} className={`relative ${className}`}>
      <button
        type="button"
        role="combobox"
        aria-label={label}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={listId}
        onClick={() => (open ? setOpen(false) : openList())}
        onKeyDown={handleKeyDown}
        className={`flex h-10 w-full items-center justify-between gap-2 rounded-full border bg-primary pr-3 pl-4 text-sm text-title shadow-sm transition hover:border-petrol/60 focus:outline-none focus-visible:ring-2 focus-visible:ring-tertiary ${
          open ? 'border-petrol ring-2 ring-tertiary' : 'border-line'
        }`}
      >
        <span className="truncate">{selected?.label}</span>
        <ChevronDown
          className={`size-4 shrink-0 text-petrol transition-transform ${open ? 'rotate-180' : ''}`}
          aria-hidden="true"
        />
      </button>

      {open && (
        <ul
          id={listId}
          role="listbox"
          aria-label={label}
          className={`absolute right-0 z-20 max-h-64 min-w-full overflow-auto rounded-2xl border border-line bg-primary p-1.5 shadow-xl ${
            placement === 'top' ? 'bottom-full mb-2' : 'top-full mt-2'
          }`}
        >
          {options.map((option, index) => {
            const isSelected = option.value === value
            return (
              <li
                key={option.value}
                role="option"
                aria-selected={isSelected}
                onMouseEnter={() => setActive(index)}
                onMouseDown={(event) => {
                  event.preventDefault() // mantém o foco no botão
                  choose(index)
                }}
                className={`flex cursor-pointer items-center justify-between gap-3 rounded-xl px-3 py-2 text-sm transition ${
                  index === active ? 'bg-tertiary text-petrol' : 'text-text'
                } ${isSelected ? 'font-semibold' : ''}`}
              >
                {option.label}
                {isSelected && <Check className="size-4 text-petrol" aria-hidden="true" />}
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
