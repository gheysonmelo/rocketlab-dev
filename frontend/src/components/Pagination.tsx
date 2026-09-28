import { ChevronLeft, ChevronRight } from 'lucide-react'
import type { Page } from '@/api/types'
import { PAGE_SIZES, pageItems } from '@/lib/pagination'
import { Select } from './Select'

interface PaginationProps {
  /** Envelope devolvido pela API: page, pages, page_size e total. */
  data: Page<unknown>
  onPageChange: (page: number) => void
  onPageSizeChange: (pageSize: number) => void
}

const arrowClasses =
  'inline-flex h-9 items-center gap-1 rounded-full border border-line px-3 text-sm text-petrol hover:bg-tertiary disabled:pointer-events-none disabled:opacity-40'

export function Pagination({ data, onPageChange, onPageSizeChange }: PaginationProps) {
  const { page, pages, page_size: pageSize, total } = data
  const first = total ? (page - 1) * pageSize + 1 : 0
  const last = Math.min(page * pageSize, total)

  return (
    <div className="flex flex-col items-center gap-4 pt-6 sm:flex-row sm:justify-between">
      <p className="text-sm text-muted">
        {first.toLocaleString('pt-BR')}–{last.toLocaleString('pt-BR')} de{' '}
        {total.toLocaleString('pt-BR')} filmes
      </p>

      {pages > 1 && (
        <nav aria-label="Paginação" className="flex items-center gap-1.5">
          <button
            className={arrowClasses}
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1}
            aria-label="Página anterior"
          >
            <ChevronLeft className="size-4" />
          </button>
          {pageItems(page, pages).map((item, index) =>
            item === 'gap' ? (
              <span key={`gap-${index}`} className="px-1 text-muted" aria-hidden="true">
                …
              </span>
            ) : (
              <button
                key={item}
                onClick={() => onPageChange(item)}
                aria-current={item === page ? 'page' : undefined}
                aria-label={`Página ${item}`}
                className={`h-9 min-w-9 rounded-full px-3 text-sm transition ${
                  item === page
                    ? 'bg-secondary font-semibold text-title'
                    : 'text-text hover:bg-tertiary'
                }`}
              >
                {item.toLocaleString('pt-BR')}
              </button>
            ),
          )}
          <button
            className={arrowClasses}
            onClick={() => onPageChange(page + 1)}
            disabled={page >= pages}
            aria-label="Próxima página"
          >
            <ChevronRight className="size-4" />
          </button>
        </nav>
      )}

      <div className="flex items-center gap-2 text-sm text-muted">
        Por página
        <Select
          label="Filmes por página"
          value={pageSize}
          options={PAGE_SIZES.map((size) => ({ value: size, label: String(size) }))}
          onChange={onPageSizeChange}
          className="w-24"
        />
      </div>
    </div>
  )
}
