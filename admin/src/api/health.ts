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

export interface ServerMetrics {
  ram_total_mb: number
  ram_used_mb: number
  ram_available_mb: number
  ram_used_pct: number
  load_1m: number
  load_5m: number
  load_15m: number
  cpu_count: number
  disk_total_gb: number
  disk_used_gb: number
  disk_free_gb: number
  disk_used_pct: number
  process_pid: number
  process_ram_mb: number
  process_ram_pct: number
}

export async function fetchServerMetrics(): Promise<ServerMetrics> {
  const { data } = await api.get<ServerMetrics>('/admin/health/server')
  return data
}
