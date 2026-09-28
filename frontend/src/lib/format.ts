const GENRES: Record<string, string> = {
  Action: 'Ação',
  Adventure: 'Aventura',
  Animation: 'Animação',
  Comedy: 'Comédia',
  Crime: 'Crime',
  Documentary: 'Documentário',
  Drama: 'Drama',
  Family: 'Família',
  Fantasy: 'Fantasia',
  History: 'História',
  Horror: 'Terror',
  Music: 'Música',
  Mystery: 'Mistério',
  Romance: 'Romance',
  'Science Fiction': 'Ficção científica',
  Thriller: 'Suspense',
  'Tv Movie': 'Filme para TV',
  War: 'Guerra',
  Western: 'Faroeste',
}

/** Os gêneros vêm em inglês nos dados; a interface mostra em português. */
export const genreLabel = (name: string) => GENRES[name] ?? name

/** As URLs apontam para o CDN do TMDB; pedir o tamanho certo economiza banda. */
export const tmdbImage = (url: string | null, size: 'w342' | 'w500' | 'w1280') =>
  url ? url.replace(/\/t\/p\/(w\d+|original)\//, `/t/p/${size}/`) : null

/** "2023-07-19" -> "19 de julho de 2023" (data sem hora: sem conversão de fuso). */
export const formatDate = (iso: string) =>
  new Date(`${iso}T00:00:00Z`).toLocaleDateString('pt-BR', { dateStyle: 'long', timeZone: 'UTC' })

export const formatDateTime = (iso: string) =>
  new Date(iso).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })

/** 181 -> "3h 1min". */
export function formatDuration(minutes: number): string {
  const hours = Math.floor(minutes / 60)
  const rest = minutes % 60
  if (!hours) return `${rest}min`
  return rest ? `${hours}h ${rest}min` : `${hours}h`
}

export const formatMoney = (value: number) =>
  `US$ ${value.toLocaleString('pt-BR', { notation: 'compact', maximumFractionDigits: 1 })}`
