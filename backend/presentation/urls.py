from rest_framework.routers import SimpleRouter

from presentation.views import PresentationViewSet

router = SimpleRouter()
router.register('presentations', PresentationViewSet, basename='presentation')

urlpatterns = router.urls
