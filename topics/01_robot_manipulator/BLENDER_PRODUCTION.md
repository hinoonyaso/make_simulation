# Blender 3D 확장 영상

기존 5분 47초 Manim 교육 영상의 시뮬레이션 영역을 Blender에서 만든 입체 로봇팔로 교체했습니다. 한국어 내레이션, 수식, Whisper로 시간 구간을 분석하고 교정한 자막을 사용합니다. 기존 Manim 결과 파일도 그대로 보관합니다.

## 완성 파일

- `output/robot_manipulator_blender_ko.mp4`: 수식·한국어 음성·화면 자막을 포함한 1920×1080, 30 fps 완성본
- `output/robot_manipulator_blender_clean_ko.mp4`: 화면 자막 없는 버전. `output/subtitles.ko.srt`를 유튜브에 별도로 추가할 수 있습니다.
- `output/blender/robot_manipulator_3d.blend`: 회전 관절, 카메라, 라벨과 보조선에 키프레임을 저장한 편집용 프로젝트
- `output/youtube_description_blender.txt`: 제목·설명·챕터
- `output/blender/robot_3d_view.mp4`: Blender 시뮬레이션 영역만 모은 900×680 영상

## 모델의 의미

두 회전축은 모두 Z축과 평행하며, 관절 위치는 XY 평면에서 계산합니다. L1=1.0 m, L2=0.8 m는 관절축 간 XY 거리입니다. 링크의 높이 차이와 두께는 기계 구조를 읽기 쉽게 표현한 형상입니다. 6자유도 모델이나 충돌·동역학 시뮬레이션을 구현한 것은 아닙니다.

좌표축은 X=빨강, Y=초록, Z=파랑이며 링크는 보라색과 금속색입니다. 평면의 위아래 방향이나 원의 반지름을 설명할 때는 평면도를, 기계의 두께와 두 팔꿈치 자세를 보여줄 때는 사선 시점을 사용합니다.

사선 시점의 파란 화살표는 관절의 +Z 회전축 방향을 나타내는 평행 이동된 방향 표시입니다. 가독성을 위해 받침대 옆에 배치했으며, 별도의 좌표 원점이나 실제 관절축의 위치를 뜻하지 않습니다. 화면 하단에도 회전축 방향과 운동 평면을 표시합니다.

## 파일과 코드

- `blender_storyboard.md`: 장면별 학습 포인트·카메라·움직임·대본 연결
- `blender_motion.py`: 기존 음성 타임라인에 맞춘 관절 각도, Manim과 동일한 보간 함수
- `blender_scene.py`: 단일 실행 Blender Python 코드. `setup`은 렌더·카메라·조명, `build`는 모델 생성, `apply`는 자세·보조선, `keyframe`은 타임라인 저장을 담당합니다.
- `compose_blender_video.py`: 정지 구간의 프레임 재사용, Manim 수식 화면과 합성, 기존 음성·자막 결합

Blender의 Workbench 렌더 엔진을 사용합니다. 동적 구간은 30 fps로 렌더하고, 정지 구간은 동일한 PNG를 다시 사용합니다. 최종 영상은 1920×1080이며, 왼쪽 Blender 영역은 합성 시 실제 표시되는 크기인 900×680으로 렌더합니다.

## 실행

현재 컴퓨터에 설치된 Windows Blender 5.2.1을 WSL에서 백그라운드로 실행했습니다. Blender 창을 켜둘 필요는 없습니다.

```bash
cd /home/sang/make_simulation/topics/01_robot_manipulator

# 장면별 미리보기
'/mnt/c/Program Files/Blender Foundation/Blender 5.2/blender.exe' \
  --background --factory-startup \
  --python '\\wsl.localhost\Ubuntu-24.04\home\sang\make_simulation\topics\01_robot_manipulator\blender_scene.py' \
  -- --preview

# 3D 프레임 생성과 .blend 저장
'/mnt/c/Program Files/Blender Foundation/Blender 5.2/blender.exe' \
  --background --factory-startup \
  --python '\\wsl.localhost\Ubuntu-24.04\home\sang\make_simulation\topics\01_robot_manipulator\blender_scene.py' \
  -- --render

# 수식·내레이션·자막을 합친 최종 영상
uv run --offline python compose_blender_video.py
```

Linux에 Blender가 설치되어 있다면 `blender --background --factory-startup --python blender_scene.py -- --render`로 실행할 수 있습니다. Blender Python은 Blender에 포함된 Python을 사용하며, `uv`는 음성·자막·검증 및 합성 스크립트의 환경을 관리합니다.

`.blend`를 직접 열면 타임라인의 장면 마커를 선택해 확인할 수 있습니다. 로봇 움직임은 `Joint_1_theta1`, `Joint_2_theta2` 객체의 Z 회전이며, TCP 위치는 `TCP_analytic_position` 객체로 확인합니다. 저장된 `.blend`에서 직접 렌더할 때는 출력 경로를 정하고 `blender -b robot_manipulator_3d.blend -a`처럼 렌더 옵션을 명령 마지막에 둡니다.

## 수정과 검증

형상·재질·카메라는 `blender_scene.py`, 관절의 시작/끝 자세와 보간은 `blender_motion.py`에서 수정합니다. 기존 내레이션·수식과 연결되어 있으므로 링크 길이나 설명 각도를 바꿀 때는 원본 대본과 Manim 수식도 함께 수정해야 합니다.

각 렌더 상태에서 Blender TCP의 월드 XY 좌표를 FK 결과와 비교합니다. 수치 검증 결과는 `output/blender/geometry_validation.json`, 영상 규격과 재생 검사는 `output/blender/final_validation.json`에 저장합니다. 기존 한국어 음성·Whisper 관련 재생성 방법은 `PRODUCTION.md`를 참조하세요.
