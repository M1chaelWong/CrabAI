import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'

interface MarkdownRendererProps {
  content: string
}

export default function MarkdownRenderer({ content }: MarkdownRendererProps) {
  return (
    <div className="prose prose-invert prose-sm max-w-none">
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      rehypePlugins={[rehypeHighlight]}
      components={{
        pre({ children }) {
          return (
            <pre className="overflow-x-auto rounded-lg p-4 text-sm">
              {children}
            </pre>
          )
        },
        a({ href, children }) {
          return (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-400 hover:text-blue-300 underline"
            >
              {children}
            </a>
          )
        },
        table({ children }) {
          return (
            <div className="overflow-x-auto">
              <table className="border-collapse border border-gray-600">
                {children}
              </table>
            </div>
          )
        },
        th({ children }) {
          return (
            <th className="border border-gray-600 px-3 py-1.5 bg-gray-700/50">
              {children}
            </th>
          )
        },
        td({ children }) {
          return (
            <td className="border border-gray-600 px-3 py-1.5">{children}</td>
          )
        },
      }}
    >
      {content}
    </ReactMarkdown>
    </div>
  )
}
