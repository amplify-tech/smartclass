import { useParams } from 'react-router-dom'

import { ChatPage } from '../components/chat'
import { presentationChat } from './presentationChat'

export default function PresentationChatPage() {
  const { chatId } = useParams()
  return <ChatPage chatId={chatId} {...presentationChat} />
}
