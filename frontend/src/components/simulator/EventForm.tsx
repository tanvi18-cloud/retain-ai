import { useCallback, useMemo, useState, type FormEvent } from 'react'

import type {
  EventPayload,
  EventSeverity,
  EventType,
  IncomingEventCreate,
} from '../../types/event'
import { Button } from '../ui/Button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/Card'

const INPUT_CLASS =
  'mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400'
const INPUT_ERROR_CLASS = 'border-red-400 focus-visible:ring-red-400'

const EVENT_TYPE_OPTIONS: { value: EventType; label: string }[] = [
  { value: 'EXTERNAL_HOME_LOAN_INQUIRY', label: 'External home-loan inquiry' },
  { value: 'EXTERNAL_CARD_INQUIRY', label: 'External card inquiry' },
  { value: 'SALARY_CREDIT_STOPPED', label: 'Salary credit stopped' },
  { value: 'SALARY_CREDIT_RESUMED', label: 'Salary credit resumed' },
  { value: 'LARGE_EXTERNAL_TRANSFER', label: 'Large external transfer' },
  { value: 'FIXED_DEPOSIT_MATURITY', label: 'Fixed deposit maturity' },
  { value: 'FOREX_SPEND_INCREASE', label: 'Forex spend increase' },
  { value: 'DPD_CHANGED', label: 'DPD changed' },
  { value: 'PRODUCT_USAGE_DECLINE', label: 'Product usage decline' },
  { value: 'BALANCE_DECLINE', label: 'Balance decline' },
  { value: 'INVESTMENT_TRANSFER_INCREASE', label: 'Investment transfer increase' },
  { value: 'MANUAL_REANALYSIS', label: 'Manual reanalysis' },
]

const SEVERITY_OPTIONS: EventSeverity[] = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']

const DEFAULT_SOURCE_SYSTEM: Record<EventType, string> = {
  EXTERNAL_HOME_LOAN_INQUIRY: 'CREDIT_BUREAU',
  EXTERNAL_CARD_INQUIRY: 'CREDIT_BUREAU',
  SALARY_CREDIT_STOPPED: 'TRANSACTION_ENGINE',
  SALARY_CREDIT_RESUMED: 'TRANSACTION_ENGINE',
  LARGE_EXTERNAL_TRANSFER: 'TRANSACTION_ENGINE',
  FIXED_DEPOSIT_MATURITY: 'CORE_BANKING',
  FOREX_SPEND_INCREASE: 'TRANSACTION_ENGINE',
  DPD_CHANGED: 'CREDIT_BUREAU',
  PRODUCT_USAGE_DECLINE: 'TRANSACTION_ENGINE',
  BALANCE_DECLINE: 'TRANSACTION_ENGINE',
  INVESTMENT_TRANSFER_INCREASE: 'TRANSACTION_ENGINE',
  MANUAL_REANALYSIS: 'CRM',
}

type FormState = Record<string, string | boolean>

function emptyString(value: string): string | undefined {
  const trimmed = value.trim()
  return trimmed.length > 0 ? trimmed : undefined
}

function parseOptionalNumber(value: string): number | undefined {
  if (value.trim() === '') return undefined
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : undefined
}

