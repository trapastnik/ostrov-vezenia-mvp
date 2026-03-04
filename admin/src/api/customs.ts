import api from './client'
import type { CustomsDeclaration, CustomsDeclarationDetail, PaginatedResponse } from '../types'

export async function fetchDeclarations(
  page = 1,
  status?: string,
): Promise<PaginatedResponse<CustomsDeclaration>> {
  const { data } = await api.get('/admin/customs/declarations', {
    params: { page, status },
  })
  return data
}

export async function createDeclaration(
  orderIds: string[],
  goodsLocation?: string,
  operatorNote?: string,
): Promise<CustomsDeclaration> {
  const { data } = await api.post('/admin/customs/declarations', {
    order_ids: orderIds,
    goods_location: goodsLocation,
    operator_note: operatorNote,
  })
  return data
}

export async function fetchDeclaration(id: string): Promise<CustomsDeclarationDetail> {
  const { data } = await api.get(`/admin/customs/declarations/${id}`)
  return data
}

export async function changeDeclarationStatus(
  id: string,
  status: string,
  ftsReference?: string,
): Promise<CustomsDeclaration> {
  const { data } = await api.patch(`/admin/customs/declarations/${id}/status`, {
    status,
    fts_reference: ftsReference,
  })
  return data
}

export async function validateDeclaration(
  id: string,
): Promise<{ valid: boolean; errors: string[] }> {
  const { data } = await api.post(`/admin/customs/declarations/${id}/validate`)
  return data
}

export async function deleteDeclaration(id: string): Promise<void> {
  await api.delete(`/admin/customs/declarations/${id}`)
}

export async function updateOrderItemsCustoms(
  orderId: string,
  updates: { item_index: number; tn_ved_code: string; country_of_origin: string; brand?: string }[],
): Promise<{ ok: boolean; items: any[] }> {
  const { data } = await api.patch(`/admin/customs/orders/${orderId}/items`, { updates })
  return data
}

export async function downloadDeclarationCsv(id: string): Promise<void> {
  const response = await api.get(`/admin/customs/declarations/${id}/export/csv`, {
    responseType: 'blob',
  })
  const url = window.URL.createObjectURL(new Blob([response.data]))
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', `ptd-eg-${id}.csv`)
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

export async function downloadDeclarationPdf(id: string): Promise<void> {
  const response = await api.get(`/admin/customs/declarations/${id}/export/pdf`, {
    responseType: 'blob',
  })
  const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }))
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', `ptd-eg-${id}.pdf`)
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}
