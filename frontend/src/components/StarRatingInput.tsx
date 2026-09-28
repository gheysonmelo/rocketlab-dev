import { useState, type KeyboardEvent } from 'react'
import { formatStars, MAX_STARS, starFills } from '@/lib/rating'
import { StarIcon } from './StarRating'

const STEP = 0.5

/**
 * Nota em meia estrela, como no Letterboxd: a metade esquerda de cada estrela
 * vale x,5 e a direita x+1. Pelo teclado funciona como um slider (setas).
 */
export function StarRatingInput({
  value,
  onChange,
}: {
  value: number
  onChange: (stars: number) => void
}) {
  const [hover, setHover] = useState<number | null>(null)
  const shown = hover ?? value

  function handleKeyDown(event: KeyboardEvent) {
    const delta = { ArrowRight: STEP, ArrowUp: STEP, ArrowLeft: -STEP, ArrowDown: -STEP }[
      event.key
    ]
    if (delta === undefined) return
    event.preventDefault()
    onChange(Math.min(Math.max(value + delta, STEP), MAX_STARS))
  }

  return (
    <div className="flex items-center gap-3">
      <div
        role="slider"
        tabIndex={0}
        aria-label="Nota em estrelas"
        aria-valuemin={STEP}
        aria-valuemax={MAX_STARS}
        aria-valuenow={value || undefined}
        aria-valuetext={value ? `${formatStars(value)} estrelas` : 'Sem nota'}
        onKeyDown={handleKeyDown}
        onMouseLeave={() => setHover(null)}
        className="inline-flex gap-1 rounded-full p-1 focus:outline-none focus-visible:ring-2 focus-visible:ring-tertiary"
      >
        {starFills(shown).map((fill, index) => (
          <span key={index} className="relative">
            <StarIcon fill={fill} className="size-8" />
            {[index + STEP, index + 1].map((stars, half) => (
              <button
                key={stars}
                type="button"
                tabIndex={-1}
                aria-label={`${formatStars(stars)} estrelas`}
                onMouseEnter={() => setHover(stars)}
                onClick={() => onChange(stars)}
                className={`absolute inset-y-0 w-1/2 cursor-pointer ${half ? 'right-0' : 'left-0'}`}
              />
            ))}
          </span>
        ))}
      </div>
      <span className="min-w-10 text-lg font-semibold text-title">
        {shown ? formatStars(shown) : '—'}
      </span>
    </div>
  )
}
