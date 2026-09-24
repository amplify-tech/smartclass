from rest_framework.routers import SimpleRouter

from .views import JobViewSet

router = SimpleRouter()
router.register('tasks/jobs', JobViewSet, basename='task-job')

urlpatterns = router.urls
