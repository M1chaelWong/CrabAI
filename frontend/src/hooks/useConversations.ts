import { useEffect, useCallback } from 'react'
import { useChatStore } from '../store/chatStore'
import {
  listConversations,
  createConversation as apiCreateConversation,
  deleteConversation as apiDeleteConversation,
} from '../api/conversations'
import { useNavigate } from 'react-router-dom'

export function useConversations() {
  const { conversations, setConversations } = useChatStore()
  const navigate = useNavigate()

  const fetchConversations = useCallback(async () => {
    try {
      const data = await listConversations()
      setConversations(data)
    } catch (err) {
      console.error('Failed to fetch conversations:', err)
    }
  }, [setConversations])

  useEffect(() => {
    fetchConversations()
  }, [fetchConversations])

  const createConversation = useCallback(
    async (title?: string) => {
      try {
        const conv = await apiCreateConversation(title)
        setConversations(useChatStore.getState().conversations.length === 0
          ? [conv]
          : [conv, ...useChatStore.getState().conversations])
        navigate(`/c/${conv.id}`)
        return conv
      } catch (err) {
        console.error('Failed to create conversation:', err)
        throw err
      }
    },
    [setConversations, navigate],
  )

  const removeConversation = useCallback(
    async (id: string) => {
      try {
        await apiDeleteConversation(id)
        setConversations(useChatStore.getState().conversations.filter((c) => c.id !== id))
        navigate('/')
      } catch (err) {
        console.error('Failed to delete conversation:', err)
      }
    },
    [setConversations, navigate],
  )

  return {
    conversations,
    fetchConversations,
    createConversation,
    removeConversation,
  }
}
