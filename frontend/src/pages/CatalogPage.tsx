import { Clapperboard, Film, Search } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { useSearchParams } from 'react-router'
import { DEFAULT_PAGE_SIZE, useCatalog } from '@/api/queries'
import { PillLink } from '@/components/Layout'
import { MovieCard } from '@/components/MovieCard'
import { Pagination } from '@/components/Pagination'
import { PAGE_SIZES } from '@/lib/pagination'

/** Busca pelo título; Enter aplica a busca na URL (?q=). */
function SearchBar({ initial, onSearch }: { initial: string; onSearch: (q: string) => void }) {
  const [term, setTerm] = useState(initial)

  function submit(event: FormEvent) {
    event.preventDefault()
    onSearch(term.trim())
  }

  return (
    <form role="search" onSubmit={submit} className="relative w-full sm:w-56">
      <input
        type="search"
        value={term}
        onChange={(event) => setTerm(event.target.value)}
        placeholder="Buscar"
        aria-label="Buscar filmes pelo título"
        className="h-10 w-full rounded-full border border-line bg-primary pr-10 pl-4 text-sm text-title placeholder:text-muted focus:border-petrol focus:outline-none"
      />
      <button
        type="submit"
        aria-label="Buscar"
        className="absolute top-1/2 right-3 -translate-y-1/2 text-muted"
      >
        <Search className="size-4" />
      </button>
    </form>
  )
}

/** Catálogo paginado. Busca e página ficam na URL (?q=&page=): voltar e links funcionam. */
export function CatalogPage() {
  const [params, setParams] = useSearchParams()
  const q = params.get('q') ?? ''
  const page = Math.max(Number(params.get('page')) || 1, 1)
  const requestedSize = Number(params.get('page_size'))
  const pageSize = (PAGE_SIZES as readonly number[]).includes(requestedSize)
    ? requestedSize
    : DEFAULT_PAGE_SIZE
  const catalog = useCatalog(q, page, pageSize)

  /** Atualiza a URL; trocar busca ou tamanho da página volta para a página 1. */
  function update(changes: Record<string, string | number | null>) {
    const next = new URLSearchParams(params)
    for (const [key, value] of Object.entries(changes)) {
      if (value === null || value === '') next.delete(key)
      else next.set(key, String(value))
    }
    setParams(next)
    window.scrollTo({ top: 0 })
  }

  return (
    <section className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="flex items-center gap-2 text-3xl font-semibold text-title">
            <Film className="size-8" strokeWidth={1.75} aria-hidden="true" />
            {q ? `Resultados para “${q}”` : 'Filmes'}
          </h1>
          {catalog.data && (
            <p className="pt-1 text-sm text-muted">
              {catalog.data.total.toLocaleString('pt-BR')} filme(s) no catálogo
            </p>
          )}
        </div>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <SearchBar key={q} initial={q} onSearch={(term) => update({ q: term, page: null })} />
          <PillLink to="/filmes/novo" icon={Clapperboard}>
            Cadastrar filme
          </PillLink>
        </div>
      </div>

      {catalog.isPending && <p className="text-muted">Carregando filmes…</p>}
      {catalog.isError && <p className="text-danger">{catalog.error.message}</p>}
      {catalog.data?.items.length === 0 && (
        <p className="text-muted">Nenhum filme encontrado. Tente outro termo.</p>
      )}

      {catalog.data && catalog.data.items.length > 0 && (
        <>
          <ul
            className={`grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 ${
              catalog.isPlaceholderData ? 'opacity-60' : ''
            }`}
          >
            {catalog.data.items.map((movie) => (
              <li key={movie.sk_movie_id}>
                <MovieCard movie={movie} />
              </li>
            ))}
          </ul>
          <Pagination
            data={catalog.data}
            onPageChange={(nextPage) => update({ page: nextPage })}
            onPageSizeChange={(size) => update({ page_size: size, page: null })}
          />
        </>
      )}
    </section>
  )
}
