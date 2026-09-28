MAX_PROMPT_LENGTH = 4000
MAX_CREATE_SLIDES = 15
MAX_ACTIONS = 20
MAX_TITLE_LENGTH = 200
MAX_TEXT_LENGTH = 3000

# Existing-slide text sent to the LLM as update context.
MAX_SLIDE_CONTEXT_CHARS = 300
MAX_CONTEXT_CHARS = 6000

# Recent chat messages sent to the LLM when routing a new message.
CHAT_HISTORY_MESSAGES = 12
MAX_HISTORY_MESSAGE_CHARS = 500

# Layout for generated content slides; its title/body placeholders take update_slide text.
CONTENT_SLIDE_LAYOUT = 'TITLE_AND_BODY'
