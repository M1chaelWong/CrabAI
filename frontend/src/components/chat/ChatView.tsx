import { useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { useChatStore } from '../../store/chatStore'
import { useChat } from '../../hooks/useChat'
import { listMessages } from '../../api/messages'
import MessageList from './MessageList'
import ChatInput from './ChatInput'

export default function ChatView() {
  const { conversationId } = useParams<{ conversationId: string }>()
  const { setActiveConversationId, setMessages } = useChatStore()
  const { sendMessage, stopStreaming, isStreaming } = useChat()

  useEffect(() => {
    if (conversationId) {
      setActiveConversationId(conversationId)
      listMessages(conversationId)
        .then((msgs) => {
          // Normalize content: ensure it's always ContentBlock[] or string
          const normalized = msgs.map((m) => {
            let content = m.content
            // If content is a string that looks like JSON array, parse it
            if (typeof content === 'string') {
              try {
                const parsed = JSON.parse(content)
                if (Array.isArray(parsed)) {
                  content = parsed
                }
              } catch { /* keep as string */ }
            }
            return { ...m, content }
          })
          setMessages(normalized)
        })
        .catch((err) => console.error('Failed to load messages:', err))
    }
    return () => {
      setActiveConversationId(null)
      setMessages([])
    }
  }, [conversationId, setActiveConversationId, setMessages])

  if (!conversationId) {
    return (
      <div className="flex-1 flex items-center justify-center text-gray-500">
        <div className="text-center">
          <div className="text-5xl mb-4">🦀</div>
          <p className="text-xl font-medium">CrabAI</p>
          <p className="text-sm mt-2">Select or create a conversation to get started</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 flex flex-col min-w-0 min-h-0 overflow-hidden">
      <MessageList />
      <ChatInput
        onSend={sendMessage}
        onStop={stopStreaming}
        isStreaming={isStreaming}
      />
    </div>
  )
}
