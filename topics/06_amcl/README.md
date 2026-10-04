# AMCL은 어떻게 로봇의 위치를 찾을까?

SLAM 후속편, Level 1, 한국어 음성·자막, 8장면, 1920×1080 / 30 fps.
학습 목표: 알려진 지도에서 후보 Pose를 이동시키고 관측으로 평가한 뒤 재표본추출하여 위치 분포를 좁힌다.

## 구성

- `storyboard.json`: 내레이션·짧은 화면 자막. TTS 문장별 길이가 전체 영상 타임라인을 결정합니다.
- `model.py`: 고정 지도, 광선 관측, noisy odometry motion model, 단순 likelihood field, 가중치, KLD adaptive resampling.
- `output/trace.json`: 모든 입자/부모 ID/가중치/추정값/관측/정답, 센서 갱신을 끈 비교.
- `lesson.py`: Manim 8장면과 재표본추출 수정 장면. 복제 순간 좌표는 부모와 정확히 같습니다.
- `blender_scene.py`: 이전 SLAM 편의 방과 AMR 자산을 재사용해 같은 기록을 3D로 재생하고 저장 파일을 다시 열어 검증합니다.
- `prepare_audio.py`: 기존 프로젝트의 Edge TTS·Whisper 강제 정렬을 재사용합니다.
- `finish.py`: 합성·음량 정규화·썸네일·메타데이터·공개 업로드 패키지.
- `output/amcl_education_ko.mp4`: 최종 합본.

## 재현

프로젝트 루트 `/home/sang/make_simulation`에서 실행합니다.

```bash
uv run python topics/06_amcl/model.py
uv run python topics/06_amcl/prepare_audio.py tts
uv run python topics/06_amcl/prepare_audio.py captions
uv run manim -qh --fps 30 --disable_caching --media_dir topics/06_amcl/output/manim topics/06_amcl/lesson.py AMCLLesson ResampleChapter SensorChapter LocalizationChapter
blender --background --factory-startup --python topics/06_amcl/blender_scene.py
uv run python topics/06_amcl/finish.py
uv run python topics/06_amcl/validate.py
uv run python youtube-education-publishing-skill/scripts/preflight.py topics/06_amcl/publish/package.json
```

현재 환경은 Windows Blender 5.2와 `wslpath -w`로 변환한 UNC 경로를 사용합니다. 3D 제작은 `../05_slam/output/blender/motion.blend` 자산을 재사용합니다.

## 모델 계약

위치 m, 방향 rad, 0.5초 간격 22개 표본. 초기 후보 900개, free space와 방향의 균등분포, seed 42. 센서 관측 seed 6. 정적 지도는 이전 SLAM 편과 같은 방입니다. 선분 광선 교점으로 36개 거리를 생성하고 σ=0.025 m 잡음을 더합니다. 정답 Pose는 관측 생성과 평가에만 사용하며 필터 입력은 거리 관측·상대 odometry·고정 지도입니다.

각 입자의 방향에 따라 body-frame 이동을 map-frame에 적용합니다. 단순화된 이동 잡음 σ=(0.065 m, 0.065 m, 0.045 rad). 실물 엔코더 역학이나 Nav2 differential motion model의 정확한 재현이 아닙니다.

센서 점수는 거리 d에 대한 `0.95 exp(-0.5(d/0.45)^2) + 0.05/12`의 로그 평균에 6을 곱하는 완화된 likelihood입니다. 점유 격자 거리 변환 대신 연속 선분 거리를 쓰며 실제 Nav2의 likelihood 결합식 재현이 아닙니다. 입자가 벽 또는 지도 밖에 놓인 경우 가중치를 억제합니다. 매 반복 재표본추출 후 가중치는 균등으로 리셋되므로 센서 가중치를 새로 계산합니다.

KLD sampling: x/y/θ 구간 폭 (0.35 m, 0.35 m, 0.25 rad), ε=0.08, z=2.326, 최소180/최대900. 선택된 입자가 차지하는 구간 수로 표본 수를 정합니다. 원래 입자 가중치에 비례해 독립 추출하며, 부모 인덱스를 전부 저장합니다. 입자 회복 주입은 구현하지 않았습니다.

최종 추정은 위치의 가중 평균과 각도의 원형 평균입니다. 다봉 분포 전체 평균이 좋은 Pose가 아닐 수 있으므로 수렴 후 결과만 강조합니다. 실제 AMCL의 군집 선택/공분산/TF/센서 extrinsics/recovery 로직의 완전한 재현은 아닙니다.

seed 42 최종 위치 오차 3.4117 cm, 방향 오차 0.3601°, 센서 갱신을 끈 비교 최종 위치 오차 1.1372 m. 입자 수 900 → 399 → 180. 단일 합성 실험이며 일반 성능 보장이 아닙니다.

## 수정 지점

`model.py`의 지도·잡음·KLD 상수, `storyboard.json`의 대본·음성 속도, `lesson.py`의 색상·레이아웃, `blender_scene.py`의 카메라. 수정 후 모형→음성→렌더→합본→검증을 다시 실행합니다. 이미 게시한 영상은 새 업로드로 덮어쓰지 말고 영수증을 먼저 확인합니다.

공식 참고:
https://docs.nav2.org/rolling/configuration_and_development/configuration_guide/others/configuring_amcl/
https://github.com/ros-navigation/navigation2/tree/main/nav2_amcl

3D 입자와 추정 위치 고리는 가독성을 위해 AMR 위 표시 평면(z=0.65/0.70 m)에 그립니다. 높이를 추정하는 3D 필터가 아니며 추정 상태는 (x,y,θ)뿐입니다.

## 게시 결과

https://www.youtube.com/watch?v=ZrRFR6ma-QY

사용자 요청에 따라 기존 hinoonyaso 채널에 공개 게시했습니다. 영상 처리 성공, 한국어 자막 serving, 썸네일 첨부를 API로 확인했습니다. 검증 시각과 산출물 해시는 `publish/receipt.json`에 기록했습니다.
