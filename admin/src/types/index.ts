export interface Operator {
  id: string
  name: string
  role: 'admin' | 'operator'
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
  operator: Operator
}

export interface OrderItem {
  name: string
  sku?: string
  quantity: number
  price_kopecks: number
  weight_grams: number
}

export interface Order {
  id: string
  external_order_id: string
  shop_name: string | null
  status: string
  recipient_name: string
  recipient_phone: string
  recipient_email: string | null
  recipient_address: string
  recipient_postal_code: string
  items: OrderItem[]
  total_amount_kopecks: number
  total_weight_grams: number
  delivery_cost_kopecks: number
  customs_fee_kopecks: number
  track_number: string | null
  internal_track_number: string | null
  batch_id: string | null
  shipment_group_id: string | null
  public_tariff_kopecks: number | null
  contract_tariff_kopecks: number | null
  tariff_savings_kopecks: number | null
  tariff_savings_percent: number | null
  created_at: string
  updated_at: string
}

export interface StatusHistoryEntry {
  old_status: string | null
  new_status: string
  comment: string | null
  created_at: string
}

export interface OrderDetail extends Order {
  history: StatusHistoryEntry[]
}

export interface Shop {
  id: string
  name: string
  domain: string
  api_key: string
  webhook_url: string | null
  customs_fee_kopecks: number
  sender_postal_code: string
  is_active: boolean
  created_at: string
}

export interface Batch {
  id: string
  number: string
  status: string
  orders_count: number
  total_weight_grams: number
  created_at: string
  customs_presented_at: string | null
  customs_cleared_at: string | null
  shipped_at: string | null
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  per_page: number
  pages: number
}

export const STATUS_LABELS: Record<string, string> = {
  accepted: 'Принят',
  awaiting_pickup: 'Ожидает забора',
  received_warehouse: 'На складе',
  batch_forming: 'Формирование партии',
  customs_presented: 'На таможне',
  customs_cleared: 'Таможня пройдена',
  awaiting_carrier: 'Ожидает отправки',
  shipped: 'Отправлен',
  in_transit: 'В пути',
  delivered: 'Доставлен',
  cancelled: 'Отменён',
  problem: 'Проблема',
}

export const STATUS_COLORS: Record<string, string> = {
  accepted: 'bg-blue-100 text-blue-800',
  awaiting_pickup: 'bg-yellow-100 text-yellow-800',
  received_warehouse: 'bg-indigo-100 text-indigo-800',
  batch_forming: 'bg-purple-100 text-purple-800',
  customs_presented: 'bg-orange-100 text-orange-800',
  customs_cleared: 'bg-teal-100 text-teal-800',
  awaiting_carrier: 'bg-cyan-100 text-cyan-800',
  shipped: 'bg-sky-100 text-sky-800',
  in_transit: 'bg-amber-100 text-amber-800',
  delivered: 'bg-green-100 text-green-800',
  cancelled: 'bg-gray-100 text-gray-800',
  problem: 'bg-red-100 text-red-800',
}

export const ALLOWED_TRANSITIONS: Record<string, string[]> = {
  accepted: ['awaiting_pickup', 'cancelled'],
  awaiting_pickup: ['received_warehouse', 'cancelled'],
  received_warehouse: ['batch_forming', 'cancelled'],
  batch_forming: ['customs_presented', 'cancelled'],
  customs_presented: ['customs_cleared', 'problem'],
  customs_cleared: ['awaiting_carrier', 'problem'],
  awaiting_carrier: ['shipped', 'problem'],
  shipped: ['in_transit'],
  in_transit: ['delivered'],
  problem: ['accepted', 'awaiting_pickup', 'received_warehouse', 'batch_forming', 'customs_presented', 'customs_cleared', 'awaiting_carrier', 'shipped'],
}
