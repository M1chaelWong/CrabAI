import { useState } from 'react'
import { ChevronDown, ChevronRight, Loader2, CheckCircle2, XCircle } from 'lucide-react'
import type { ToolCallStatus } from '../../types'

interface ToolCallCardProps {
  toolCall: ToolCallStatus
}

export default function ToolCallCard({ toolCall }: ToolCallCardProps) {
  const [expanded, setExpanded] = useState(false)

  const statusIcon = {
    running: <Loader2 className="w-4 h-4 animate-spin text-blue-400" />,
    completed: <CheckCircle2 className="w-4 h-4 text-green-400" />,
    error: <XCircle className="w-4 h-4 text-red-400" />,
  }

  return (
    <div className="my-2 rounded-lg border border-gray-700 bg-gray-800/50 overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-300 hover:bg-gray-700/50 transition-colors"
      >
        {expanded ? (
          <ChevronDown className="w-4 h-4 shrink-0" />
        ) : (
          <ChevronRight className="w-4 h-4 shrink-0" />
        )}
        {statusIcon[toolCall.status]}
        <span className="font-mono text-xs">{toolCall.name}</span>
        <span className="ml-auto text-xs text-gray-500">{toolCall.status}</span>
      </button>
      {expanded && (
        <div className="px-3 pb-3 space-y-2">
          {Object.keys(toolCall.input).length > 0 && (
            <div>
              <div className="text-xs text-gray-500 mb-1">Input</div>
              <pre className="text-xs bg-gray-900 rounded p-2 overflow-x-auto text-gray-300">
                {JSON.stringify(toolCall.input, null, 2)}
              </pre>
            </div>
          )}
          {toolCall.output && (
            <div>
              <div className="text-xs text-gray-500 mb-1">Output</div>
              <pre className="text-xs bg-gray-900 rounded p-2 overflow-x-auto text-gray-300 max-h-48 overflow-y-auto">
                {toolCall.output}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
