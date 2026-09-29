import { useParams } from 'react-router-dom'

import { ChatPage } from '../components/chat'

export default function PresentationChatPage() {
  const { chatId } = useParams()
  return (
    <ChatPage
      chatType="presentation"
      chatId={chatId}
      chatPath={(id) => `/ppts/chat/${id}`}
      breadcrumbs={[
        { label: 'Home', to: '/' },
        { label: 'PPT', to: '/ppts' },
      ]}
      description="Ask for a presentation, then keep chatting to change it."
      emptyTitle="Start a new presentation"
      emptyDescription='For example: "Generate a 3-slide PPT on Class 6 Physics - Optics."'
    />
  )
}
