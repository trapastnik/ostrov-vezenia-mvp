import api from './client'

export interface ShipmentGroup {
  id: string
  number: string
  hub: string
  hub_name: string
  transport_type: string
  status: string
  orders_count: number
  total_weight_grams: number
  public_cost_kopecks: number
  contract_cost_kopecks: number
  savings_kopecks: number
  savings_percent: number
  scheduled_at: string | null
  dispatched_at: string | null
  arrived_at_hub_at: string | null
  operator_note: string | null
  created_at: string
}

export interface ShipmentGroupsResponse {
  items: ShipmentGroup[]
  total: number
  page: number
  page_size: number
}

export interface GroupingSettings {
  id: string
  scope: string
  scope_name: string
  enabled: boolean
  max_wait_hours: number
  min_group_size: number
  min_savings_rub: number
  penalty_per_hour_rub: number
  worker_interval_minutes: number
  description: string | null
}

export async function fetchGroups(params: {
  page?: number
  page_size?: number
  status?: string
  hub?: string
}): Promise<ShipmentGroupsResponse> {
  const { data } = await api.get('/admin/groups', { params })
  return data
}

export async function fetchGroup(id: string): Promise<ShipmentGroup> {
  const { data } = await api.get(`/admin/groups/${id}`)
  return data
}

export async function updateGroupStatus(id: string, status: string, note?: string) {
  const { data } = await api.patch(`/admin/groups/${id}/status`, { status, operator_note: note })
  return data
}

export async function forceDispatchGroup(id: string, note?: string) {
  const { data } = await api.post(`/admin/groups/${id}/force-dispatch`, { note })
  return data
}

export async function fetchGroupingSettings(): Promise<GroupingSettings> {
  const { data } = await api.get('/admin/groups/settings/global')
  return data
}

export async function updateGroupingSettings(updates: Partial<GroupingSettings>): Promise<GroupingSettings> {
  const { data } = await api.patch('/admin/groups/settings/global', updates)
  return data
}
