from rest_framework.routers import SimpleRouter

from document.views import DocumentViewSet, GradeViewSet, SubjectViewSet

router = SimpleRouter()
router.register('grades', GradeViewSet, basename='grade')
router.register('subjects', SubjectViewSet, basename='subject')
router.register('documents', DocumentViewSet, basename='document')

urlpatterns = router.urls
