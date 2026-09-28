/** Conversões entre a escala do banco (0 a 10) e estrelas (0 a 5). */

export const MAX_STARS = 5

/** Nota 0–10 -> estrelas 0–5 (ex.: 8,8 -> 4,4). */
export const toStars = (score: number) => Math.min(Math.max(score / 2, 0), MAX_STARS)

/** Estrelas em meia estrela (0,5–5) -> nota inteira 1–10 aceita pela API. */
export const starsToScore = (stars: number) => Math.round(stars * 2)

/** Fração preenchida de cada estrela. Ex.: 4,4 -> [1, 1, 1, 1, 0.4]. */
export function starFills(stars: number): number[] {
  return Array.from({ length: MAX_STARS }, (_, index) => {
    const fill = Math.min(Math.max(stars - index, 0), 1)
    return Math.round(fill * 100) / 100
  })
}

export const formatStars = (stars: number) =>
  stars.toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })
