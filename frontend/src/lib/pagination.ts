export const PAGE_SIZES = [12, 24, 48, 96] as const

type PageItem = number | 'gap'

/** Primeira, última e vizinhas da atual, com reticências. Ex.: (6, 20) -> 1 … 5 6 7 … 20 */
export function pageItems(current: number, total: number): PageItem[] {
  const pages = [...new Set([1, current - 1, current, current + 1, total])]
    .filter((page) => page >= 1 && page <= total)
    .sort((a, b) => a - b)
  const items: PageItem[] = []
  pages.forEach((page, index) => {
    const previous = pages[index - 1]
    if (previous !== undefined && page - previous === 2) items.push(previous + 1)
    else if (previous !== undefined && page - previous > 2) items.push('gap')
    items.push(page)
  })
  return items
}
