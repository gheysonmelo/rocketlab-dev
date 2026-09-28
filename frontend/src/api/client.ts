/** Erro HTTP da API. `fieldErrors` traz as mensagens de validação (422) por campo. */
export class ApiError extends Error {
  readonly status: number
  readonly fieldErrors: Record<string, string>

  constructor(status: number, message: string, fieldErrors: Record<string, string> = {}) {
    super(message)
    this.status = status
    this.fieldErrors = fieldErrors
  }
}

interface ValidationIssue {
  loc: (string | number)[]
  msg: string
}

async function toApiError(response: Response): Promise<ApiError> {
  const body = await response.json().catch(() => null)
  const detail: unknown = body?.detail
  if (typeof detail === 'string') return new ApiError(response.status, detail)
  if (Array.isArray(detail)) {
    // Formato do FastAPI: [{ loc: ["body", "titulo"], msg: "..." }]
    const fieldErrors: Record<string, string> = {}
    for (const issue of detail as ValidationIssue[]) {
      const field = issue.loc.filter((part) => part !== 'body').join('.')
      fieldErrors[field || 'form'] = issue.msg
    }
    return new ApiError(response.status, 'Revise os campos destacados.', fieldErrors)
  }
  return new ApiError(response.status, `Erro ${response.status} ao falar com a API.`)
}

type Query = Record<string, string | number | undefined>

export async function request<T>(
  path: string,
  options: { method?: string; body?: unknown; query?: Query } = {},
): Promise<T> {
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(options.query ?? {})) {
    if (value !== undefined && value !== '') params.set(key, String(value))
  }
  const search = params.toString()
  const url = `/api/v1${path}${search ? `?${search}` : ''}`

  let response: Response
  try {
    response = await fetch(url, {
      method: options.method ?? 'GET',
      headers: options.body === undefined ? undefined : { 'Content-Type': 'application/json' },
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
    })
  } catch {
    throw new ApiError(0, 'Não foi possível conectar à API. O backend está rodando?')
  }
  if (!response.ok) throw await toApiError(response)
  return (response.status === 204 ? undefined : await response.json()) as T
}
