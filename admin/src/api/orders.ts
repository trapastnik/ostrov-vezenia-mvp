import api from './client'
import type { Order, OrderDetail, PaginatedResponse } from '../types'

export async function fetchOrders(params: {
  page?: number
  per_page?: number
  status?: string
  shop_id?: string
  search?: string
}): Promise<PaginatedResponse<Order>> {
  const { data } = await api.get('/admin/orders', { params })
  return data
}

export async function fetchOrder(id: string): Promise<OrderDetail> {
  const { data } = await api.get(`/admin/orders/${id}`)
  return data
}

export async function changeOrderStatus(id: string, status: string, comment?: string): Promise<Order> {
  const { data } = await api.patch(`/admin/orders/${id}/status`, { status, comment })
  return data
}
