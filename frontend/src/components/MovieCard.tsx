import { Clapperboard, Eye } from 'lucide-react'
import { Link } from 'react-router'
import type { MovieSummary } from '@/api/types'
import { formatStars, toStars } from '@/lib/rating'
import { MoviePoster } from './MoviePoster'
import { StarRating } from './StarRating'

/**
 * Card do catálogo, como no protótipo FILO: degradê sobre a foto destaca o nome
 * em branco; no hover aparece "Ver detalhes".
 */
export function MovieCard({ movie }: { movie: MovieSummary }) {
  const { media } = movie.avaliacao
  const directors = movie.diretores.map((person) => person.nome_pessoa).join(', ')

  return (
    <Link
      to={`/filmes/${movie.sk_movie_id}`}
      className="group flex h-full flex-col rounded-2xl bg-card p-1.5 transition hover:shadow-lg focus-visible:outline-2 focus-visible:outline-petrol"
    >
      <div className="relative overflow-hidden rounded-xl">
        <MoviePoster
          url={movie.url_poster}
          title={movie.titulo}
          className="transition duration-300 group-hover:scale-105"
        />
        {/* Degradê que destaca o título em branco */}
        <div className="absolute inset-x-0 bottom-0 flex items-end gap-1.5 bg-gradient-to-t from-[#5c8a9b]/95 via-[#8fb8c7]/60 to-transparent p-3 pt-16">
          <Clapperboard className="mb-0.5 size-4 shrink-0 text-primary" aria-hidden="true" />
          <h3 className="line-clamp-2 text-base leading-tight font-medium text-primary drop-shadow">
            {movie.titulo}
          </h3>
        </div>
        {/* Hover: "Ver detalhes" */}
        <div className="absolute inset-0 flex items-center justify-center bg-slate/30 opacity-0 transition group-hover:opacity-100 group-focus-visible:opacity-100">
          <span className="inline-flex items-center gap-1.5 rounded-full bg-primary px-4 py-2 text-sm font-medium text-petrol shadow">
            <Eye className="size-4" aria-hidden="true" /> Ver detalhes
          </span>
        </div>
      </div>
      <div className="flex flex-1 flex-col gap-1 px-1.5 pt-2 pb-1 text-xs text-muted">
        <p className="line-clamp-1">
          {[movie.ano_lancamento, directors].filter(Boolean).join(' · ') || 'Sem informações'}
        </p>
        {media !== null ? (
          <span className="flex items-center gap-1.5">
            <StarRating value={toStars(media)} className="size-3.5" />
            <span className="font-medium text-text">{formatStars(toStars(media))}</span>
          </span>
        ) : (
          <span>Sem avaliações</span>
        )}
      </div>
    </Link>
  )
}
