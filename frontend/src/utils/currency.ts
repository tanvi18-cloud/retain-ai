export function formatINR(value: number, compact = false): string {
  if (!Number.isFinite(value)) {
    return '₹—'
  }

  if (compact) {
    if (Math.abs(value) >= 10_000_000) {
      const crores = value / 10_000_000
      return `₹${crores.toFixed(2)} crore`
    }
    if (Math.abs(value) >= 100_000) {
      const lakhs = value / 100_000
      return `₹${lakhs.toFixed(2)} lakh`
    }
  }

  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value)
}
