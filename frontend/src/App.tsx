import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import ChatPage from './pages/Chat'
import DocumentsPage from './pages/Documents'
import SettingsPage from './pages/Settings'
import ChatbotsPage from './pages/Chatbots'
import LogsPage from './pages/Logs'
import SearchTestPage from './pages/SearchTest'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/chat" replace />} />
          <Route path="chat" element={<ChatPage />} />
          <Route path="chat/:chatbotId" element={<ChatPage />} />
          <Route path="chat/:chatbotId/:conversationId" element={<ChatPage />} />
          <Route path="chatbots" element={<ChatbotsPage />} />
          <Route path="documents" element={<DocumentsPage />} />
          <Route path="search-test" element={<SearchTestPage />} />
          <Route path="logs" element={<LogsPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App

