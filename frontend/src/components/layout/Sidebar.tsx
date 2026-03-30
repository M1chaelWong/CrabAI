import { Plus, Trash2, MessageSquare, PanelLeftClose } from 'lucide-react'
import { useNavigate, useParams } from 'react-router-dom'
import { useConversations } from '../../hooks/useConversations'
import { useChatStore } from '../../store/chatStore'

export default function Sidebar() {
  const { conversations, createConversation, removeConversation } =
    useConversations()
  const { sidebarOpen, toggleSidebar } = useChatStore()
  const navigate = useNavigate()
  const { conversationId } = useParams<{ conversationId: string }>()

  if (!sidebarOpen) return null

  return (
    <div className="w-64 h-full bg-[#12122a] border-r border-gray-800 flex flex-col shrink-0">
      <div className="p-3 flex items-center justify-between">
        <button
          onClick={() => createConversation()}
          className="flex items-center gap-2 flex-1 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors"
        >
          <Plus className="w-4 h-4" />
          New Chat
        </button>
        <button
          onClick={toggleSidebar}
          className="ml-2 p-2 text-gray-400 hover:text-gray-200 hover:bg-gray-700 rounded-lg transition-colors"
          aria-label="Close sidebar"
        >
          <PanelLeftClose className="w-4 h-4" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-2 py-1">
        {conversations.map((conv) => (
          <div
            key={conv.id}
            className={`group flex items-center gap-2 px-3 py-2 rounded-lg mb-0.5 cursor-pointer transition-colors ${
              conv.id === conversationId
                ? 'bg-gray-700/60 text-white'
                : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'
            }`}
            onClick={() => navigate(`/c/${conv.id}`)}
          >
            <MessageSquare className="w-4 h-4 shrink-0" />
            <span className="flex-1 truncate text-sm">{conv.title}</span>
            <button
              onClick={(e) => {
                e.stopPropagation()
                removeConversation(conv.id)
              }}
              className="p-1 opacity-0 group-hover:opacity-100 hover:bg-gray-600 rounded transition-all"
              aria-label={`Delete ${conv.title}`}
            >
              <Trash2 className="w-3.5 h-3.5 text-gray-400" />
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
