const DATE_ONLY = /^\d{4}-\d{2}-\d{2}$/

function isDateOnly(str: string): boolean {
  return DATE_ONLY.test(str)
}

export function formatDateLocal(dateStr: string | null): string | null {
  if (!dateStr) return null
  if (isDateOnly(dateStr)) {
    const [y, m, d] = dateStr.split('-').map(Number)
    return new Date(y, m - 1, d).toLocaleDateString('pt-BR')
  }
  return new Date(dateStr).toLocaleDateString('pt-BR')
}

export function dateToLocalISO(dateStr: string): string {
  const [y, m, d] = dateStr.split('-').map(Number)
  return new Date(y, m - 1, d).toISOString()
}

export function formatDateTimeLocal(dateStr: string | null): string {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hours = String(d.getHours()).padStart(2, '0')
  const minutes = String(d.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day}T${hours}:${minutes}`
}

export function localDatetimeToISO(datetimeStr: string): string {
  const d = new Date(datetimeStr)
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString()
}

export function formatDateOnly(dateStr: string | null): string | null {
  if (!dateStr) return null
  const match = dateStr.match(/^(\d{4})-(\d{2})-(\d{2})/)
  if (!match) return dateStr
  return `${match[3]}/${match[2]}/${match[1]}`
}

export function toDateInputValue(dateStr: string | null): string {
  if (!dateStr) return ''
  if (isDateOnly(dateStr)) return dateStr
  return dateStr.slice(0, 10)
}
