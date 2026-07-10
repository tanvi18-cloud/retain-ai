import { toast } from 'sonner'
import { useNavigate } from 'react-router-dom'

import type { RetentionAlertMessage } from '../../types/alert'
import { formatINR } from '../../utils/currency'

const toastedAlertIds = new Set<string>()

export function resetLiveAlertToastsForTests(): void {
  toastedAlertIds.clear()
}

export function showRetentionAlertToast(alert: RetentionAlertMessage): void {
  if (toastedAlertIds.has(alert.alert_id)) return
  toastedAlertIds.add(alert.alert_id)

  const benefit =
    alert.expected_net_benefit != null
      ? ` · Est. benefit ${formatINR(alert.expected_net_benefit, true)}`
      : ''

  toast(alert.title, {
    description: `${alert.severity} · ${alert.customer_id} · Priority ${alert.priority_score}${benefit}`,
    duration: 8000,
    action: {
      label: 'View customer',
      onClick: () => {
        window.location.assign(`/customers/${alert.customer_id}`)
      },
    },
    cancel: {
      label: 'Alert center',
      onClick: () => {
        window.location.assign('/alerts')
      },
    },
  })
}

export function LiveAlertToastBridge() {
  return null
}

export function useLiveAlertNavigation() {
  const navigate = useNavigate()
  return {
    viewCustomer: (customerId: string) => navigate(`/customers/${customerId}`),
    openAlerts: () => navigate('/alerts'),
  }
}
