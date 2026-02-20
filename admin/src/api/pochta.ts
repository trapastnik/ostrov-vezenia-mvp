import api from './client'

export interface PochtaLogEntry {
  method: string
  url: string
  headers: Record<string, string>
  request_body: unknown
  response_status: number
  response_body: unknown
  duration_ms: number
}

export interface TariffResult {
  cost_kopecks: number
  vat_kopecks: number
  total_kopecks: number
  min_days: number
  max_days: number
  pochta_log?: PochtaLogEntry[]
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
  pochta_log?: PochtaLogEntry[]
}

export interface FioResult {
  surname: string
  name: string
  middle_name: string
  quality_code: string
  pochta_log?: PochtaLogEntry[]
}

export interface PhoneResult {
  country_code: string
  city_code: string
  number: string
  quality_code: string
  pochta_log?: PochtaLogEntry[]
}

export interface BalanceResult {
  balance_kopecks: number | null
  available: boolean
  message?: string | null
}

export interface TariffCompareResult {
  public_cost_kopecks: number
  public_vat_kopecks: number
  public_total_kopecks: number
  contract_cost_kopecks: number
  contract_vat_kopecks: number
  contract_total_kopecks: number
  savings_kopecks: number
  savings_percent: number
  min_days: number
  max_days: number
  contract_available: boolean
  contract_error: string | null
  pochta_log?: PochtaLogEntry[]
}

export async function compareTariffs(params: {
  index_from: string
  index_to: string
  weight_grams: number
}): Promise<TariffCompareResult> {
  const { data } = await api.post('/admin/pochta/tariff-compare', params)
  return data
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
