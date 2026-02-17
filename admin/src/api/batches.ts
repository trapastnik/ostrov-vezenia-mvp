import api from './client'
import type { Batch, PaginatedResponse } from '../types'

export async function fetchBatches(page = 1): Promise<PaginatedResponse<Batch>> {
  const { data } = await api.get('/admin/batches', { params: { page } })
  return data
}

export async function createBatch(orderIds: string[]): Promise<Batch> {
  const { data } = await api.post('/admin/batches', { order_ids: orderIds })
  return data
}
