# 추상적으로 역/직렬화 하는 논리적 코드 설계

from rest_framework import serializers
from .safty_training_ai import preprocess_sensor_data
from .models import *

class MotionSerializer(serializers.ModelSerializer):
    motionTypeName = serializers.SlugRelatedField(source="motion_type",
                                                  slug_field="motion_name",
                                                  queryset=MotionType.objects.all(),
                                                  write_only=True)
    
    scoreCategory = serializers.CharField(
        source="score_category",
        max_length=20,
    )

    sensorData = serializers.JSONField(write_only=True)

    class Meta:
        model = MotionRecording

        fields = [
            "id",
            "motionTypeName",
            "scoreCategory",
            "sensorData",
            "data_frames",
            "recorded_at"
        ]

        # 역직렬화는 되지 않고, 직렬화만 할 필드(서버에서 계산되는 필드)
        read_only_fields = ["id", "data_frames", "recorded_at"]
    
    def create(self, validated_data):
        raw_sensor_data = validated_data.pop("sensorData")

        # 원본 데이터를 전처리하고 numpy 배열로 변환
        preprocessed_numpy = preprocess_sensor_data(raw_sensor_data)

        # 전처리된 numpy 배열을 python 리스트로 변환하여 모델에 저장
        validated_data["sensor_data_json"] = preprocessed_numpy.tolist()

        # data_frames 필드에 넣을 데이터의 프레임 수
        validated_data["data_frames"] = preprocessed_numpy.shape[0]

        # 필요한 데이터만 값 할당 후 다시 부모 클래스의 create 메서드를 호출(실제 db에 저장)
        return super().create(validated_data)


class UserRecordingSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRecording
        fields = ["id", "user", "motion_type", "score", "sensor_data_json", "recorded_at"]
        read_only_fields = ["id", "recorded_at"]