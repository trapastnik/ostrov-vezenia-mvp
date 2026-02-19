import api from './client'

export interface TariffResult {
  cost_kopecks: number
  vat_kopecks: number
  total_kopecks: number
  min_days: number
  max_days: number
}

export interface AddressResult {
  index: string
  region: string
  place: string
  street: string
  house: string
  room: string
  quality_code: string
  validation_code: string
  is_valid: boolean
}

export interface FioResult {
  surname: string
  name: string
  middle_name: string
  quality_code: string
}

export interface PhoneResult {
  country_code: string
  city_code: string
  number: string
  quality_code: string
}

export interface BalanceResult {
  balance_kopecks: number
}

export async function calculatePublicTariff(params: {
  index_from: string
  index_to: string
  weight_grams: number
}): Promise<TariffResult> {
  const { data } = await api.post('/admin/pochta/tariff-public', params)
  return data
}

export async function calculateContractTariff(params: {
  index_from: string
  index_to: string
  weight_grams: number
}): Promise<TariffResult> {
  const { data } = await api.post('/admin/pochta/tariff-contract', params)
  return data
}

export async function normalizeAddress(address: string): Promise<AddressResult> {
  const { data } = await api.post('/admin/pochta/normalize-address', { address })
  return data
}

export async function normalizeFio(fio: string): Promise<FioResult> {
  const { data } = await api.post('/admin/pochta/normalize-fio', { fio })
  return data
}

export async function normalizePhone(phone: string): Promise<PhoneResult> {
  const { data } = await api.post('/admin/pochta/normalize-phone', { phone })
  return data
}

export async function getBalance(): Promise<BalanceResult> {
  const { data } = await api.get('/admin/pochta/balance')
  return data
}
