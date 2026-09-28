// Contrato da API (espelha backend/app/movies/schemas.py).

export const MOVIE_STATUSES = ['Lançado', 'Pós-Produção', 'Em Produção', 'Planejado'] as const
export type MovieStatus = (typeof MOVIE_STATUSES)[number]

export interface Genre {
  sk_genre_id: string
  nome_genero: string
}

export interface Person {
  sk_person_id: string
  nome_pessoa: string
  tipo_pessoa: string
}

export interface Company {
  sk_company_id: string
  nome_produtora: string
}

/** Média na escala do banco (0 a 10). */
export interface RatingSummary {
  media: number | null
  qtd_avaliacoes: number
}

export interface MovieSummary {
  sk_movie_id: string
  titulo: string
  ano_lancamento: number | null
  url_poster: string | null
  generos: Genre[]
  diretores: Person[]
  avaliacao: RatingSummary
}

export interface Performance {
  orcamento_usd: number | null
  receita_usd: number | null
  lucro_usd: number | null
  popularidade: number | null
  nota_tmdb: number | null
  qtd_tmdb: number | null
  nota_imdb: number | null
  qtd_imdb: number | null
}

export interface MovieDetail extends MovieSummary {
  id_filme: string
  data_lancamento: string | null
  duracao_minutos: number | null
  status_filme: string | null
  sinopse: string | null
  url_backdrop: string | null
  roteiristas: Person[]
  elenco: Person[]
  produtoras: Company[]
  desempenho: Performance | null
}

export interface Page<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface Review {
  sk_movie_review_id: string
  sk_movie_id: string
  nome: string
  /** Escala 0 a 10. */
  nota: number
  comentario: string
  created_at: string
}

export interface MovieWrite {
  titulo: string
  diretores: string[]
  genero_ids: string[]
  data_lancamento: string | null
  ano_lancamento: number | null
  duracao_minutos: number | null
  status_filme: MovieStatus
  sinopse: string | null
  url_poster: string | null
}

export interface ReviewCreate {
  nome: string
  /** Inteiro de 1 a 10: cada meia estrela vale 1 ponto. */
  nota: number
  comentario: string
}
