import { Routes, Route, Navigate } from 'react-router-dom'
import MainLayout from './components/layout/MainLayout'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<MainLayout />} />
      <Route path="/c/:conversationId" element={<MainLayout />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