function parseRequiredNumber(value: string): number | null {
  if (value.trim() === '') return null
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

function buildDefaultFormState(eventType: EventType): FormState {
  switch (eventType) {
    case 'EXTERNAL_HOME_LOAN_INQUIRY':
      return { severity: 'HIGH', amount_band: '', institution_category: '' }
    case 'EXTERNAL_CARD_INQUIRY':
      return { severity: 'MEDIUM', card_type: '' }
    case 'SALARY_CREDIT_STOPPED':
      return { previous_monthly_salary: '' }
    case 'SALARY_CREDIT_RESUMED':
      return {}
    case 'LARGE_EXTERNAL_TRANSFER':
      return { amount: '', destination_category: '' }
    case 'FIXED_DEPOSIT_MATURITY':
      return {
        maturity_date: '',
        maturity_amount: '',
        external_outflow_detected: false,
      }
    case 'FOREX_SPEND_INCREASE':
      return {
        forex_spend_30d: '',
        percentage_increase: '',
        travel_trigger_detected: false,
      }
    case 'DPD_CHANGED':
      return { previous_dpd: '', new_dpd: '60' }
    case 'PRODUCT_USAGE_DECLINE':
      return { product_inactivity_days: '30', card_spend_change_pct_30d: '' }
    case 'BALANCE_DECLINE':
      return { balance_change_pct_30d: '-15' }
    case 'INVESTMENT_TRANSFER_INCREASE':
      return {
        external_transfer_amount_30d: '',
        destination_category: 'INVESTMENT_PLATFORM',
        percentage_increase: '',
      }
    case 'MANUAL_REANALYSIS':
      return { reason: '' }
    default:
      return {}
  }
}

function buildPayload(eventType: EventType, form: FormState): EventPayload | null {
  switch (eventType) {
    case 'EXTERNAL_HOME_LOAN_INQUIRY':
      return {
        severity: form.severity as EventSeverity,
        amount_band: emptyString(String(form.amount_band ?? '')),
        institution_category: emptyString(String(form.institution_category ?? '')),
      }
    case 'EXTERNAL_CARD_INQUIRY':
      return {
        severity: form.severity as EventSeverity,
        card_type: emptyString(String(form.card_type ?? '')),
      }
    case 'SALARY_CREDIT_STOPPED':
      return {
        previous_monthly_salary: parseOptionalNumber(String(form.previous_monthly_salary ?? '')),
      }
    case 'SALARY_CREDIT_RESUMED':
      return {}
    case 'LARGE_EXTERNAL_TRANSFER': {
      const amount = parseRequiredNumber(String(form.amount ?? ''))
      if (amount === null || amount < 0) return null
      return {
        amount,
        destination_category: emptyString(String(form.destination_category ?? '')),
      }
    }
    case 'FIXED_DEPOSIT_MATURITY': {
      const maturityDate = emptyString(String(form.maturity_date ?? ''))
      if (!maturityDate) return null
      return {
        maturity_date: maturityDate,
        maturity_amount: parseOptionalNumber(String(form.maturity_amount ?? '')),
        external_outflow_detected: Boolean(form.external_outflow_detected),
      }
    }
    case 'FOREX_SPEND_INCREASE': {
      const forexSpend = parseRequiredNumber(String(form.forex_spend_30d ?? ''))
      if (forexSpend === null || forexSpend < 0) return null
      return {
        forex_spend_30d: forexSpend,
        percentage_increase: parseOptionalNumber(String(form.percentage_increase ?? '')),
        travel_trigger_detected: Boolean(form.travel_trigger_detected),
      }
    }
    case 'DPD_CHANGED': {
      const newDpd = parseRequiredNumber(String(form.new_dpd ?? ''))
      if (newDpd === null || newDpd < 0) return null
      return {
        previous_dpd: parseOptionalNumber(String(form.previous_dpd ?? '')),
        new_dpd: newDpd,
      }
    }
    case 'PRODUCT_USAGE_DECLINE': {
      const inactivityDays = parseRequiredNumber(String(form.product_inactivity_days ?? ''))
      if (inactivityDays === null || inactivityDays < 0) return null
      return {
        product_inactivity_days: inactivityDays,
        card_spend_change_pct_30d: parseOptionalNumber(
          String(form.card_spend_change_pct_30d ?? ''),
        ),
      }
    }
    case 'BALANCE_DECLINE': {
      const balanceChange = parseRequiredNumber(String(form.balance_change_pct_30d ?? ''))
      if (balanceChange === null) return null
      return { balance_change_pct_30d: balanceChange }
    }
    case 'INVESTMENT_TRANSFER_INCREASE': {
      const transferAmount = parseRequiredNumber(
        String(form.external_transfer_amount_30d ?? ''),
      )
      const destination = emptyString(String(form.destination_category ?? ''))
      if (transferAmount === null || transferAmount < 0 || !destination) return null
      return {
        external_transfer_amount_30d: transferAmount,
        destination_category: destination,
        percentage_increase: parseOptionalNumber(String(form.percentage_increase ?? '')),
      }
    }
    case 'MANUAL_REANALYSIS':
      return { reason: emptyString(String(form.reason ?? '')) }
    default:
      return {}
  }
}

function validateForm(eventType: EventType, form: FormState): Record<string, string> {
  const errors: Record<string, string> = {}

  switch (eventType) {
    case 'LARGE_EXTERNAL_TRANSFER': {
      const amount = parseRequiredNumber(String(form.amount ?? ''))
      if (amount === null) errors.amount = 'Amount is required.'
      else if (amount < 0) errors.amount = 'Amount must be zero or positive.'
      break
    }
    case 'FIXED_DEPOSIT_MATURITY':
      if (!emptyString(String(form.maturity_date ?? ''))) {
        errors.maturity_date = 'Maturity date is required.'
      }
      break
    case 'FOREX_SPEND_INCREASE': {
      const forex = parseRequiredNumber(String(form.forex_spend_30d ?? ''))
      if (forex === null) errors.forex_spend_30d = 'Forex spend is required.'
      else if (forex < 0) errors.forex_spend_30d = 'Forex spend must be zero or positive.'
      break
    }
    case 'DPD_CHANGED': {
      const newDpd = parseRequiredNumber(String(form.new_dpd ?? ''))
      if (newDpd === null) errors.new_dpd = 'New DPD is required.'
      else if (newDpd < 0) errors.new_dpd = 'DPD must be zero or positive.'
      break
    }
    case 'PRODUCT_USAGE_DECLINE': {
      const days = parseRequiredNumber(String(form.product_inactivity_days ?? ''))
      if (days === null) errors.product_inactivity_days = 'Inactivity days are required.'
      else if (days < 0) errors.product_inactivity_days = 'Inactivity days must be zero or positive.'
      break
    }
    case 'BALANCE_DECLINE': {
      const pct = parseRequiredNumber(String(form.balance_change_pct_30d ?? ''))
      if (pct === null) errors.balance_change_pct_30d = 'Balance change percentage is required.'
      break
    }
    case 'INVESTMENT_TRANSFER_INCREASE': {
      const amount = parseRequiredNumber(String(form.external_transfer_amount_30d ?? ''))
      if (amount === null) errors.external_transfer_amount_30d = 'Transfer amount is required.'
      else if (amount < 0) {
        errors.external_transfer_amount_30d = 'Transfer amount must be zero or positive.'
      }
      if (!emptyString(String(form.destination_category ?? ''))) {
        errors.destination_category = 'Destination category is required.'
      }
      break
    }
    default:
      break
  }

  return errors
}

function createIdempotencyKey(): string {
  return `sim-${Date.now()}-${crypto.randomUUID()}`
}

export interface EventFormProps {
  customerId: string
  onSubmit: (event: IncomingEventCreate) => void | Promise<void>
  loading?: boolean
  fieldErrors?: Record<string, string>
}

function FieldError({ id, message }: { id: string; message?: string }) {
  if (!message) return null
  return (
    <p id={id} className="mt-1 text-xs text-red-600" role="alert">
      {message}
    </p>
  )
}

export function EventForm({
  customerId,
  onSubmit,
  loading = false,
  fieldErrors = {},
}: EventFormProps) {
  const [eventType, setEventType] = useState<EventType>('EXTERNAL_HOME_LOAN_INQUIRY')
  const [formState, setFormState] = useState<FormState>(() =>
    buildDefaultFormState('EXTERNAL_HOME_LOAN_INQUIRY'),
  )
  const [notificationsEnabled, setNotificationsEnabled] = useState(true)
  const [clientErrors, setClientErrors] = useState<Record<string, string>>({})

  const mergedErrors = useMemo(
    () => ({ ...clientErrors, ...fieldErrors }),
    [clientErrors, fieldErrors],
  )

  const handleEventTypeChange = useCallback((nextType: EventType) => {
    setEventType(nextType)
    setFormState(buildDefaultFormState(nextType))
    setClientErrors({})
  }, [])

  const updateField = useCallback((key: string, value: string | boolean) => {
    setFormState((prev) => ({ ...prev, [key]: value }))
    setClientErrors((prev) => {
      if (!(key in prev)) return prev
      const next = { ...prev }
      delete next[key]
      return next
    })
  }, [])

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const validationErrors = validateForm(eventType, formState)
    if (Object.keys(validationErrors).length > 0) {
      setClientErrors(validationErrors)
      return
    }

    const payload = buildPayload(eventType, formState)
    if (!payload) {
      setClientErrors({ form: 'Please correct the highlighted fields.' })
      return
    }

    setClientErrors({})
    await onSubmit({
      customer_id: customerId,
      event_type: eventType,
      source_system: DEFAULT_SOURCE_SYSTEM[eventType],
      payload,
      notifications_enabled: notificationsEnabled,
      idempotency_key: createIdempotencyKey(),
    })
  }

  const renderFields = () => {
    switch (eventType) {
      case 'EXTERNAL_HOME_LOAN_INQUIRY':
        return (
          <>
            <div>
              <label htmlFor="severity" className="text-sm font-medium text-slate-700">
                Severity
              </label>
              <select
                id="severity"
                className={INPUT_CLASS}
                value={String(formState.severity ?? 'HIGH')}
                onChange={(e) => updateField('severity', e.target.value)}
              >
                {SEVERITY_OPTIONS.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="amount_band" className="text-sm font-medium text-slate-700">
                Amount band
              </label>
              <input
                id="amount_band"
                className={INPUT_CLASS}
                value={String(formState.amount_band ?? '')}
                onChange={(e) => updateField('amount_band', e.target.value)}
                placeholder="e.g. 50L-1Cr"
              />
            </div>
            <div>
              <label
                htmlFor="institution_category"
                className="text-sm font-medium text-slate-700"
              >
                Institution category
              </label>
              <input
                id="institution_category"
                className={INPUT_CLASS}
                value={String(formState.institution_category ?? '')}
                onChange={(e) => updateField('institution_category', e.target.value)}
                placeholder="e.g. PRIVATE_BANK"
              />
            </div>
          </>
        )
      case 'EXTERNAL_CARD_INQUIRY':
        return (
          <>
            <div>
              <label htmlFor="severity" className="text-sm font-medium text-slate-700">
                Severity
              </label>
              <select
                id="severity"
                className={INPUT_CLASS}
                value={String(formState.severity ?? 'MEDIUM')}
                onChange={(e) => updateField('severity', e.target.value)}
              >
                {SEVERITY_OPTIONS.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="card_type" className="text-sm font-medium text-slate-700">
                Card type
              </label>
              <input
                id="card_type"
                className={INPUT_CLASS}
                value={String(formState.card_type ?? '')}
                onChange={(e) => updateField('card_type', e.target.value)}
                placeholder="e.g. TRAVEL_CARD"
              />
            </div>
          </>
        )
      case 'SALARY_CREDIT_STOPPED':
        return (
          <div>
            <label
              htmlFor="previous_monthly_salary"
              className="text-sm font-medium text-slate-700"
            >
              Previous monthly salary (optional)
            </label>
            <input
              id="previous_monthly_salary"
              type="number"
              min={0}
              className={INPUT_CLASS}
              value={String(formState.previous_monthly_salary ?? '')}
              onChange={(e) => updateField('previous_monthly_salary', e.target.value)}
            />
          </div>
        )
      case 'SALARY_CREDIT_RESUMED':
        return (
          <p className="text-sm text-slate-500">
            No additional fields required for salary credit resumed.
          </p>
        )
      case 'LARGE_EXTERNAL_TRANSFER':
        return (
          <>
            <div>
              <label htmlFor="amount" className="text-sm font-medium text-slate-700">
                Amount
              </label>
              <input
                id="amount"
                type="number"
                min={0}
                required
                aria-describedby={mergedErrors.amount ? 'amount-error' : undefined}
                aria-invalid={Boolean(mergedErrors.amount)}
                className={`${INPUT_CLASS} ${mergedErrors.amount ? INPUT_ERROR_CLASS : ''}`}
                value={String(formState.amount ?? '')}
                onChange={(e) => updateField('amount', e.target.value)}
              />
              <FieldError id="amount-error" message={mergedErrors.amount} />
            </div>
            <div>
              <label
                htmlFor="destination_category"
                className="text-sm font-medium text-slate-700"
              >
                Destination category
              </label>
              <input
                id="destination_category"
                className={INPUT_CLASS}
                value={String(formState.destination_category ?? '')}
                onChange={(e) => updateField('destination_category', e.target.value)}
              />
            </div>
          </>
        )
      case 'FIXED_DEPOSIT_MATURITY':
        return (
          <>
            <div>
              <label htmlFor="maturity_date" className="text-sm font-medium text-slate-700">
                Maturity date
              </label>
              <input
                id="maturity_date"
                type="date"
                required
                aria-describedby={mergedErrors.maturity_date ? 'maturity-date-error' : undefined}
                aria-invalid={Boolean(mergedErrors.maturity_date)}
                className={`${INPUT_CLASS} ${mergedErrors.maturity_date ? INPUT_ERROR_CLASS : ''}`}
                value={String(formState.maturity_date ?? '')}
                onChange={(e) => updateField('maturity_date', e.target.value)}
              />
              <FieldError id="maturity-date-error" message={mergedErrors.maturity_date} />
            </div>
            <div>
              <label htmlFor="maturity_amount" className="text-sm font-medium text-slate-700">
                Maturity amount (optional)
              </label>
              <input
                id="maturity_amount"
                type="number"
                min={0}
                className={INPUT_CLASS}
                value={String(formState.maturity_amount ?? '')}
                onChange={(e) => updateField('maturity_amount', e.target.value)}
              />
            </div>
            <label className="flex items-center gap-2 text-sm text-slate-700">
              <input
                type="checkbox"
                checked={Boolean(formState.external_outflow_detected)}
                onChange={(e) => updateField('external_outflow_detected', e.target.checked)}
              />
              External outflow detected
            </label>
          </>
        )
      case 'FOREX_SPEND_INCREASE':
        return (
          <>
            <div>
              <label htmlFor="forex_spend_30d" className="text-sm font-medium text-slate-700">
                Forex spend (30 days)
              </label>
              <input
                id="forex_spend_30d"
                type="number"
                min={0}
                required
                aria-describedby={
                  mergedErrors.forex_spend_30d ? 'forex-spend-error' : undefined
                }
                aria-invalid={Boolean(mergedErrors.forex_spend_30d)}
                className={`${INPUT_CLASS} ${mergedErrors.forex_spend_30d ? INPUT_ERROR_CLASS : ''}`}
                value={String(formState.forex_spend_30d ?? '')}
                onChange={(e) => updateField('forex_spend_30d', e.target.value)}
              />
              <FieldError id="forex-spend-error" message={mergedErrors.forex_spend_30d} />
            </div>
            <div>
              <label
                htmlFor="percentage_increase"
                className="text-sm font-medium text-slate-700"
              >
                Percentage increase (optional)
              </label>
              <input
                id="percentage_increase"
                type="number"
                className={INPUT_CLASS}
                value={String(formState.percentage_increase ?? '')}
                onChange={(e) => updateField('percentage_increase', e.target.value)}
              />
            </div>
            <label className="flex items-center gap-2 text-sm text-slate-700">
              <input
                type="checkbox"
                checked={Boolean(formState.travel_trigger_detected)}
                onChange={(e) => updateField('travel_trigger_detected', e.target.checked)}
              />
              Travel trigger detected
            </label>
          </>
        )
      case 'DPD_CHANGED':
        return (
          <>
            <div>
              <label htmlFor="previous_dpd" className="text-sm font-medium text-slate-700">
                Previous DPD (optional)
              </label>
              <input
                id="previous_dpd"
                type="number"
                min={0}
                className={INPUT_CLASS}
                value={String(formState.previous_dpd ?? '')}
                onChange={(e) => updateField('previous_dpd', e.target.value)}
              />
            </div>
            <div>
              <label htmlFor="new_dpd" className="text-sm font-medium text-slate-700">
                New DPD
              </label>
              <input
                id="new_dpd"
                type="number"
                min={0}
                required
                aria-describedby={mergedErrors.new_dpd ? 'new-dpd-error' : undefined}
                aria-invalid={Boolean(mergedErrors.new_dpd)}
                className={`${INPUT_CLASS} ${mergedErrors.new_dpd ? INPUT_ERROR_CLASS : ''}`}
                value={String(formState.new_dpd ?? '')}
                onChange={(e) => updateField('new_dpd', e.target.value)}
              />
              <FieldError id="new-dpd-error" message={mergedErrors.new_dpd} />
            </div>
          </>
        )
      case 'PRODUCT_USAGE_DECLINE':
        return (
          <>
            <div>
              <label
                htmlFor="product_inactivity_days"
                className="text-sm font-medium text-slate-700"
              >
                Product inactivity days
              </label>
              <input
                id="product_inactivity_days"
                type="number"
                min={0}
                required
                aria-describedby={
                  mergedErrors.product_inactivity_days ? 'inactivity-days-error' : undefined
                }
                aria-invalid={Boolean(mergedErrors.product_inactivity_days)}
                className={`${INPUT_CLASS} ${mergedErrors.product_inactivity_days ? INPUT_ERROR_CLASS : ''}`}
                value={String(formState.product_inactivity_days ?? '')}
                onChange={(e) => updateField('product_inactivity_days', e.target.value)}
              />
              <FieldError
                id="inactivity-days-error"
                message={mergedErrors.product_inactivity_days}
              />
            </div>
            <div>
              <label
                htmlFor="card_spend_change_pct_30d"
                className="text-sm font-medium text-slate-700"
              >
                Card spend change % (30 days, optional)
              </label>
              <input
                id="card_spend_change_pct_30d"
                type="number"
                className={INPUT_CLASS}
                value={String(formState.card_spend_change_pct_30d ?? '')}
                onChange={(e) => updateField('card_spend_change_pct_30d', e.target.value)}
              />
            </div>
          </>
        )
      case 'BALANCE_DECLINE':
        return (
          <div>
            <label
              htmlFor="balance_change_pct_30d"
              className="text-sm font-medium text-slate-700"
            >
              Balance change % (30 days)
            </label>
            <input
              id="balance_change_pct_30d"
              type="number"
              required
              aria-describedby={
                mergedErrors.balance_change_pct_30d ? 'balance-change-error' : undefined
              }
              aria-invalid={Boolean(mergedErrors.balance_change_pct_30d)}
              className={`${INPUT_CLASS} ${mergedErrors.balance_change_pct_30d ? INPUT_ERROR_CLASS : ''}`}
              value={String(formState.balance_change_pct_30d ?? '')}
              onChange={(e) => updateField('balance_change_pct_30d', e.target.value)}
            />
            <FieldError
              id="balance-change-error"
              message={mergedErrors.balance_change_pct_30d}
            />
          </div>
        )
      case 'INVESTMENT_TRANSFER_INCREASE':
        return (
          <>
            <div>
              <label
                htmlFor="external_transfer_amount_30d"
                className="text-sm font-medium text-slate-700"
              >
                External transfer amount (30 days)
              </label>
              <input
                id="external_transfer_amount_30d"
                type="number"
                min={0}
                required
                aria-describedby={
                  mergedErrors.external_transfer_amount_30d
                    ? 'transfer-amount-error'
                    : undefined
                }
                aria-invalid={Boolean(mergedErrors.external_transfer_amount_30d)}
                className={`${INPUT_CLASS} ${mergedErrors.external_transfer_amount_30d ? INPUT_ERROR_CLASS : ''}`}
                value={String(formState.external_transfer_amount_30d ?? '')}
                onChange={(e) => updateField('external_transfer_amount_30d', e.target.value)}
              />
              <FieldError
                id="transfer-amount-error"
                message={mergedErrors.external_transfer_amount_30d}
              />
            </div>
            <div>
              <label
                htmlFor="destination_category"
                className="text-sm font-medium text-slate-700"
              >
                Destination category
              </label>
              <input
                id="destination_category"
                required
                aria-describedby={
                  mergedErrors.destination_category ? 'destination-category-error' : undefined
                }
                aria-invalid={Boolean(mergedErrors.destination_category)}
                className={`${INPUT_CLASS} ${mergedErrors.destination_category ? INPUT_ERROR_CLASS : ''}`}
                value={String(formState.destination_category ?? '')}
                onChange={(e) => updateField('destination_category', e.target.value)}
              />
              <FieldError
                id="destination-category-error"
                message={mergedErrors.destination_category}
              />
            </div>
            <div>
              <label
                htmlFor="percentage_increase"
                className="text-sm font-medium text-slate-700"
              >
                Percentage increase (optional)
              </label>
              <input
                id="percentage_increase"
                type="number"
                className={INPUT_CLASS}
                value={String(formState.percentage_increase ?? '')}
                onChange={(e) => updateField('percentage_increase', e.target.value)}
              />
            </div>
          </>
        )
      case 'MANUAL_REANALYSIS':
        return (
          <div>
            <label htmlFor="reason" className="text-sm font-medium text-slate-700">
              Reason (optional)
            </label>
            <textarea
              id="reason"
              rows={3}
              className={INPUT_CLASS}
              value={String(formState.reason ?? '')}
              onChange={(e) => updateField('reason', e.target.value)}
            />
          </div>
        )
      default:
        return null
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Simulate event</CardTitle>
        <CardDescription>
          Customer {customerId} · Source system is set automatically per event type.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={(e) => void handleSubmit(e)} noValidate className="space-y-4">
          <div>
            <label htmlFor="event_type" className="text-sm font-medium text-slate-700">
              Event type
            </label>
            <select
              id="event_type"
              className={INPUT_CLASS}
              value={eventType}
              onChange={(e) => handleEventTypeChange(e.target.value as EventType)}
            >
              {EVENT_TYPE_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">{renderFields()}</div>

          <label className="flex items-center gap-2 text-sm text-slate-700">
            <input
              type="checkbox"
              checked={notificationsEnabled}
              onChange={(e) => setNotificationsEnabled(e.target.checked)}
            />
            Enable notifications for this event
          </label>

          {mergedErrors.form ? (
            <p className="text-sm text-red-600" role="alert">
              {mergedErrors.form}
            </p>
          ) : null}

          <Button type="submit" loading={loading} disabled={!customerId}>
            Submit event
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}
