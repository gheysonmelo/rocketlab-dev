import { Clapperboard } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router'
import { ApiError } from '@/api/client'
import { useGenres, useMovie, useSaveMovie } from '@/api/queries'
import { MOVIE_STATUSES, type MovieDetail, type MovieStatus, type MovieWrite } from '@/api/types'
import { MoviePoster } from '@/components/MoviePoster'
import { Select } from '@/components/Select'
import { Button, Field, Input, Textarea } from '@/components/ui'
import { genreLabel } from '@/lib/format'

interface FormState {
  titulo: string
  diretores: string
  genero_ids: string[]
  ano_lancamento: string
  data_lancamento: string
  duracao_minutos: string
  status_filme: MovieStatus
  sinopse: string
  url_poster: string
}

function toForm(movie?: MovieDetail): FormState {
  return {
    titulo: movie?.titulo ?? '',
    diretores: movie?.diretores.map((d) => d.nome_pessoa).join(', ') ?? '',
    genero_ids: movie?.generos.map((g) => g.sk_genre_id) ?? [],
    ano_lancamento: movie?.ano_lancamento ? String(movie.ano_lancamento) : '',
    data_lancamento: movie?.data_lancamento ?? '',
    duracao_minutos: movie?.duracao_minutos ? String(movie.duracao_minutos) : '',
    status_filme: (movie?.status_filme as MovieStatus) ?? 'Lançado',
    sinopse: movie?.sinopse ?? '',
    url_poster: movie?.url_poster ?? '',
  }
}

function toPayload(form: FormState): MovieWrite {
  return {
    titulo: form.titulo.trim(),
    // Diretores separados por vírgula; a API reaproveita os que já existem.
    diretores: form.diretores.split(',').map((name) => name.trim()).filter(Boolean),
    genero_ids: form.genero_ids,
    ano_lancamento: form.ano_lancamento ? Number(form.ano_lancamento) : null,
    data_lancamento: form.data_lancamento || null,
    duracao_minutos: form.duracao_minutos ? Number(form.duracao_minutos) : null,
    status_filme: form.status_filme,
    sinopse: form.sinopse.trim() || null,
    url_poster: form.url_poster.trim() || null,
  }
}

function validate(form: FormState): Record<string, string> {
  const errors: Record<string, string> = {}
  if (!form.titulo.trim()) errors.titulo = 'Informe o título.'
  if (!/^\d{4}$/.test(form.ano_lancamento)) errors.ano_lancamento = 'Informe o ano com 4 dígitos.'
  else if (form.data_lancamento && form.data_lancamento.slice(0, 4) !== form.ano_lancamento)
    errors.ano_lancamento = 'Deve ser o mesmo ano da data de lançamento.'
  if (form.duracao_minutos && !(Number(form.duracao_minutos) > 0))
    errors.duracao_minutos = 'Informe a duração em minutos.'
  return errors
}

