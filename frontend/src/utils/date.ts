const DATE_ONLY_RE = /^\d{4}-\d{2}-\d{2}$/

export const toDateOnlyString = (date: Date): string => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

export const parseDateOnlyString = (value: string): Date => {
  const [yearStr, monthStr, dayStr] = value.split('-')
  const year = Number(yearStr)
  const monthIndex = Number(monthStr) - 1
  const day = Number(dayStr)
  return new Date(year, monthIndex, day)
}

export const parseDateString = (value: string): Date => {
  if (DATE_ONLY_RE.test(value)) return parseDateOnlyString(value)
  return new Date(value)
}

