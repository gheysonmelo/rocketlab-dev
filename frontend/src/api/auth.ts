/** Token JWT do administrador, guardado no navegador entre visitas. */

const KEY = 'cinefilo.token'

export function getToken(): string | null {
  try {
    return localStorage.getItem(KEY)
  } catch {
    return null // modo privado ou armazenamento bloqueado
  }
}

export function setToken(token: string): void {
  try {
    localStorage.setItem(KEY, token)
  } catch {
    /* sem armazenamento: o login vale só nesta aba */
  }
}

export function clearToken(): void {
  try {
    localStorage.removeItem(KEY)
  } catch {
    /* nada a limpar */
  }
}
