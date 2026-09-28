import { ArrowLeft, CalendarDays, Clock, Pencil, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router'
import { ApiError } from '@/api/client'
import { useDeleteMovie, useMovie } from '@/api/queries'
import { MoviePoster } from '@/components/MoviePoster'
import { ReviewSection } from '@/components/ReviewSection'
import { StarRating } from '@/components/StarRating'
import { Button, ConfirmDialog } from '@/components/ui'
import { formatDate, formatDuration, formatMoney, genreLabel, tmdbImage } from '@/lib/format'
import { formatStars, toStars } from '@/lib/rating'

function Chips({ title, names }: { title: string; names: string[] }) {
  if (!names.length) return null
  return (
    <div className="flex flex-col gap-2">
      <h3 className="text-xs font-semibold tracking-wide text-muted uppercase">{title}</h3>
      <ul className="flex flex-wrap gap-2">
        {names.map((name) => (
          <li key={name} className="rounded-full bg-card px-3 py-1 text-sm text-text">
            {name}
          </li>
        ))}
      </ul>
    </div>
  )
}

export function MovieDetailPage() {
  const { movieId = '' } = useParams()
  const movie = useMovie(movieId)
  const deleteMovie = useDeleteMovie()
  const navigate = useNavigate()
  const [confirmDelete, setConfirmDelete] = useState(false)

  if (movie.isPending) return <p className="text-muted">Carregando filme…</p>
  if (movie.isError) {
    const notFound = movie.error instanceof ApiError && movie.error.status === 404
    return (
      <div className="flex flex-col items-start gap-4">
        <p className="text-danger">{notFound ? 'Filme não encontrado.' : movie.error.message}</p>
        <Link to="/" className="text-petrol hover:underline">
          Voltar ao catálogo
        </Link>
      </div>
    )
  }

  const m = movie.data
  const backdrop = tmdbImage(m.url_backdrop, 'w1280')
  const perf = m.desempenho
  const stats = [
    perf?.nota_tmdb != null && ['Nota TMDB', perf.nota_tmdb.toLocaleString('pt-BR')],
    perf?.nota_imdb != null && ['Nota IMDb', perf.nota_imdb.toLocaleString('pt-BR')],
    perf?.orcamento_usd != null && ['Orçamento', formatMoney(perf.orcamento_usd)],
    perf?.receita_usd != null && ['Bilheteria', formatMoney(perf.receita_usd)],
    // A API só envia o lucro quando orçamento e receita existem.
    perf?.lucro_usd != null && ['Lucro', formatMoney(perf.lucro_usd)],
  ].filter(Boolean) as [string, string][]

  return (
    <div className="flex flex-col gap-10">
      <title>{`${m.titulo} · CineFILO`}</title>
      <Link to="/" className="inline-flex items-center gap-1.5 self-start text-sm text-petrol hover:underline">
        <ArrowLeft className="size-4" /> Voltar ao catálogo
      </Link>

      <section className="relative overflow-hidden rounded-3xl bg-card">
        {backdrop && (
          <img src={backdrop} alt="" className="absolute inset-0 size-full object-cover opacity-25" aria-hidden="true" />
        )}
        <div className="relative grid gap-6 p-6 sm:grid-cols-[13rem_1fr] sm:p-8">
          <div className="overflow-hidden rounded-2xl shadow-lg">
            <MoviePoster url={m.url_poster} title={m.titulo} size="w500" />
          </div>
          <div className="flex flex-col gap-4">
            <div>
              <h1 className="text-3xl font-semibold text-title sm:text-4xl">
                {m.titulo} {m.ano_lancamento && <span className="font-light text-muted">{m.ano_lancamento}</span>}
              </h1>
              {m.diretores.length > 0 && (
                <p className="pt-1 text-text">
                  Dirigido por <strong className="font-medium text-title">{m.diretores.map((d) => d.nome_pessoa).join(', ')}</strong>
                </p>
              )}
            </div>

            <div className="flex flex-wrap items-center gap-2 text-sm text-text">
              {m.status_filme && <span className="rounded-full bg-secondary px-3 py-1 font-medium text-title">{m.status_filme}</span>}
              {m.data_lancamento && (
                <span className="inline-flex items-center gap-1.5 rounded-full bg-primary/80 px-3 py-1">
                  <CalendarDays className="size-4" /> {formatDate(m.data_lancamento)}
                </span>
              )}
              {m.duracao_minutos && (
                <span className="inline-flex items-center gap-1.5 rounded-full bg-primary/80 px-3 py-1">
                  <Clock className="size-4" /> {formatDuration(m.duracao_minutos)}
                </span>
              )}
              {m.generos.map((g) => (
                <span key={g.sk_genre_id} className="rounded-full bg-tertiary px-3 py-1 text-petrol">
                  {genreLabel(g.nome_genero)}
                </span>
              ))}
            </div>

            {/* Média geral das avaliações */}
            <div className="flex flex-col gap-1 self-start rounded-2xl bg-primary/90 px-5 py-3">
              <span className="text-xs font-semibold tracking-wide text-muted uppercase">Média geral</span>
              {m.avaliacao.media !== null ? (
                <span className="flex items-center gap-2">
                  <StarRating value={toStars(m.avaliacao.media)} className="size-6" />
                  <span className="text-2xl font-semibold text-title">{formatStars(toStars(m.avaliacao.media))}</span>
                  <span className="text-sm text-muted">({m.avaliacao.qtd_avaliacoes} avaliação(ões))</span>
                </span>
              ) : (
                <span className="text-muted">Sem avaliações</span>
              )}
            </div>

            <p className="max-w-prose leading-relaxed text-text">{m.sinopse ?? 'Sinopse não informada.'}</p>

            <div className="flex flex-wrap gap-2">
              <Link
                to={`/filmes/${m.sk_movie_id}/editar`}
                className="inline-flex h-10 items-center gap-2 rounded-full bg-tertiary px-5 text-sm font-medium text-petrol hover:bg-tertiary-strong"
              >
                <Pencil className="size-4" /> Editar
              </Link>
              <Button variant="danger" onClick={() => setConfirmDelete(true)}>
                <Trash2 className="size-4" /> Excluir
              </Button>
            </div>
          </div>
        </div>
      </section>

      <ReviewSection movieId={m.sk_movie_id} />

      <section className="flex flex-col gap-4">
        <Chips title="Elenco" names={m.elenco.map((p) => p.nome_pessoa)} />
        <Chips title="Roteiro" names={m.roteiristas.map((p) => p.nome_pessoa)} />
        <Chips title="Produtoras" names={m.produtoras.map((c) => c.nome_produtora)} />
        {stats.length > 0 && (
          <dl className="grid grid-cols-2 gap-3 pt-2 sm:grid-cols-5">
            {stats.map(([label, value]) => (
              <div key={label} className="rounded-2xl bg-card p-3">
                <dt className="text-xs text-muted">{label}</dt>
                <dd className="text-lg font-semibold text-title">{value}</dd>
              </div>
            ))}
          </dl>
        )}
      </section>

      {confirmDelete && (
        <ConfirmDialog
          title="Excluir filme?"
          message={<><strong>{m.titulo}</strong> e todas as suas avaliações serão removidos. Essa ação não pode ser desfeita.</>}
          confirmLabel="Excluir filme"
          loading={deleteMovie.isPending}
          onCancel={() => setConfirmDelete(false)}
          onConfirm={() =>
            deleteMovie.mutate(m.sk_movie_id, { onSuccess: () => navigate('/', { replace: true }) })
          }
        />
      )}
    </div>
  )
}
