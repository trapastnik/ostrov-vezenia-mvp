import api from './client'
import type { Batch, BatchDetail, PaginatedResponse } from '../types'

export async function fetchBatches(page = 1): Promise<PaginatedResponse<Batch>> {
  const { data } = await api.get('/admin/batches', { params: { page } })
  return data
}

export async function fetchBatch(id: string): Promise<BatchDetail> {
  const { data } = await api.get(`/admin/batches/${id}`)
  return data
}

export async function createBatch(orderIds: string[], goodsLocation?: string): Promise<Batch> {
  const payload: Record<string, any> = { order_ids: orderIds }
  if (goodsLocation) payload.goods_location = goodsLocation
  const { data } = await api.post('/admin/batches', payload)
  return data
}

export async function changeBatchStatus(id: string, status: string): Promise<Batch> {
  const { data } = await api.patch(`/admin/batches/${id}/status`, { status })
  return data
}
