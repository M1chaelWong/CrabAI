import { create } from 'zustand'
import { updateConversation } from '../api/conversations'
import type {
  Conversation,
  Message,
  ContentBlock,
  ToolCallStatus,
  UploadedFile,
} from '../types'

interface ChatState {
  conversations: Conversation[]
  activeConversationId: string | null
  messages: Message[]
  isStreaming: boolean
  streamingContent: ContentBlock[]
  activeToolCalls: ToolCallStatus[]
  pendingFiles: UploadedFile[]
  sidebarOpen: boolean

  setConversations: (conversations: Conversation[]) => void
  setActiveConversationId: (id: string | null) => void
  setMessages: (messages: Message[]) => void
  addMessage: (message: Message) => void
  setIsStreaming: (streaming: boolean) => void
  setStreamingContent: (content: ContentBlock[]) => void
  appendStreamingText: (index: number, text: string) => void
  addStreamingBlock: (block: ContentBlock) => void
  updateToolCall: (toolCall: ToolCallStatus) => void
  clearActiveToolCalls: () => void
  addPendingFile: (file: UploadedFile) => void
  removePendingFile: (id: string) => void
  clearPendingFiles: () => void
  toggleSidebar: () => void
  setSidebarOpen: (open: boolean) => void
  updateConversationTitle: (id: string, title: string) => void
}

export const useChatStore = create<ChatState>((set) => ({
  conversations: [],
  activeConversationId: null,
  messages: [],
  isStreaming: false,
  streamingContent: [],
  activeToolCalls: [],
  pendingFiles: [],
  sidebarOpen: true,

  setConversations: (conversations) => set({ conversations }),

  setActiveConversationId: (id) => set({ activeConversationId: id }),

  setMessages: (messages) => set({ messages }),

  addMessage: (message) =>
    set((state) => ({ messages: [...state.messages, message] })),

  setIsStreaming: (streaming) => set({ isStreaming: streaming }),

  setStreamingContent: (content) => set({ streamingContent: content }),

  appendStreamingText: (index, text) =>
    set((state) => {
      const content = [...state.streamingContent]
      const block = content[index]
      if (block && block.type === 'text') {
        content[index] = { ...block, text: block.text + text }
      }
      return { streamingContent: content }
    }),

  addStreamingBlock: (block) =>
    set((state) => ({
      streamingContent: [...state.streamingContent, block],
    })),

  updateToolCall: (toolCall) =>
    set((state) => {
      const existing = state.activeToolCalls.findIndex((tc) => tc.id === toolCall.id)
      const calls = [...state.activeToolCalls]
      if (existing >= 0) {
        calls[existing] = toolCall
      } else {
        calls.push(toolCall)
      }
      return { activeToolCalls: calls }
    }),

  clearActiveToolCalls: () => set({ activeToolCalls: [] }),

  addPendingFile: (file) =>
    set((state) => ({ pendingFiles: [...state.pendingFiles, file] })),

  removePendingFile: (id) =>
    set((state) => ({
      pendingFiles: state.pendingFiles.filter((f) => f.id !== id),
    })),

  clearPendingFiles: () => set({ pendingFiles: [] }),

  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),

  setSidebarOpen: (open) => set({ sidebarOpen: open }),

  updateConversationTitle: (id, title) => {
    set((state) => ({
      conversations: state.conversations.map((c) =>
        c.id === id ? { ...c, title } : c,
      ),
    }))
    updateConversation(id, { title }).catch(() => {})
  },
}))
