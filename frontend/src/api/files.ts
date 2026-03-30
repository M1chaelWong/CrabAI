import type { UploadedFile } from '../types'

export async function uploadFile(file: File, conversationId?: string): Promise<UploadedFile> {
  const formData = new FormData()
  formData.append('file', file)

  const url = conversationId
    ? `/api/files/upload?conversation_id=${encodeURIComponent(conversationId)}`
    : '/api/files/upload'

  const res = await fetch(url, {
    method: 'POST',
    body: formData,
  })

  if (!res.ok) {
    const text = await res.text()
    throw new Error(`Upload failed: ${text}`)
  }

  return res.json()
}
