from django.urls import path
from .views import MotionRecordingView, MotionEvaluationView

urlpatterns = [
    path('recordings/', MotionRecordingView.as_view(), name='motion-recording'),
    path('evaluate/', MotionEvaluationView.as_view(), name='motion-evaluation'),
]
