import { X, FileText } from 'lucide-react'
import type { UploadedFile } from '../../types'

interface FileChipProps {
  file: UploadedFile
  onRemove: (id: string) => void
}

export default function FileChip({ file, onRemove }: FileChipProps) {
  const sizeLabel =
    file.file_size < 1024
      ? `${file.file_size} B`
      : file.file_size < 1024 * 1024
        ? `${(file.file_size / 1024).toFixed(1)} KB`
        : `${(file.file_size / (1024 * 1024)).toFixed(1)} MB`

  return (
    <div className="inline-flex items-center gap-1.5 bg-gray-700 rounded-lg px-2.5 py-1.5 text-sm text-gray-200">
      <FileText className="w-3.5 h-3.5 text-gray-400 shrink-0" />
      <span className="truncate max-w-[150px]">{file.original_name}</span>
      <span className="text-xs text-gray-400">{sizeLabel}</span>
      <button
        onClick={() => onRemove(file.id)}
        className="ml-0.5 p-0.5 hover:bg-gray-600 rounded transition-colors"
        aria-label={`Remove ${file.original_name}`}
      >
        <X className="w-3 h-3 text-gray-400" />
      </button>
    </div>
  )
}
