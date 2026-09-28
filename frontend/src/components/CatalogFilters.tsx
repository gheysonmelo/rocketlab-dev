import { X } from 'lucide-react'
import { useState } from 'react'
import { useGenres, type CatalogFilters as Filters } from '@/api/queries'
import { MOVIE_STATUSES } from '@/api/types'
import { genreLabel } from '@/lib/format'
import { Select } from './Select'

interface CatalogFiltersProps {
  filters: Filters
  onChange: (changes: Partial<Filters>) => void
  onClear: () => void
}

/** Filtros do catálogo (gênero, status e ano), combináveis com a busca. */
export function CatalogFilters({ filters, onChange, onClear }: CatalogFiltersProps) {
  const genres = useGenres()
  const [year, setYear] = useState(filters.ano)
  const active = Boolean(filters.genero_id || filters.status || filters.ano)

  const genreOptions = [
    { value: '', label: 'Todos os gêneros' },
    ...[...(genres.data ?? [])]
      .map((genre) => ({ value: genre.sk_genre_id, label: genreLabel(genre.nome_genero) }))
      .sort((a, b) => a.label.localeCompare(b.label, 'pt-BR')),
  ]
  const statusOptions = [
    { value: '', label: 'Todos os status' },
    ...MOVIE_STATUSES.map((status) => ({ value: status, label: status })),
  ]

  // O ano é aplicado ao sair do campo ou com Enter, e só com 4 dígitos (ou vazio).
  function applyYear() {
    if (year === filters.ano) return
    if (year === '' || /^\d{4}$/.test(year)) onChange({ ano: year })
  }

  return (
    <div className="flex flex-col gap-3 rounded-2xl bg-card p-3 sm:flex-row sm:flex-wrap sm:items-center">
      <Select
        label="Filtrar por gênero"
        value={filters.genero_id}
        options={genreOptions}
        onChange={(genero_id) => onChange({ genero_id })}
        placement="bottom"
        className="sm:w-52"
      />
      <Select
        label="Filtrar por status"
        value={filters.status}
        options={statusOptions}
        onChange={(status) => onChange({ status })}
        placement="bottom"
        className="sm:w-48"
      />
      <input
        value={year}
        onChange={(event) => setYear(event.target.value.replace(/\D/g, '').slice(0, 4))}
        onBlur={applyYear}
        onKeyDown={(event) => event.key === 'Enter' && applyYear()}
        inputMode="numeric"
        placeholder="Ano (ex.: 2023)"
        aria-label="Filtrar por ano de lançamento"
        className="h-10 rounded-full border border-line bg-primary px-4 text-sm text-title shadow-sm placeholder:text-muted focus:border-petrol focus:ring-2 focus:ring-tertiary focus:outline-none sm:w-40"
      />
      {active && (
        <button
          type="button"
          onClick={() => {
            setYear('')
            onClear()
          }}
          className="inline-flex h-10 items-center justify-center gap-1.5 rounded-full px-4 text-sm text-petrol hover:bg-tertiary"
        >
          <X className="size-4" aria-hidden="true" /> Limpar filtros
        </button>
      )}
    </div>
  )
}
