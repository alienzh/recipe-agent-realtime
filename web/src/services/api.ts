const API_BASE_URL = '/api'

export interface GetConfigResponse {
  app_id: string
  token: string
  uid: string
  channel_name: string
  agent_uid: string
}

export interface VendorOption {
  name: string
  needs_key: boolean
  required_env: string[]
}

const VENDOR_RETRY_DELAYS_MS = [250, 500]

function wait(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export async function getConfig(options?: { channel?: string; uid?: string | number }): Promise<GetConfigResponse> {
  const params = new URLSearchParams()
  if (options?.channel !== undefined && options.channel !== '') {
    params.set('channel', options.channel)
  }
  if (options?.uid !== undefined && options.uid !== '') {
    params.set('uid', String(options.uid))
  }

  const query = params.toString()
  const response = await fetch(`${API_BASE_URL}/get_config${query ? `?${query}` : ''}`, {
    method: 'GET',
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  const result = await response.json()
  if (result.code !== 0 || !result.data) {
    throw new Error(result.msg || 'Failed to get configuration')
  }
  return result.data
}

export async function getVendors(): Promise<{ default: string; vendors: VendorOption[] }> {
  let lastError: unknown

  for (let attempt = 0; attempt <= VENDOR_RETRY_DELAYS_MS.length; attempt += 1) {
    try {
      const response = await fetch(`${API_BASE_URL}/vendors`)
      if (!response.ok) throw new Error(`HTTP ${response.status}`)

      const result = await response.json()
      if (result.code !== 0 || !result.data) {
        throw new Error(result.msg || 'Failed to list vendors')
      }
      return result.data
    } catch (error) {
      lastError = error
      const delay = VENDOR_RETRY_DELAYS_MS[attempt]
      if (delay === undefined) break
      await wait(delay)
    }
  }

  throw lastError instanceof Error ? lastError : new Error('Failed to list vendors')
}

export async function startAgent(
  channelName: string,
  rtcUid: number,
  userUid: number,
  vendor?: string,
): Promise<string> {
  const payload = { channelName, rtcUid, userUid, vendor }

  const response = await fetch(`${API_BASE_URL}/startAgent`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  const result = await response.json()
  if (result.code !== 0 || !result.data?.agent_id) {
    throw new Error(result.msg || 'Failed to start agent')
  }
  return result.data.agent_id
}

export async function stopAgent(agentId: string): Promise<void> {
  if (!agentId) return

  const response = await fetch(`${API_BASE_URL}/stopAgent`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ agentId }),
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
}
