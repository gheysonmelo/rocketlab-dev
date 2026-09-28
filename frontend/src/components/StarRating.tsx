import { formatStars, MAX_STARS, starFills } from '@/lib/rating'

const STAR_PATH = 'M12 2.5l2.9 6.1 6.6.8-4.9 4.6 1.3 6.6L12 17.3l-5.9 3.3 1.3-6.6-4.9-4.6 6.6-.8z'

/**
 * Estrela com preenchimento fracionado: uma estrela vazia por baixo e uma cheia
 * por cima, recortada na largura exata da fração (0,4 = 40% cheia). O contorno
 * mantém o verde-limão legível sobre fundo claro.
 */
export function StarIcon({ fill, className = 'size-4' }: { fill: number; className?: string }) {
  return (
    <span className={`relative inline-block shrink-0 ${className}`} aria-hidden="true">
      <svg viewBox="0 0 24 24" className="absolute inset-0 size-full fill-line stroke-muted/60">
        <path d={STAR_PATH} />
      </svg>
      <span className="absolute inset-y-0 left-0 overflow-hidden" style={{ width: `${fill * 100}%` }}>
        <svg viewBox="0 0 24 24" className="h-full w-auto max-w-none fill-secondary stroke-slate/70">
          <path d={STAR_PATH} />
        </svg>
      </span>
    </span>
  )
}

/** Nota em estrelas (0 a 5), somente leitura. 4,4 = quatro cheias e uma 40% cheia. */
export function StarRating({ value, className }: { value: number; className?: string }) {
  return (
    <span
      role="img"
      aria-label={`${formatStars(value)} de ${MAX_STARS} estrelas`}
      className="inline-flex items-center gap-0.5"
    >
      {starFills(value).map((fill, index) => (
        <StarIcon key={index} fill={fill} className={className} />
      ))}
    </span>
  )
}
