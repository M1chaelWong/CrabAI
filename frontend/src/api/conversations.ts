import { apiGet, apiPost, apiPatch, apiDelete } from './client'
import type { Conversation } from '../types'

export async function listConversations(): Promise<Conversation[]> {
  return apiGet<Conversation[]>('/conversations')
}

export async function getConversation(id: string): Promise<Conversation> {
  return apiGet<Conversation>(`/conversations/${id}`)
}

export async function createConversation(title?: string): Promise<Conversation> {
  return apiPost<Conversation>('/conversations', { title: title || 'New Chat' })
}

export async function updateConversation(id: string, data: { title?: string }): Promise<Conversation> {
  return apiPatch<Conversation>(`/conversations/${id}`, data)
}

export async function deleteConversation(id: string): Promise<void> {
  return apiDelete(`/conversations/${id}`)
}
