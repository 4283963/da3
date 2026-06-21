export function formatNum(n, digits = 2) {
  if (n === null || n === undefined || n === '') return '-'
  const num = Number(n)
  if (Number.isNaN(num)) return String(n)
  return num.toLocaleString('zh-CN', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })
}

export function statusText(s) {
  return (
    {
      active: '生效中',
      pending_deduction: '待扣款',
      deducted: '已扣款',
      overdue: '逾期',
    }[s] || s
  )
}

export function statusClass(s) {
  return (
    {
      active: 'tag-active',
      pending_deduction: 'tag-pending',
      deducted: 'tag-done',
      overdue: 'tag-overdue',
    }[s] || ''
  )
}

export function gainClass(n) {
  const num = Number(n)
  if (num > 0) return 'gain'
  if (num < 0) return 'loss'
  return ''
}
