import type { Message, ContentBlock, ToolCallStatus } from '../../types'
import MarkdownRenderer from '../markdown/MarkdownRenderer'
import ToolCallCard from '../tools/ToolCallCard'

interface MessageBubbleProps {
  message: Message
  toolCalls?: ToolCallStatus[]
}

function renderContent(
  content: ContentBlock[] | string,
  toolCalls?: ToolCallStatus[],
) {
  if (typeof content === 'string') {
    return <MarkdownRenderer content={content} />
  }

  return content.map((block, i) => {
    switch (block.type) {
      case 'text':
        return <MarkdownRenderer key={i} content={block.text} />
      case 'tool_use': {
        const tc = toolCalls?.find((t) => t.id === block.id)
        if (tc) return <ToolCallCard key={block.id} toolCall={tc} />
        return (
          <ToolCallCard
            key={block.id}
            toolCall={{
              id: block.id,
              name: block.name,
              input: block.input,
              status: 'completed',
            }}
          />
        )
      }
      case 'tool_result':
        return null
      case 'image':
        return (
          <img
            key={i}
            src={
              block.source.type === 'base64'
                ? `data:${block.source.media_type};base64,${block.source.data}`
                : block.source.data
            }
            alt="Uploaded content"
            className="max-w-sm rounded-lg"
          />
        )
      default:
        return null
    }
  })
}

export default function MessageBubble({ message, toolCalls }: MessageBubbleProps) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isUser
            ? 'bg-blue-600 text-white'
            : 'bg-[#2a2b3d] text-gray-100'
        }`}
      >
        {renderContent(message.content, toolCalls)}
      </div>
    </div>
  )
}
