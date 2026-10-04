# Pixel + Depth → 3D XYZ

> 최신 재제작 버전: [simulation_v3 설명](simulation_v3/README.md) · [한국어 시뮬레이션 영상](simulation_v3/output/pixel_depth_simulation_ko_v3.mp4). 아래는 기존 설명 영상의 기록입니다.

**3분 53초 · 1920×1080 · 30 fps · 한국어 내레이션과 자막**

Manim으로 수식과 예제를 만든 다음, Blender로 카메라·가상 영상 평면·광선·깊이 평면·3D 점을 제작해 같은 타임라인에 합성합니다. 수식 유도와 행렬, 픽셀 격자 장면은 Manim을 유지하고 공간 관계를 설명하는 6개 챕터에 Blender 장면을 사용합니다.

## 완성 파일

- `output/pixel_depth_blender_ko.mp4`: Blender + Manim 최종본, 한국어 음성과 화면 자막
- `output/pixel_depth_blender_clean_ko.mp4`: 같은 영상과 음성, 화면 자막 없음. SRT를 별도로 사용할 수 있습니다.
- `output/pixel_depth_manim_ko.mp4`: 먼저 제작한 Manim 설명 버전
- `output/subtitles.ko.srt`, `output/subtitles.ko.vtt`: Whisper로 발화 구간을 정렬한 교정 자막 30개
- `output/narration.wav`, `output/narration.ko.txt`: 한국어 음성과 대본
- `output/youtube_description.txt`: 제목, 설명, 10개 챕터와 참고 자료
- `output/blender/pixel_depth_camera.blend`: 키프레임과 챕터 마커를 저장한 편집용 Blender 프로젝트
- `output/blender/camera_3d_view.mp4`: 합성용 3D 영역만 담은 880×640 영상
- `output/review.png`: 장면별 검수 이미지
- `output/validation.json`: 전체 디코딩, 코덱, 타이밍, 좌표 계산 검증
- `output/blender/geometry_validation.json`, `output/blender/saved_project_validation.json`: 렌더 상태와 저장된 프로젝트의 실제 위치 검증

## 좌표와 수식

픽셀은 `u`가 오른쪽, `v`가 아래쪽으로 증가합니다. 카메라 광학 좌표는 `X` 오른쪽, `Y` 아래쪽, `Z` 전방입니다. 공간 좌표와 깊이의 단위는 m, 초점 거리와 주점은 px입니다.

```text
xn = (u - cx) / fx
yn = (v - cy) / fy
Pcamera = Z (xn, yn, 1)
X = (u - cx) Z / fx
Y = (v - cy) Z / fy
Pcamera = Z K^-1 [u, v, 1]^T
```

예시는 `fx=fy=600`, `(cx,cy)=(320,240)`, `(u,v)=(440,300)`, `Z=2 m`입니다. 결과는 `(0.4, 0.2, 2.0) m`, 직선거리는 `R=√4.2≈2.04939 m`입니다. `Z=1 m`이면 `(0.2,0.1,1.0) m`이며, 두 점은 같은 픽셀로 투영됩니다.

`Z`는 광학축 성분입니다. 센서가 광선 방향의 거리 `R`을 제공하면 `Z=R/√(xn²+yn²+1)`로 변환해야 합니다. 이 식은 왜곡 보정된 픽셀과 해당 영상의 내부 행렬, skew=0 모델을 가정합니다. 컬러와 깊이 영상이 정렬됐는지, 깊이가 어느 광학 좌표계의 Z인지, 단위와 유효 값을 확인해야 합니다.

앞쪽의 영상 평면은 설명용 가상 평면입니다. 수식 장면의 삼각형은 일반적인 닮음 관계를 설명하는 도식입니다. Blender 장면은 실제 핀홀 투영 관계를 따르며 렌즈 굴절, 센서 노이즈, 실제 물체 인식 또는 로봇의 동역학을 시뮬레이션하지 않습니다. 카메라 좌표의 점을 로봇 베이스로 옮긴 뒤에는 별도로 자세와 동작 계획이 필요합니다.

## 파일 구조와 수정

