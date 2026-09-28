import { formatStars, MAX_STARS, starFills } from '@/lib/rating'

// Estrela com pontas e cantos arredondados (curvas nas pontas + stroke-linejoin round).
const STAR_PATH =
  'M11.525 2.295a.53.53 0 0 1 .95 0l2.31 4.679a2.123 2.123 0 0 0 1.595 1.16l5.166.756a.53.53 0 0 1 .294.904l-3.736 3.638a2.123 2.123 0 0 0-.611 1.878l.882 5.14a.53.53 0 0 1-.771.56l-4.618-2.428a2.122 2.122 0 0 0-1.973 0L6.396 21.01a.53.53 0 0 1-.77-.56l.881-5.139a2.122 2.122 0 0 0-.611-1.879L2.16 9.795a.53.53 0 0 1 .294-.906l5.165-.755a2.122 2.122 0 0 0 1.597-1.16z'

/**
 * Estrela com preenchimento fracionado: uma estrela vazia por baixo e uma cheia
 * por cima, recortada na largura exata da fração (0,4 = 40% cheia). O contorno
 * mantém o verde-limão legível sobre fundo claro.
 */
export function StarIcon({ fill, className = 'size-4' }: { fill: number; className?: string }) {
  return (
    <span className={`relative inline-block shrink-0 ${className}`} aria-hidden="true">
      <svg viewBox="0 0 24 24" className="absolute inset-0 size-full fill-line stroke-muted/60 [stroke-linejoin:round] [stroke-width:1.5]">
        <path d={STAR_PATH} />
      </svg>
      <span className="absolute inset-y-0 left-0 overflow-hidden" style={{ width: `${fill * 100}%` }}>
        <svg viewBox="0 0 24 24" className="h-full w-auto max-w-none fill-secondary stroke-slate/70 [stroke-linejoin:round] [stroke-width:1.5]">
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
