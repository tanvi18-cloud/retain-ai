import { describe, expect, it } from 'vitest'

import { formatINR } from '../utils/currency'
import { formatDate, formatDateTime, formatPercentage, formatRelativeTime } from '../utils/date'
import {
  decisionLabel,
  recommendationStatusLabel,
  riskLabelFromScore,
  scoreBandLabel,
} from '../utils/risk'

describe('formatINR', () => {
  it('formats standard amounts', () => {
    expect(formatINR(12500)).toMatch(/12,500/)
  })

  it('formats compact lakh', () => {
    expect(formatINR(125000, true)).toBe('₹1.25 lakh')
  })

  it('formats compact crore', () => {
    expect(formatINR(12_000_000, true)).toBe('₹1.20 crore')
  })
})

describe('date formatting', () => {
  it('formats dates', () => {
    expect(formatDate('2026-07-08')).toContain('2026')
  })

  it('formats date times', () => {
    expect(formatDateTime('2026-07-08T10:00:00Z')).toBeTruthy()
  })

  it('formats relative time', () => {
    const future = new Date(Date.now() + 60_000).toISOString()
    expect(formatRelativeTime(future)).toMatch(/in/i)
  })

  it('formats percentage', () => {
    expect(formatPercentage(42.5)).toBe('42.5%')
  })
})

describe('risk labels', () => {
  it('maps score bands', () => {
    expect(scoreBandLabel('HIGH')).toBe('High')
  })

  it('maps risk labels', () => {
    expect(riskLabelFromScore(80)).toBe('Critical risk')
  })

  it('maps decision labels', () => {
    expect(decisionLabel('RETAIN')).toBe('Retain')
  })

  it('maps recommendation status labels', () => {
    expect(recommendationStatusLabel('APPROVED')).toBe('Approved for discussion')
  })
})
