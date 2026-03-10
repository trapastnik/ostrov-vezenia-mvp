import api from './client'

export interface ChangelogSection {
  title: string
  items: string[]
}

export interface ChangelogEntry {
  version: string
  date: string
  sections: ChangelogSection[]
}

export interface VersionInfo {
  current_version: string
  changelog: ChangelogEntry[]
}

export async function fetchVersionInfo(): Promise<VersionInfo> {
  const { data } = await api.get('/admin/version')
  return data
}
