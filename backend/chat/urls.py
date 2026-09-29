from rest_framework.routers import SimpleRouter

from chat.views import ConversationViewSet

router = SimpleRouter()
router.register('conversations', ConversationViewSet, basename='conversation')

urlpatterns = router.urls