- `storyboard.json`: 학습 목표, 10개 챕터, 30개 한국어 발화와 짧은 자막
- `geometry.py`: 카메라 내부 파라미터, 역투영·재투영, 음성 시간에 맞춘 깊이 변화. Manim과 Blender가 같은 값을 사용합니다.
- `pixel_depth_video.py`: 실행 가능한 Manim 코드 전체. `chapter_*`가 장면, `beat()`가 음성 타이밍, `geometry()`와 `pixels()`가 시각화입니다.
- `blender_scene.py`: Blender Python 코드 전체. `setup()`은 렌더·카메라·조명, `build()`는 객체, `apply()`는 상태, `keyframe()`은 편집용 애니메이션을 담당합니다.
- `prepare_audio.py`: Edge TTS와 Whisper base를 사용한 발화별 음성·자막 생성
- `finish_video.py`: Manim 결과 저장 → Blender 프레임 영상화 → 공간 장면 합성 → 자막·음성·챕터 패키징
- `validate_video.py`, `check_blender.py`: 최종 미디어와 저장된 Blender 프로젝트 검사

Blender의 월드 좌표에는 광학 좌표 `(X,Y,Z)`를 `(X,Z,-Y)`로 배치합니다. 행렬식이 +1인 회전이며 좌표계의 손잡이성을 유지합니다. 색은 X=빨강, Y=초록, Z=파랑입니다. 주황색은 선택 픽셀·광선·점입니다.

Workbench 엔진으로 실제 표시 크기인 880×640 영역을 렌더합니다. 정지 상태를 재사용하며 움직임은 30 fps로 계산합니다. 총 6,984 프레임에 273개의 서로 다른 3D 상태를 사용했습니다. `.blend`에는 전체 타임라인의 상태를 저장했습니다.

## 재생성

상위 프로젝트의 공통 `uv` 환경을 사용합니다. Python 3.12, Manim CE, manim-voiceover, Edge TTS, Whisper, FFmpeg, LaTeX/dvisvgm, NanumGothic을 사용합니다. 기존 캐시로 렌더할 때는 네트워크가 필요하지 않으며 새 음성 합성에는 네트워크가 필요합니다.

```bash
cd /home/sang/make_simulation/topics/02_pixel_depth_to_xyz

# 대본을 수정했을 때 음성·자막 재생성
uv run --offline python prepare_audio.py tts
uv run --offline python prepare_audio.py captions

# Manim 미리보기 / 최종본
uv run --offline manim -ql --fps 30 --media_dir media pixel_depth_video.py PixelDepthLesson
uv run --offline manim -qh --fps 30 --media_dir media pixel_depth_video.py PixelDepthLesson

# 특정 장면만 확인
LESSON_CHAPTER=ray uv run --offline manim -ql --fps 30 --media_dir media pixel_depth_video.py PixelDepthLesson
```

현재 WSL 환경에서 설치된 Windows Blender를 실행하는 명령입니다. Blender 창을 열어 둘 필요는 없습니다.

```bash
'/mnt/c/Program Files/Blender Foundation/Blender 5.2/blender.exe' \
  --background --factory-startup \
  --python '\\wsl.localhost\Ubuntu-24.04\home\sang\make_simulation\topics\02_pixel_depth_to_xyz\blender_scene.py' \
  -- --render

uv run --offline python finish_video.py
uv run --offline python validate_video.py
uv run --offline python review_frames.py output/pixel_depth_blender_ko.mp4
```

Linux Blender 환경에서는 `blender --background --factory-startup --python blender_scene.py -- --render`로 실행합니다. `--preview`는 주요 상태 3장의 PNG만 렌더합니다. 저장된 `.blend`를 직접 렌더할 때는 `blender -b output/blender/pixel_depth_camera.blend -a`처럼 렌더 옵션을 마지막에 놓습니다.

## 참고 자료

- [OpenCV Camera Calibration and 3D Reconstruction](https://docs.opencv.org/4.x/d9/d0c/group__calib3d.html)
- [ROS REP-103 광학 좌표계 규약](https://github.com/ros-infrastructure/rep/blob/master/rep-0103.rst)

처음 작성된 40개 발화의 긴 대본은 `archive/storyboard_original.json`에 보존했습니다.
