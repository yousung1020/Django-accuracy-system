from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import MotionSerializer, UserRecordingSerializer
from .safty_training_ai import MotionEvaluator
from .models import MotionType

# 모범 동작 또는 0점 동작을 DB에 저장하는 View
class MotionRecordingView(APIView):
    """
    모범 동작(reference) 또는 0점 동작(zero_score) 데이터를 받아
    전처리 후 DB에 저장합니다.
    ---
    POST /api/ai/recordings/
    Body:
    {
        "motionTypeName": "fire_extinguisher_lift",
        "scoreCategory": "reference",
        "sensorData": [ ... ]
    }
    """
    # 이 API는 보통 관리자나 개발자가 사용하므로, 별도 권한 설정 가능
    # permission_classes = [IsAdminUser] 
    def post(self, request, *args, **kwargs):
        serializer = MotionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# 사용자의 동작을 평가하고 점수를 반환하는 View
class MotionEvaluationView(APIView):
    """
    사용자의 센서 데이터를 받아 모범 동작과 비교하여
    정확도 점수를 계산하고, 그 결과를 DB에 저장한 후 반환합니다.
    ---
    POST /api/ai/evaluate/
    Body:
    {
        "motionName": "fire_extinguisher_lift",
        "sensorData": [ ... ]
    }
    """
    permission_classes = [IsAuthenticated] # 인증된 사용자만 접근 가능

    def post(self, request, *args, **kwargs):
        motion_name = request.data.get("motionName")
        user_sensor_data = request.data.get("sensorData")

        if not motion_name or not user_sensor_data:
            return Response(
                {"error": "motionName과 sensorData 필드는 필수입니다."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            motion_type = MotionType.objects.get(motion_name=motion_name)
        except MotionType.DoesNotExist:
            return Response(
                {"error": f"'{motion_name}'이라는 이름의 동작을 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            evaluator = MotionEvaluator(motion_name)
            result = evaluator.evaluator_user_motion(user_sensor_data)
            
            if "error" in result:
                return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # 평가 결과 저장 로직
            recording_data = {
                "user": request.user.id,
                "motion_type": motion_type.id,
                "score": result.get("score"),
                "sensor_data_json": user_sensor_data
            }
            
            recording_serializer = UserRecordingSerializer(data=recording_data)
            if recording_serializer.is_valid():
                recording_serializer.save()
            else:
                # 평가 자체는 성공했으나, 기록 저장에 실패한 경우
                # 에러 로그를 남기고 사용자에게는 평가 결과만 반환할 수 있음
                print(f"사용자 평가 기록 저장 실패: {recording_serializer.errors}")

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"평가 중 오류 발생: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
