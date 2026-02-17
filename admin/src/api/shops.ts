import api from './client'
import type { Shop, PaginatedResponse } from '../types'

export async function fetchShops(page = 1): Promise<PaginatedResponse<Shop>> {
  const { data } = await api.get('/admin/shops', { params: { page } })
  return data
}

export async function fetchShop(id: string): Promise<Shop> {
  const { data } = await api.get(`/admin/shops/${id}`)
  return data
}

export async function createShop(body: {
  name: string
  domain: string
  webhook_url?: string
  customs_fee_kopecks?: number
  sender_postal_code?: string
}): Promise<Shop> {
  const { data } = await api.post('/admin/shops', body)
  return data
}

export async function updateShop(id: string, body: Record<string, unknown>): Promise<Shop> {
  const { data } = await api.patch(`/admin/shops/${id}`, body)
  return data
}
