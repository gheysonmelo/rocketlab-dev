import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { request } from './client'
import type { Genre, MovieDetail, MovieSummary, MovieWrite, Page, Review, ReviewCreate } from './types'

export const DEFAULT_PAGE_SIZE = 24

export function useCatalog(q: string, page: number, pageSize: number) {
  return useQuery({
    queryKey: ['movies', 'list', { q, page, pageSize }],
    queryFn: () =>
      request<Page<MovieSummary>>('/movies', {
        query: { q: q || undefined, page, page_size: pageSize },
      }),
    // Mantém a página atual na tela enquanto a próxima carrega.
    placeholderData: keepPreviousData,
  })
}

export function useMovie(movieId: string) {
  return useQuery({
    queryKey: ['movies', 'detail', movieId],
    queryFn: () => request<MovieDetail>(`/movies/${movieId}`),
    enabled: Boolean(movieId), // no cadastro não há filme para buscar
  })
}

export function useReviews(movieId: string, page: number) {
  return useQuery({
    queryKey: ['movies', 'reviews', movieId, page],
    queryFn: () =>
      request<Page<Review>>(`/movies/${movieId}/reviews`, { query: { page, page_size: 10 } }),
    placeholderData: keepPreviousData,
  })
}

/** Qualquer escrita pode mudar catálogo, ficha e avaliações: invalida o cache de filmes. */
function useInvalidateMovies() {
  const queryClient = useQueryClient()
  return () => queryClient.invalidateQueries({ queryKey: ['movies'] })
}

export function useCreateReview(movieId: string) {
  const invalidate = useInvalidateMovies()
  return useMutation({
    mutationFn: (data: ReviewCreate) =>
      request<Review>(`/movies/${movieId}/reviews`, { method: 'POST', body: data }),
    onSuccess: invalidate,
  })
}

export function useDeleteReview(movieId: string) {
  const invalidate = useInvalidateMovies()
  return useMutation({
    mutationFn: (reviewId: string) =>
      request<void>(`/movies/${movieId}/reviews/${reviewId}`, { method: 'DELETE' }),
    onSuccess: invalidate,
  })
}

/** Cadastra (sem movieId) ou atualiza (com movieId) um filme. */
export function useSaveMovie(movieId?: string) {
  const invalidate = useInvalidateMovies()
  return useMutation({
    mutationFn: (data: MovieWrite) =>
      movieId
        ? request<MovieDetail>(`/movies/${movieId}`, { method: 'PUT', body: data })
        : request<MovieDetail>('/movies', { method: 'POST', body: data }),
    onSuccess: invalidate,
  })
}

export function useDeleteMovie() {
  const invalidate = useInvalidateMovies()
  return useMutation({
    mutationFn: (movieId: string) => request<void>(`/movies/${movieId}`, { method: 'DELETE' }),
    onSuccess: invalidate,
  })
}

export function useGenres() {
  return useQuery({
    queryKey: ['genres'],
    queryFn: () => request<Genre[]>('/genres'),
    staleTime: Infinity, // os 19 gêneros não mudam
  })
}
