import api from './client'
import type { TnVedSearchResponse, TnVedTreeResponse } from '../types'

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

export async function fetchTnVedChildren(
  parentCode?: string,
): Promise<TnVedTreeResponse> {
  const { data } = await api.get('/admin/tnved/children', {
    params: parentCode ? { parent_code: parentCode } : {},
  })
  return data
}
