import { useCallback } from 'react'
import { useChatStore } from '../store/chatStore'
import { uploadFile } from '../api/files'

export function useFileUpload() {
  const { pendingFiles, addPendingFile, removePendingFile, activeConversationId } = useChatStore()

  const handleUpload = useCallback(
    async (files: FileList | File[]) => {
      const fileArray = Array.from(files)
      for (const file of fileArray) {
        try {
          const uploaded = await uploadFile(file, activeConversationId ?? undefined)
          addPendingFile(uploaded)
        } catch (err) {
          console.error('Upload failed:', err)
        }
      }
    },
    [addPendingFile, activeConversationId],
  )

  return {
    pendingFiles,
    handleUpload,
    removePendingFile,
  }
}
