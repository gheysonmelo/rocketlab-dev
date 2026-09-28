import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode, TextareaHTMLAttributes } from 'react'

/** Botões em pílula do protótipo FILO. */
const VARIANTS = {
  primary: 'bg-tertiary text-petrol hover:bg-tertiary-strong',
  ghost: 'border border-line text-text hover:bg-card',
  danger: 'bg-danger/10 text-danger hover:bg-danger/20',
}

export function Button({
  variant = 'primary',
  className = '',
  type = 'button',
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: keyof typeof VARIANTS }) {
  return (
    <button
      type={type}
      className={`inline-flex h-10 items-center justify-center gap-2 rounded-full px-5 text-sm font-medium transition disabled:opacity-50 ${VARIANTS[variant]} ${className}`}
      {...props}
    />
  )
}

const controlClasses =
  'w-full rounded-2xl border border-line bg-primary px-4 py-2.5 text-sm text-title placeholder:text-muted focus:border-petrol focus:ring-2 focus:ring-tertiary focus:outline-none aria-[invalid=true]:border-danger'

export function Input(props: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={controlClasses} {...props} />
}

export function Textarea(props: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea className={`${controlClasses} min-h-28 resize-y`} {...props} />
}

/** Rótulo + campo + mensagem de erro. */
export function Field({
  label,
  error,
  required,
  children,
}: {
  label: string
  error?: string
  required?: boolean
  children: ReactNode
}) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="text-sm font-medium text-title">
        {label}
        {required && <span className="text-danger"> *</span>}
      </span>
      {children}
      {error && <span className="text-xs text-danger">{error}</span>}
    </label>
  )
}

/** Janela de confirmação para ações que não podem ser desfeitas. */
export function ConfirmDialog({
  title,
  message,
  confirmLabel,
  loading,
  onConfirm,
  onCancel,
}: {
  title: string
  message: ReactNode
  confirmLabel: string
  loading?: boolean
  onConfirm: () => void
  onCancel: () => void
}) {
  return (
    <div
      className="fixed inset-0 z-50 grid place-items-center bg-slate/40 p-4 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-label={title}
      onKeyDown={(event) => event.key === 'Escape' && onCancel()}
    >
      <div className="w-full max-w-md rounded-3xl bg-primary p-6 shadow-2xl">
        <h2 className="text-xl font-semibold text-title">{title}</h2>
        <div className="mt-2 text-sm text-text">{message}</div>
        <div className="mt-6 flex justify-end gap-2">
          <Button variant="ghost" onClick={onCancel} disabled={loading} autoFocus>
            Cancelar
          </Button>
          <Button variant="danger" onClick={onConfirm} disabled={loading}>
            {loading ? 'Excluindo…' : confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  )
}
