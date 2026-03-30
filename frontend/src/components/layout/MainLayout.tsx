import { PanelLeft } from 'lucide-react'
import { useChatStore } from '../../store/chatStore'
import Sidebar from './Sidebar'
import ChatView from '../chat/ChatView'

export default function MainLayout() {
  const { sidebarOpen, toggleSidebar } = useChatStore()

  return (
    <div className="flex h-screen w-full bg-[#1a1a2e] text-gray-100 overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 min-h-0 overflow-hidden">
        {!sidebarOpen && (
          <button
            onClick={toggleSidebar}
            className="absolute top-3 left-3 z-10 p-2 text-gray-400 hover:text-gray-200 hover:bg-gray-700 rounded-lg transition-colors"
            aria-label="Open sidebar"
          >
            <PanelLeft className="w-5 h-5" />
          </button>
        )}
        <ChatView />
      </div>
    </div>
  )
}
