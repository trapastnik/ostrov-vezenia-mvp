import api from './client'

export interface ServiceStatus {
  name: string
  status: 'ok' | 'error' | 'unknown'
  latency_ms?: number
  detail?: string
}

export interface SystemStats {
  orders_total: number
  orders_today: number
  shops_total: number
  batches_total: number
}

export interface HealthResponse {
  version: string
  uptime_seconds: number
  services: ServiceStatus[]
  stats: SystemStats
}

export interface TestResult {
  name: string
  status: 'pass' | 'fail' | 'skip'
  detail?: string
  duration_ms: number
}

export interface SystemTestsResponse {
  results: TestResult[]
  passed: number
  failed: number
  total: number
}

export async function fetchHealth(): Promise<HealthResponse> {
  const { data } = await api.get<HealthResponse>('/admin/health')
  return data
}

export async function runSystemTests(): Promise<SystemTestsResponse> {
  const { data } = await api.post<SystemTestsResponse>('/admin/health/run-tests')
  return data
}
