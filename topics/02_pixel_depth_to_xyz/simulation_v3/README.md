# Pixel + Depth → XYZ · simulation v3

수정된 Manim/Blender 스킬의 ‘실제 계산’과 ‘한 장면 한 학습 포인트’ 기준을 적용한 새 버전입니다. 기존 완성본을 덮어쓰지 않습니다.

## 결과물

- `output/pixel_depth_simulation_ko_v3.mp4`: 1920×1080, 30 fps, 약 2분 40초, 한국어 음성·자막
- `output/blender/camera_observation_experiment.blend`: 센서/관찰자 카메라와 전체 애니메이션
- `output/trace.json`: 관측→역투영→참조 표면점→오차, 비디오 프레임별 표본 대응
- `output/model_validation.json`, `output/blender/saved_project_validation.json`, `output/validation.json`: 검증 결과
- `output/subtitles.ko.srt`, `.vtt`: 별도 자막

## 계산과 가정

Level 1 합성 기하 센서 실험입니다. 움직이는 구와 정적 장면의 메시 교차로 160×120 깊이와 마스크를 계산하고, 물체 영역 가운데 픽셀의 깊이로 표면점을 역투영합니다. 물체 중심과 표면점은 다릅니다. 광학 좌표는 X 오른쪽, Y 아래, Z 전방, 공간 단위 m입니다. 깊이는 직선거리가 아니라 광학축 성분입니다.

`fx=fy=150 px`, `(cx,cy)=(79.5,59.5)`, seed 20260916. 10초/301표본의 같은 경로에 대해 이상적 기준, σZ=0.04 m 가우시안 잡음, 역투영 fx만 120 px, 보정 복구를 비교합니다. 3D 위치 RMSE는 각각 약 0, 40.33, 59.99, 0 mm입니다. 실제 카메라의 측정 정확도나 로봇 제어 성능을 의미하지 않습니다. 이상적 마스크, 왜곡 없는 핀홀, 영상/깊이 정렬을 가정하며 실제 센서의 모든 노이즈를 재현하지 않습니다.

`P=Z((u-cx)/fx,(v-cy)/fy,1)`이며 깊이 오차는 광선 방향, 잘못된 fx는 X 방향으로 전파됩니다. 얻은 점은 카메라 좌표이므로 로봇에서 쓰려면 TF 변환, 자세/접근점 설정과 계획이 별도로 필요합니다.

각 실험은 처음 1초 정지 후 10초를 실시간 재생하고 끝 상태를 설명 동안 유지합니다. 마지막 요약은 정지 장면입니다. `trace.video_map`이 실제 기준이며 별도의 임의 보간으로 값을 만들지 않습니다.

## 구성과 재생성

- `experiment.py`: 단위·내부 파라미터·경로·역투영
- `blender_experiment.py`: 실제 메시 관측 생성 및 Blender 렌더
- `lesson.py`: Manim 수식·단계별 설명
- `finish_video.py`: 공유 trace로 RGB/깊이/3D/수치/오차 그래프 합성, 음량 조절 및 자막
- `validate_model.py`, `check_blender.py`, `validate_video.py`: 수치·저장 프로젝트·최종 영상 검증

기존 `../simulation_v2`의 검증된 관측 데이터와 한국어 Edge TTS / Whisper 정렬 음성을 재사용합니다. `assets/audio`, `output/data`에 원본 파일을 복사하여 버전 폴더를 독립적으로 보존했습니다. 새로운 음성을 생성하거나 Whisper를 재실행했다고 주장하지 않습니다.

```bash
cd /home/sang/make_simulation/topics/02_pixel_depth_to_xyz/simulation_v3
uv run --offline python validate_model.py
uv run --offline manim -ql --fps 30 --media_dir media lesson.py PixelDepthSimulation
uv run --offline manim -qh --fps 30 --media_dir media lesson.py PixelDepthSimulation
# 설치된 Blender로 아래 스크립트 실행. WSL에서는 상위 README의 Windows 실행 경로 사용.
blender --background --factory-startup --python blender_experiment.py -- --render
blender --background --python check_blender.py
uv run --offline python finish_video.py
uv run --offline python validate_video.py
```

관측을 변경하면 `blender_experiment.py -- --simulate`부터 실행하고 렌더 캐시를 별도 버전으로 생성하세요. 내레이션 변경은 v2의 prepare_audio.py 워크플로를 새 버전에 복사하여 사용하고 타임라인을 다시 생성해야 합니다.
