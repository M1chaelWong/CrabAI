import { apiGet, apiStreamUrl } from './client'
import type { Message } from '../types'

export interface BackendSSEEvent {
  event: string
  data: Record<string, unknown>
}

export async function listMessages(conversationId: string): Promise<Message[]> {
  return apiGet<Message[]>(`/conversations/${conversationId}/messages`)
}

export async function sendMessageStream(
  conversationId: string,
  content: string,
  fileIds?: string[],
  onEvent: (event: BackendSSEEvent) => void = () => {},
  signal?: AbortSignal,
): Promise<void> {
  const url = apiStreamUrl(`/conversations/${conversationId}/messages`)
  const body: Record<string, unknown> = { content }
  if (fileIds && fileIds.length > 0) {
    body.file_ids = fileIds
  }

  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal,
  })

  if (!res.ok) {
    const text = await res.text()
    throw new Error(`API error ${res.status}: ${text}`)
  }

  const reader = res.body?.getReader()
  if (!reader) throw new Error('No response body')

  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    let currentEvent = ''
    for (const line of lines) {
      const trimmed = line.trim()
      if (!trimmed) {
        currentEvent = ''
        continue
      }
      if (trimmed.startsWith(':')) continue

      if (trimmed.startsWith('event: ')) {
        currentEvent = trimmed.slice(7)
      } else if (trimmed.startsWith('data: ')) {
        const dataStr = trimmed.slice(6)
        if (dataStr === '[DONE]') return

        try {
          const data = JSON.parse(dataStr)
          onEvent({ event: currentEvent || data.type || '', data })
        } catch {
          // Skip malformed JSON
        }
      }
    }
  }
}