function MovieForm({ movie }: { movie?: MovieDetail }) {
  const [form, setForm] = useState(() => toForm(movie))
  const [errors, setErrors] = useState<Record<string, string>>({})
  const genres = useGenres()
  const save = useSaveMovie(movie?.sk_movie_id)
  const navigate = useNavigate()

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) =>
    setForm((current) => ({ ...current, [key]: value }))

  function submit(event: FormEvent) {
    event.preventDefault()
    const found = validate(form)
    setErrors(found)
    if (Object.keys(found).length) return
    save.mutate(toPayload(form), {
      onSuccess: (saved) => navigate(`/filmes/${saved.sk_movie_id}`),
      // Erros de validação da API (422) aparecem no campo correspondente.
      onError: (error) =>
        setErrors(error instanceof ApiError ? { ...error.fieldErrors, form: error.message } : {}),
    })
  }

  return (
    <form onSubmit={submit} noValidate className="grid gap-8 lg:grid-cols-[1fr_14rem]">
      <div className="flex flex-col gap-5">
        <Field label="Título" required error={errors.titulo}>
          <Input value={form.titulo} onChange={(e) => set('titulo', e.target.value)} maxLength={500} aria-invalid={!!errors.titulo} />
        </Field>
        <Field label="Direção (separe vários nomes com vírgula)" error={errors.diretores}>
          <Input value={form.diretores} onChange={(e) => set('diretores', e.target.value)} placeholder="Ex.: Christopher Nolan" />
        </Field>
        <div className="grid gap-5 sm:grid-cols-3">
          <Field label="Ano de lançamento" required error={errors.ano_lancamento}>
            <Input
              value={form.ano_lancamento}
              onChange={(e) => set('ano_lancamento', e.target.value.replace(/\D/g, '').slice(0, 4))}
              inputMode="numeric"
              placeholder="2024"
              aria-invalid={!!errors.ano_lancamento}
            />
          </Field>
          <Field label="Data de lançamento" error={errors.data_lancamento}>
            <Input
              type="date"
              value={form.data_lancamento}
              onChange={(e) => {
                const date = e.target.value
                // Ao escolher a data, o ano é preenchido automaticamente.
                setForm((c) => ({ ...c, data_lancamento: date, ano_lancamento: date ? date.slice(0, 4) : c.ano_lancamento }))
              }}
            />
          </Field>
          <Field label="Duração (min)" error={errors.duracao_minutos}>
            <Input
              value={form.duracao_minutos}
              onChange={(e) => set('duracao_minutos', e.target.value.replace(/\D/g, ''))}
              inputMode="numeric"
              placeholder="120"
              aria-invalid={!!errors.duracao_minutos}
            />
          </Field>
        </div>
        <div className="flex flex-col gap-1.5">
          <span className="text-sm font-medium text-title">Status</span>
          <Select
            label="Status do filme"
            value={form.status_filme}
            options={MOVIE_STATUSES.map((status) => ({ value: status, label: status }))}
            onChange={(status) => set('status_filme', status)}
            className="sm:w-64"
            placement="bottom"
          />
        </div>
        <div className="flex flex-col gap-2">
          <span className="text-sm font-medium text-title">Gêneros</span>
          <div className="flex flex-wrap gap-2">
            {genres.data?.map((genre) => {
              const selected = form.genero_ids.includes(genre.sk_genre_id)
              return (
                <button
                  key={genre.sk_genre_id}
                  type="button"
                  aria-pressed={selected}
                  onClick={() =>
                    set('genero_ids', selected ? form.genero_ids.filter((id) => id !== genre.sk_genre_id) : [...form.genero_ids, genre.sk_genre_id])
                  }
                  className={`rounded-full border px-3 py-1 text-sm transition ${
                    selected ? 'border-transparent bg-secondary font-medium text-title' : 'border-line text-text hover:bg-card'
                  }`}
                >
                  {genreLabel(genre.nome_genero)}
                </button>
              )
            })}
          </div>
        </div>
        <Field label="Sinopse" error={errors.sinopse}>
          <Textarea value={form.sinopse} onChange={(e) => set('sinopse', e.target.value)} maxLength={4000} rows={5} />
        </Field>
        <Field label="URL do pôster" error={errors.url_poster}>
          <Input type="url" value={form.url_poster} onChange={(e) => set('url_poster', e.target.value)} placeholder="https://image.tmdb.org/t/p/w500/…" aria-invalid={!!errors.url_poster} />
        </Field>
        {errors.form && <p className="text-sm text-danger">{errors.form}</p>}
        <div className="flex justify-end gap-2 border-t border-line pt-5">
          <Link to={movie ? `/filmes/${movie.sk_movie_id}` : '/'} className="inline-flex h-10 items-center rounded-full border border-line px-5 text-sm text-text hover:bg-card">
            Cancelar
          </Link>
          <Button type="submit" disabled={save.isPending}>
            {save.isPending ? 'Salvando…' : movie ? 'Salvar alterações' : 'Cadastrar filme'}
          </Button>
        </div>
      </div>
      <aside className="order-first flex flex-col gap-2 lg:order-none">
        <span className="text-sm font-medium text-title">Prévia do pôster</span>
        <div className="w-40 overflow-hidden rounded-2xl lg:w-full">
          <MoviePoster key={form.url_poster} url={form.url_poster || null} title={form.titulo || 'Sem título'} size="w500" />
        </div>
      </aside>
    </form>
  )
}

/** Cadastro (/filmes/novo) e edição (/filmes/:id/editar) usam o mesmo formulário. */
export function MovieFormPage() {
  const { movieId } = useParams()
  const movie = useMovie(movieId ?? '')
  const editing = Boolean(movieId)

  return (
    <div className="flex flex-col gap-6">
      <h1 className="flex items-center gap-2 text-3xl font-semibold text-title">
        <Clapperboard className="size-8" strokeWidth={1.75} aria-hidden="true" />
        {editing ? 'Editar filme' : 'Novo filme'}
      </h1>
      {!editing && <MovieForm />}
      {editing && movie.isPending && <p className="text-muted">Carregando filme…</p>}
      {editing && movie.isError && <p className="text-danger">{movie.error.message}</p>}
      {editing && movie.data && <MovieForm movie={movie.data} />}
    </div>
  )
}
