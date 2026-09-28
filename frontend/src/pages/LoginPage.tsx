import { LogIn } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { useNavigate, useSearchParams } from 'react-router'
import { setToken } from '@/api/auth'
import { ApiError, request } from '@/api/client'
import { Button, Field, Input } from '@/components/ui'

export function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [params] = useSearchParams()
  const navigate = useNavigate()

  async function submit(event: FormEvent) {
    event.preventDefault()
    setError('')
    setLoading(true)
    try {
      const { access_token } = await request<{ access_token: string }>('/auth/login', {
        method: 'POST',
        body: { username, password },
      })
      setToken(access_token)
      // Volta para onde a pessoa estava antes de precisar logar.
      const next = params.get('next')
      navigate(next?.startsWith('/') && !next.startsWith('//') ? next : '/', { replace: true })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Não foi possível entrar.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="grid min-h-dvh place-items-center p-4">
      <title>Entrar · CineFILO</title>
      <form
        onSubmit={submit}
        className="flex w-full max-w-sm flex-col gap-5 rounded-3xl bg-primary p-8 shadow-sm"
      >
        <div className="flex flex-col items-center gap-2 pb-2 text-center">
          <span className="text-4xl font-bold tracking-tight text-slate">
            Cine<span className="font-extrabold">FILO</span>
          </span>
          <p className="text-sm text-muted">Área do administrador</p>
        </div>
        <Field label="Usuário">
          <Input
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            autoComplete="username"
            autoFocus
            required
          />
        </Field>
        <Field label="Senha">
          <Input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            autoComplete="current-password"
            required
          />
        </Field>
        {error && (
          <p role="alert" className="text-sm text-danger">
            {error}
          </p>
        )}
        <Button type="submit" disabled={loading || !username || !password}>
          <LogIn className="size-4" aria-hidden="true" />
          {loading ? 'Entrando…' : 'Entrar'}
        </Button>
      </form>
    </main>
  )
}
