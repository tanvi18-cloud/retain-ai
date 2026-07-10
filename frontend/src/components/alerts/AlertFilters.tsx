import type { AlertType, Severity } from '../../types/api'
import { Button } from '../ui/Button'

export interface AlertFiltersState {
  severity?: Severity
  alert_type?: AlertType
  customer_id?: string
  acknowledged?: boolean
}

export interface AlertFiltersProps {
  values: AlertFiltersState
  onChange: (values: AlertFiltersState) => void
  onClear?: () => void
}

const SEVERITIES: Severity[] = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
const ALERT_TYPES: AlertType[] = ['RULES_PREVIEW', 'AGENT_RECOMMENDATION', 'SYSTEM']

type AcknowledgedFilterValue = '' | 'true' | 'false'

function acknowledgedToSelectValue(acknowledged?: boolean): AcknowledgedFilterValue {
  if (acknowledged === true) return 'true'
  if (acknowledged === false) return 'false'
  return ''
}

function selectValueToAcknowledged(value: AcknowledgedFilterValue): boolean | undefined {
  if (value === 'true') return true
  if (value === 'false') return false
  return undefined
}

export function AlertFilters({ values, onChange, onClear }: AlertFiltersProps) {
  const update = (patch: Partial<AlertFiltersState>) => {
    onChange({ ...values, ...patch })
  }

  return (
    <div className="grid gap-4 rounded-xl border border-slate-200 bg-white p-4 sm:grid-cols-2 lg:grid-cols-5">
      <div>
        <label htmlFor="alert-severity-filter" className="text-sm font-medium text-slate-700">
          Severity
        </label>
        <select
          id="alert-severity-filter"
          className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
          value={values.severity ?? ''}
          onChange={(event) =>
            update({
              severity: event.target.value ? (event.target.value as Severity) : undefined,
            })
          }
        >
          <option value="">All</option>
          {SEVERITIES.map((severity) => (
            <option key={severity} value={severity}>
              {severity}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label htmlFor="alert-type-filter" className="text-sm font-medium text-slate-700">
          Alert type
        </label>
        <select
          id="alert-type-filter"
          className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
          value={values.alert_type ?? ''}
          onChange={(event) =>
            update({
              alert_type: event.target.value ? (event.target.value as AlertType) : undefined,
            })
          }
        >
          <option value="">All</option>
          {ALERT_TYPES.map((alertType) => (
            <option key={alertType} value={alertType}>
              {alertType}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label htmlFor="alert-customer-filter" className="text-sm font-medium text-slate-700">
          Customer ID
        </label>
        <input
          id="alert-customer-filter"
          className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
          placeholder="e.g. C001"
          value={values.customer_id ?? ''}
          onChange={(event) =>
            update({
              customer_id: event.target.value.trim() || undefined,
            })
          }
        />
      </div>

      <div>
        <label htmlFor="alert-acknowledged-filter" className="text-sm font-medium text-slate-700">
          Acknowledged
        </label>
        <select
          id="alert-acknowledged-filter"
          className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
          value={acknowledgedToSelectValue(values.acknowledged)}
          onChange={(event) =>
            update({
              acknowledged: selectValueToAcknowledged(event.target.value as AcknowledgedFilterValue),
            })
          }
        >
          <option value="">All</option>
          <option value="false">Unacknowledged</option>
          <option value="true">Acknowledged</option>
        </select>
      </div>

      {onClear ? (
        <div className="flex items-end">
          <Button variant="ghost" onClick={onClear}>
            Clear filters
          </Button>
        </div>
      ) : null}
    </div>
  )
}
