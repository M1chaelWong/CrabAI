import { useCallback, useRef } from 'react'
import { useChatStore } from '../store/chatStore'
import { sendMessageStream } from '../api/messages'
import type { BackendSSEEvent } from '../api/messages'
import type { ContentBlock, ToolCallStatus } from '../types'

export function useChat() {
  const {
    activeConversationId,
    isStreaming,
    streamingContent,
    activeToolCalls,
    pendingFiles,
    addMessage,
    setIsStreaming,
    setStreamingContent,
    appendStreamingText,
    addStreamingBlock,
    updateToolCall,
    clearActiveToolCalls,
    clearPendingFiles,
    updateConversationTitle,
  } = useChatStore()

  const abortRef = useRef<AbortController | null>(null)

  const sendMessage = useCallback(
    async (content: string) => {
      if (!activeConversationId || !content.trim() || isStreaming) return

      // Add user message immediately
      const userMessage = {
        id: crypto.randomUUID(),
        conversation_id: activeConversationId,
        role: 'user' as const,
        content: [{ type: 'text' as const, text: content }],
        created_at: new Date().toISOString(),
      }
      addMessage(userMessage)

      const fileIds = pendingFiles.map((f) => f.id)
      clearPendingFiles()

      setIsStreaming(true)
      setStreamingContent([])
      clearActiveToolCalls()

      const abortController = new AbortController()
      abortRef.current = abortController

      let assistantMessageId = ''
      let model = ''
      let stopReason = ''
      // Local streaming state to avoid race conditions (P2-10)
      let localContent: ContentBlock[] = []
      const toolCallMap = new Map<string, ToolCallStatus>()
      // Accumulate tool input JSON fragments
      let toolInputJsonBuffer = ''

      const handleEvent = (event: BackendSSEEvent) => {
        const eventType = event.event || (event.data.type as string) || ''

        switch (eventType) {
          case 'message_start': {
            const msg = event.data.message as Record<string, unknown> | undefined
            assistantMessageId = (msg?.id as string) || (event.data.message_id as string) || ''
            model = (msg?.model as string) || (event.data.model as string) || ''
            break
          }

          case 'content_block_start': {
            const block = event.data.content_block as Record<string, unknown> | undefined
            if (block?.type === 'text') {
              const initText = (block.text as string) || ''
              localContent.push({ type: 'text', text: initText })
              addStreamingBlock({ type: 'text', text: initText }) // separate copy for store
            } else if (block?.type === 'tool_use') {
              const toolUseId = (block.id as string) || ''
              const name = (block.name as string) || ''
              localContent.push({ type: 'tool_use', id: toolUseId, name, input: {} })
              addStreamingBlock({ type: 'tool_use', id: toolUseId, name, input: {} }) // separate copy

              const tc: ToolCallStatus = { id: toolUseId, name, input: {}, status: 'running' }
              toolCallMap.set(tc.id, tc)
              updateToolCall(tc)
            }
            break
          }

          case 'content_block_delta': {
            const delta = event.data.delta as Record<string, unknown> | undefined
            if (delta?.type === 'text_delta') {
              const text = delta.text as string
              if (!text) break
              const lastBlock = localContent[localContent.length - 1]
              if (lastBlock && lastBlock.type === 'text') {
                lastBlock.text += text // only mutate local copy
                appendStreamingText(localContent.length - 1, text) // store appends independently
              } else {
                localContent.push({ type: 'text', text })
                addStreamingBlock({ type: 'text', text }) // separate copy
              }
            } else if (delta?.type === 'input_json_delta') {
              toolInputJsonBuffer += (delta.partial_json as string) || ''
            }
            break
          }

          case 'content_block_stop': {
            // If we accumulated tool input JSON, parse and update
            if (toolInputJsonBuffer) {
              try {
                const parsedInput = JSON.parse(toolInputJsonBuffer)
                // Update the last tool_use block in localContent
                for (let i = localContent.length - 1; i >= 0; i--) {
                  const block = localContent[i]
                  if (block.type === 'tool_use') {
                    block.input = parsedInput
                    // Update the tool call status with input
                    const tc = toolCallMap.get(block.id)
                    if (tc) {
                      tc.input = parsedInput
                      updateToolCall({ ...tc })
                    }
                    break
                  }
                }
              } catch { /* ignore parse errors */ }
              toolInputJsonBuffer = ''
            }
            break
          }

          case 'tool_result': {
            const toolUseId = (event.data.tool_use_id as string) || ''
            const resultContent = typeof event.data.content === 'string'
              ? event.data.content
              : JSON.stringify(event.data.content)
            const resultBlock: ContentBlock = { type: 'tool_result', tool_use_id: toolUseId, content: resultContent }
            localContent.push(resultBlock)
            addStreamingBlock(resultBlock)

            const tc = toolCallMap.get(toolUseId)
            if (tc) {
              tc.status = 'completed'
              tc.output = resultContent
              updateToolCall({ ...tc })
            }
            break
          }

          case 'message_delta': {
            const delta = event.data.delta as Record<string, unknown> | undefined
            stopReason = (delta?.stop_reason as string) || ''
            break
          }

          case 'message_stop': {
            const assistantMessage = {
              id: assistantMessageId || crypto.randomUUID(),
              conversation_id: activeConversationId,
              role: 'assistant' as const,
              content: localContent as ContentBlock[],
              model,
              stop_reason: stopReason || 'end_turn',
              created_at: new Date().toISOString(),
            }
            addMessage(assistantMessage)
            setStreamingContent([])
            setIsStreaming(false)

            // Update title from first assistant reply
            const state = useChatStore.getState()
            if (state.messages.filter((m) => m.role === 'assistant').length <= 1) {
              const textContent = localContent
                .filter((b): b is { type: 'text'; text: string } => b.type === 'text')
                .map((b) => b.text)
                .join('')
              const title = textContent.slice(0, 50) || 'New Chat'
              updateConversationTitle(activeConversationId, title)
            }
            break
          }

          case 'error': {
            const err = event.data.error as Record<string, unknown> | undefined
            console.error('Stream error:', err?.message || event.data.message)
            setIsStreaming(false)
            break
          }
        }
      }

      try {
        await sendMessageStream(
          activeConversationId,
          content,
          fileIds.length > 0 ? fileIds : undefined,
          handleEvent,
          abortController.signal,
        )
      } catch (err) {
        if ((err as Error).name !== 'AbortError') {
          console.error('Stream failed:', err)
        }
      } finally {
        setIsStreaming(false)
        abortRef.current = null
      }
    },
    [
      activeConversationId,
      isStreaming,
      pendingFiles,
      addMessage,
      setIsStreaming,
      setStreamingContent,
      appendStreamingText,
      addStreamingBlock,
      updateToolCall,
      clearActiveToolCalls,
      clearPendingFiles,
      updateConversationTitle,
    ],
  )

  const stopStreaming = useCallback(() => {
    abortRef.current?.abort()
    setIsStreaming(false)
  }, [setIsStreaming])

  return {
    sendMessage,
    stopStreaming,
    isStreaming,
    streamingContent,
    activeToolCalls,
  }
}
