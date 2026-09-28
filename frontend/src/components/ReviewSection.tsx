import { MessageSquareText, Trash2 } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { ApiError } from '@/api/client'
import { useCreateReview, useDeleteReview, useReviews } from '@/api/queries'
import type { Review } from '@/api/types'
import { formatDateTime } from '@/lib/format'
import { formatStars, starsToScore, toStars } from '@/lib/rating'
import { StarRating } from './StarRating'
import { StarRatingInput } from './StarRatingInput'
import { Button, ConfirmDialog, Field, Input, Textarea } from './ui'

function ReviewForm({ movieId }: { movieId: string }) {
  const createReview = useCreateReview(movieId)
  const [stars, setStars] = useState(0)
  const [nome, setNome] = useState('')
  const [comentario, setComentario] = useState('')
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [success, setSuccess] = useState(false)

  function submit(event: FormEvent) {
    event.preventDefault()
    const found: Record<string, string> = {}
    if (!stars) found.nota = 'Escolha uma nota de 0,5 a 5 estrelas.'
    if (!nome.trim()) found.nome = 'Informe quem está avaliando.'
    if (!comentario.trim()) found.comentario = 'Escreva a resenha.'
    setErrors(found)
    setSuccess(false)
    if (Object.keys(found).length) return

    // A API usa a escala 0–10: cada meia estrela vale 1 ponto (4,5 estrelas = 9).
    createReview.mutate(
      { nome: nome.trim(), comentario: comentario.trim(), nota: starsToScore(stars) },
      {
        onSuccess: () => {
          setStars(0)
          setNome('')
          setComentario('')
          setSuccess(true)
        },
        onError: (error) =>
          setErrors(error instanceof ApiError ? { ...error.fieldErrors, form: error.message } : {}),
      },
    )
  }

  return (
    <form onSubmit={submit} noValidate className="flex flex-col gap-4 rounded-3xl bg-card p-5">
      <h3 className="text-lg font-semibold text-title">Adicionar avaliação</h3>
      <div className="flex flex-col gap-1.5">
        <span className="text-sm font-medium text-title">
          Nota <span className="text-danger">*</span>
        </span>
        <StarRatingInput value={stars} onChange={setStars} />
        {errors.nota && <span className="text-xs text-danger">{errors.nota}</span>}
      </div>
      <Field label="Seu nome" required error={errors.nome}>
        <Input value={nome} onChange={(e) => setNome(e.target.value)} maxLength={120} aria-invalid={!!errors.nome} />
      </Field>
      <Field label="Resenha" required error={errors.comentario}>
        <Textarea
          value={comentario}
          onChange={(e) => setComentario(e.target.value)}
          maxLength={4000}
          placeholder="O que você achou do filme?"
          aria-invalid={!!errors.comentario}
        />
      </Field>
      {errors.form && <p className="text-sm text-danger">{errors.form}</p>}
      {success && <p className="text-sm text-petrol">Avaliação publicada! A média foi atualizada.</p>}
      <Button type="submit" disabled={createReview.isPending} className="self-end">
        {createReview.isPending ? 'Publicando…' : 'Publicar avaliação'}
      </Button>
    </form>
  )
}

function ReviewItem({ review, onDelete }: { review: Review; onDelete: () => void }) {
  const stars = toStars(review.nota)
  return (
    <article className="flex flex-col gap-1.5 border-b border-line py-4 last:border-b-0">
      <header className="flex flex-wrap items-center gap-x-3 gap-y-1">
        <span className="grid size-9 place-items-center rounded-full bg-tertiary text-sm font-semibold text-petrol">
          {review.nome.trim()[0]?.toUpperCase()}
        </span>
        <h4 className="font-medium text-title">{review.nome}</h4>
        <span className="flex items-center gap-1.5">
          <StarRating value={stars} className="size-3.5" />
          <span className="text-xs font-medium">{formatStars(stars)}</span>
        </span>
        <time dateTime={review.created_at} className="text-xs text-muted">
          {formatDateTime(review.created_at)}
        </time>
        <button
          type="button"
          onClick={onDelete}
          aria-label={`Excluir avaliação de ${review.nome}`}
          className="ml-auto rounded-full p-1.5 text-muted hover:bg-danger/10 hover:text-danger"
        >
          <Trash2 className="size-4" />
        </button>
      </header>
      <p className="pl-12 leading-relaxed whitespace-pre-line text-text">{review.comentario}</p>
    </article>
  )
}

/** Histórico de avaliações (mais recentes primeiro) e formulário de nova avaliação. */
export function ReviewSection({ movieId }: { movieId: string }) {
  const [page, setPage] = useState(1)
  const [toDelete, setToDelete] = useState<Review | null>(null)
  const reviews = useReviews(movieId, page)
  const deleteReview = useDeleteReview(movieId)
  const data = reviews.data

  return (
    <section className="grid gap-6 lg:grid-cols-[1fr_22rem] lg:items-start">
      <div>
        <h2 className="flex items-center gap-2 text-2xl font-semibold text-title">
          <MessageSquareText className="size-6" strokeWidth={1.75} aria-hidden="true" />
          Avaliações {data && <span className="text-base font-normal text-muted">({data.total})</span>}
        </h2>
        {reviews.isPending && <p className="pt-4 text-muted">Carregando avaliações…</p>}
        {data?.items.length === 0 && (
          <p className="pt-4 text-muted">Nenhuma avaliação ainda. Seja o primeiro a avaliar!</p>
        )}
        {data?.items.map((review) => (
          <ReviewItem key={review.sk_movie_review_id} review={review} onDelete={() => setToDelete(review)} />
        ))}
        {data && data.pages > 1 && (
          <div className="flex items-center gap-3 pt-4 text-sm text-muted">
            <Button variant="ghost" onClick={() => setPage(page - 1)} disabled={page <= 1}>
              Anteriores
            </Button>
            Página {data.page} de {data.pages}
            <Button variant="ghost" onClick={() => setPage(page + 1)} disabled={page >= data.pages}>
              Próximas
            </Button>
          </div>
        )}
      </div>
      <ReviewForm movieId={movieId} />

      {toDelete && (
        <ConfirmDialog
          title="Excluir avaliação?"
          message={
            <>
              A avaliação de <strong>{toDelete.nome}</strong> será removida e a média do filme,
              recalculada.
            </>
          }
          confirmLabel="Excluir avaliação"
          loading={deleteReview.isPending}
          onCancel={() => setToDelete(null)}
          onConfirm={() =>
            deleteReview.mutate(toDelete.sk_movie_review_id, {
              onSettled: () => setToDelete(null),
            })
          }
        />
      )}
    </section>
  )
}
