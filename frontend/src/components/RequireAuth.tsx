import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router'
import { getToken } from '@/api/auth'

/** Só deixa passar quem está logado; os demais vão para /login e voltam depois. */
export function RequireAuth({ children }: { children: ReactNode }) {
  const location = useLocation()
  if (!getToken()) {
    const next = encodeURIComponent(location.pathname + location.search)
    return <Navigate to={`/login?next=${next}`} replace />
  }
  return children
}
