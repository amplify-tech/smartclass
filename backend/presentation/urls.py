from rest_framework.routers import SimpleRouter

from presentation.views import ConversationViewSet, PresentationViewSet

router = SimpleRouter()
router.register('presentations', PresentationViewSet, basename='presentation')
router.register(
    'presentation-conversations',
    ConversationViewSet,
    basename='presentation-conversation',
)

urlpatterns = router.urls
