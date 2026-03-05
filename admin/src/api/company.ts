import api from './client'
import type { CompanySettings } from '../types'

export async function fetchCompanySettings(): Promise<CompanySettings> {
  const { data } = await api.get('/admin/company/settings')
  return data
}

export async function updateCompanySettings(
  updates: Partial<CompanySettings>,
): Promise<CompanySettings> {
  const { data } = await api.patch('/admin/company/settings', updates)
  return data
}

export async function updateRatesFromCBR(): Promise<CompanySettings> {
  const { data } = await api.post('/admin/company/settings/update-rates')
  return data
}
