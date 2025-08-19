from django.db import models

# Create your models here.
# ㅇㅋ
class MotionType(models.Model):
    # 동작에 대한 이름 필드
    motion_name = models.CharField(max_length=100, unique=True)

    # 동작에 대한 설명 필드
    description = models.TextField(blank=True)

    def __str__(self):
        return self.motion_name
    

class MotionRecording(models.Model):
    motion_type = models.ForeignKey(MotionType, on_delete=models.CASCADE,
                                    related_name="recordings")
    
    # 언제 해당 기록이 저장이 됐는지에 대한 필드
    recorded_at = models.DateTimeField(auto_now_add=True)

    # 전처리된 센서 데이터의 프레임 수에 대한 필드
    data_frames = models.IntegerField()

    # 해당 동작 기록이 어떤 카테고리에 속하는지
    # reference(모범동작) 또는 zero_score(빵점 동작)
    score_category = models.CharField(max_length=20,
                                      choices=[
                                          ("reference", "모범 동작"),
                                          ("zero_score", "0점 동작")
                                      ])
    
    # 전처리된 센서 데이터를 json 형태로 저장
    sensor_data_json = models.JSONField()

    # db에 저장된 json 데이터를 numpy 배열로 변환하여 반환하는 메서드
    def get_sensor_data_numpy(self):
        import numpy as np
        import pandas as pd

        # json 데이터를 DataFrame으로 변환 후에 numpy 배열로 변환
        if self.sensor_data_json:
            df = pd.DataFrame(self.sensor_data_json)
            return df.values
        
        # 없으면 빈 numpy 배열 반환
        return np.array([])

class UserRecording(models.Model):
    # 해당 기록을 수행한 사용자
    user = models.ForeignKey("auth.User", on_delete=models.CASCADE,
                             related_name="user_recordings")
    
    # 어떤 동작을 수행했는지
    motion_type = models.ForeignKey(MotionType, on_delete=models.CASCADE)

    # 평가 점수
    score = models.FloatField()

    # 사용자가 수행한 원본 센서 데이터
    sensor_data_json = models.JSONField()
    
    # 기록 시간
    recorded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.motion_type.motion_name} ({self.score})"
