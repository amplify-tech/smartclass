export const presentationChat = {
  chatType: 'presentation',
  chatPath: (id) => `/ppts/chat/${id}`,
  breadcrumbs: [
    { label: 'Home', to: '/' },
    { label: 'PPT', to: '/ppts' },
  ],
  description: 'Ask for a presentation, then keep chatting to change it.',
  emptyTitle: 'Start a new presentation',
  emptyDescription: 'For example: "Generate a 3-slide PPT on Class 6 Physics - Optics."',
}

export function presentationChatContext(presentation) {
  if (!presentation) return {}
  return {
    presentations: [{
      id: presentation.id,
      title: presentation.title,
      url: presentation.url,
    }],
    active_presentation_id: presentation.id,
  }
}
