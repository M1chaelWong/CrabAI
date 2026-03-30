import { useState, useRef, type KeyboardEvent } from 'react'
import { Send, Paperclip, Square } from 'lucide-react'
import { useFileUpload } from '../../hooks/useFileUpload'
import FileChip from '../files/FileChip'

interface ChatInputProps {
  onSend: (content: string) => void
  onStop: () => void
  isStreaming: boolean
}

export default function ChatInput({ onSend, onStop, isStreaming }: ChatInputProps) {
  const [input, setInput] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { pendingFiles, handleUpload, removePendingFile } = useFileUpload()

  const handleSend = () => {
    const text = input.trim()
    if (!text || isStreaming) return
    onSend(text)
    setInput('')
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleUpload(e.target.files)
      e.target.value = ''
    }
  }

  return (
    <div className="border-t border-gray-700 bg-[#1a1a2e] px-4 py-3">
      {pendingFiles.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-2">
          {pendingFiles.map((file) => (
            <FileChip key={file.id} file={file} onRemove={removePendingFile} />
          ))}
        </div>
      )}
      <div className="flex items-end gap-2 max-w-4xl mx-auto">
        <button
          onClick={() => fileInputRef.current?.click()}
          className="p-2 text-gray-400 hover:text-gray-200 hover:bg-gray-700 rounded-lg transition-colors shrink-0 mb-0.5"
          aria-label="Attach file"
        >
          <Paperclip className="w-5 h-5" />
        </button>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          onChange={handleFileChange}
          className="hidden"
        />
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Send a message..."
          rows={1}
          className="flex-1 resize-none bg-[#2a2b3d] text-gray-100 rounded-xl px-4 py-2.5 text-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 max-h-48 overflow-y-auto"
        />
        {isStreaming ? (
          <button
            onClick={onStop}
            className="p-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors shrink-0 mb-0.5"
            aria-label="Stop generating"
          >
            <Square className="w-5 h-5" />
          </button>
        ) : (
          <button
            onClick={handleSend}
            disabled={!input.trim()}
            className="p-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:text-gray-500 text-white rounded-lg transition-colors shrink-0 mb-0.5"
            aria-label="Send message"
          >
            <Send className="w-5 h-5" />
          </button>
        )}
      </div>
    </div>
  )
}
