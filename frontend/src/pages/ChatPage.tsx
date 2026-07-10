import { ChatLayout } from '../components/chat/ChatLayout'
import { useDocumentTitle } from '../hooks/useDocumentTitle'

export function ChatPage() {
  useDocumentTitle('RM Copilot')
  return <ChatLayout />
}
