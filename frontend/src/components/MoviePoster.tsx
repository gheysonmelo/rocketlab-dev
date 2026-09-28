import { Film } from 'lucide-react'
import { useState } from 'react'
import { tmdbImage } from '@/lib/format'

interface MoviePosterProps {
  url: string | null
  title: string
  size?: 'w342' | 'w500'
  className?: string
}

/** Pôster 2:3, com substituto para filmes sem imagem (~8 mil) ou com link quebrado. */
export function MoviePoster({ url, title, size = 'w342', className = '' }: MoviePosterProps) {
  const [failed, setFailed] = useState(false)
  const src = tmdbImage(url, size)

  if (src && !failed) {
    return (
      <img
        src={src}
        alt={`Pôster de ${title}`}
        loading="lazy"
        onError={() => setFailed(true)}
        className={`aspect-[2/3] w-full object-cover ${className}`}
      />
    )
  }
  return (
    <div
      className={`flex aspect-[2/3] w-full items-start justify-center bg-gradient-to-b from-tertiary to-[#8fbccb] pt-10 text-primary ${className}`}
    >
      <Film className="size-10 opacity-80" aria-hidden="true" />
    </div>
  )
}
