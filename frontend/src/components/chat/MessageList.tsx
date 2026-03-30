import { useEffect, useRef } from 'react'
import { useChatStore } from '../../store/chatStore'
import MessageBubble from './MessageBubble'
import StreamingIndicator from './StreamingIndicator'
import MarkdownRenderer from '../markdown/MarkdownRenderer'
import ToolCallCard from '../tools/ToolCallCard'
import type { ContentBlock } from '../../types'

export default function MessageList() {
  const { messages, isStreaming, streamingContent, activeToolCalls } =
    useChatStore()
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingContent, isStreaming])

  const renderStreamingContent = (blocks: ContentBlock[]) => {
    return blocks.map((block, i) => {
      if (block.type === 'text') {
        return <MarkdownRenderer key={i} content={block.text} />
      }
      if (block.type === 'tool_use') {
        const tc = activeToolCalls.find((t) => t.id === block.id)
        if (tc) return <ToolCallCard key={block.id} toolCall={tc} />
        return null
      }
      return null
    })
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6">
      {messages.length === 0 && !isStreaming && (
        <div className="flex flex-col items-center justify-center h-full text-gray-500">
          <div className="text-4xl mb-4">🦀</div>
          <p className="text-lg font-medium">CrabAI</p>
          <p className="text-sm mt-1">Start a conversation</p>
        </div>
      )}

      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}

      {isStreaming && streamingContent.length > 0 && (
        <div className="flex justify-start mb-4">
          <div className="max-w-[80%] rounded-2xl px-4 py-3 bg-[#2a2b3d] text-gray-100">
            {renderStreamingContent(streamingContent)}
          </div>
        </div>
      )}

      {isStreaming && streamingContent.length === 0 && (
        <div className="flex justify-start mb-4">
          <div className="rounded-2xl px-4 py-3 bg-[#2a2b3d]">
            <StreamingIndicator />
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  )
}
