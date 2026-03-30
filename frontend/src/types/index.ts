export interface Conversation {
  id: string
  title: string
  created_at: string
  updated_at: string
}

export interface TextBlock {
  type: 'text'
  text: string
}

export interface ToolUseBlock {
  type: 'tool_use'
  id: string
  name: string
  input: Record<string, unknown>
}

export interface ToolResultBlock {
  type: 'tool_result'
  tool_use_id: string
  content: string
  is_error?: boolean
}

export interface ImageBlock {
  type: 'image'
  source: {
    type: 'base64' | 'url'
    media_type: string
    data: string
  }
}

export type ContentBlock = TextBlock | ToolUseBlock | ToolResultBlock | ImageBlock

export interface Message {
  id: string
  conversation_id: string
  role: 'user' | 'assistant'
  content: ContentBlock[] | string
  model?: string
  stop_reason?: string
  created_at: string
}

export interface ToolCallStatus {
  id: string
  name: string
  input: Record<string, unknown>
  status: 'running' | 'completed' | 'error'
  output?: string
}

export interface UploadedFile {
  id: string
  original_name: string
  mime_type: string
  file_size: number
  conversation_id?: string
}

// SSE event types from the streaming API
export interface SSEEvent {
  event: string
  data: string
}

export interface StreamMessageStart {
  type: 'message_start'
  message: {
    id: string
    role: 'assistant'
    model: string
  }
}

export interface StreamContentBlockStart {
  type: 'content_block_start'
  index: number
  content_block: ContentBlock
}

export interface StreamContentBlockDelta {
  type: 'content_block_delta'
  index: number
  delta: {
    type: 'text_delta' | 'input_json_delta'
    text?: string
    partial_json?: string
  }
}

export interface StreamContentBlockStop {
  type: 'content_block_stop'
  index: number
}

export interface StreamMessageDelta {
  type: 'message_delta'
  delta: {
    stop_reason: string
  }
}

export interface StreamMessageStop {
  type: 'message_stop'
}

export interface StreamError {
  type: 'error'
  error: {
    type: string
    message: string
  }
}

export type StreamEvent =
  | StreamMessageStart
  | StreamContentBlockStart
  | StreamContentBlockDelta
  | StreamContentBlockStop
  | StreamMessageDelta
  | StreamMessageStop
  | StreamError
