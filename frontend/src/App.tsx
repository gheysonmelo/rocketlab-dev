import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createBrowserRouter, RouterProvider } from 'react-router'
import { Layout } from '@/components/Layout'
import { CatalogPage } from '@/pages/CatalogPage'
import { MovieDetailPage } from '@/pages/MovieDetailPage'
import { MovieFormPage } from '@/pages/MovieFormPage'

// Cache de consultas: voltar para uma página já vista não refaz a requisição por 30 s.
const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000, retry: 1, refetchOnWindowFocus: false } },
})

const router = createBrowserRouter([
  {
    element: <Layout />,
    children: [
      { index: true, element: <CatalogPage /> },
      { path: 'filmes/novo', element: <MovieFormPage /> },
      { path: 'filmes/:movieId', element: <MovieDetailPage /> },
      { path: 'filmes/:movieId/editar', element: <MovieFormPage /> },
    ],
  },
])

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  )
}
