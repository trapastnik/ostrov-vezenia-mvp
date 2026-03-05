import api from './client'
import type { TnVedSearchResponse } from '../types'

export async function searchTnVed(
  query: string,
  limit: number = 20,
): Promise<TnVedSearchResponse> {
  const { data } = await api.get('/admin/tnved/search', {
    params: { q: query, limit },
  })
  return data
}

export async function getTnVedCode(code: string) {
  const { data } = await api.get(`/admin/tnved/${code}`)
  return data
}
