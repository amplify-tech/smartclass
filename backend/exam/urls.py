from rest_framework.routers import SimpleRouter

from exam.views import (
    ExamViewSet,
    LabelViewSet,
    QuestionGenerationJobViewSet,
    QuestionViewSet,
)

router = SimpleRouter()
router.register(
    'question-generation-jobs',
    QuestionGenerationJobViewSet,
    basename='question-generation-job',
)
router.register('labels', LabelViewSet, basename='label')
router.register('questions', QuestionViewSet, basename='question')
router.register('exams', ExamViewSet, basename='exam')

urlpatterns = router.urls
