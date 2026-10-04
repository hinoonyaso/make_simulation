# EP01 — 3축 로봇팔과 Forward Kinematics

주제: **로봇팔은 관절 각도로 손의 위치를 어떻게 계산할까?**

Blender의 3D 로봇팔과 Manim의 평면 투영·누적각·변환행렬을 연결하는 한국어 교육 영상입니다. 프로젝트 환경은 [상위 README](../../../README.md)와 [pyproject.toml](../../../pyproject.toml)을 사용합니다.

## 모델

J1은 베이스 yaw, J2는 shoulder pitch, J3는 elbow pitch입니다. 링크 길이는 2.0 m와 1.5 m, 어깨 높이는 0.6 m입니다. 우수 좌표계에서 Z가 위쪽이며, 양의 pitch는 링크를 들어 올리므로 `Ry(-theta)`로 구현합니다. 프레임 3의 원점은 End Effector입니다.

평면 설명의 `alpha, beta`와 3D 설명의 `theta1, theta2, theta3`를 구분합니다. 평면의 세로 좌표는 3D의 `z-h`에 대응합니다. 동역학·충돌·실물 측정이 없는 이상적인 기구학 모델이며, 화면 동작과 좌표값은 같은 계산 trace에서 재생합니다.

## 제작 자료

- `beat_sheet.md`: 장면 구성과 좌표계 계약
- `narration_manifest.json`: 한국어 대본, 자막 문구, 시각 큐
- `prepare_audio.py`: Edge TTS 발화와 실측 음성 길이에 따른 타임라인
- `model.py`: 해석적 FK, 동차변환 및 수치 검증
- `make_trace.py`: 공통 프레임별 관절각·관절 위치·말단 좌표
- `output/timeline.json`: 음성과 장면 타이밍
- `output/trace.json`: 재현 가능한 계산 데이터
- `output/model_validation.json`: 해석적 사례와 행렬 교차 검증 결과

상위 프로젝트에서 `uv run --offline python topics/01_robot_manipulator/ep01_fk/model.py`로 모델을 검증합니다. 음성 재생성은 `prepare_audio.py`를 실행하며 인터넷 연결이 필요합니다. 그다음 `make_trace.py`를 실행하면 음성 길이에 맞춰 공통 trace를 생성합니다.

## 결과물과 재생성

- `output/EP01_3DOF_Forward_Kinematics_KO.mp4`: 한국어 음성과 화면 자막을 포함한 최종 영상
- `output/subtitles.ko.srt`: 발화 구간에 맞춘 별도 한국어 자막
- `output/blender/ep01_fk_scenes_1_4.blend`: 편집 가능한 3D 장면과 관절 키프레임
- `output/final_validation.json`: 해상도, 프레임 수, 음성 길이, 전체 디코딩 검사

확정 타임라인은 5,351프레임, 30fps, 약 178.37초입니다. `beat_sheet.md`의 168초는 최초 목표이며, 실제 제작에서는 `output/timeline.json`의 측정된 음성 길이를 사용합니다. 모든 길이를 바꾸려면 Manim의 장면 이벤트 프레임도 함께 수정해야 합니다.

상위 `make_simulation` 디렉터리에서 수식 장면을 출력합니다.

```bash
uv run --offline manim -qh --fps 30 \
  --media_dir topics/01_robot_manipulator/ep01_fk/output/manim/final \
  -o lesson topics/01_robot_manipulator/ep01_fk/manim_scene.py EP01ForwardKinematics
uv run --offline python topics/01_robot_manipulator/ep01_fk/align_manim.py
```

Blender에서 `blender_scene.py -- --preview`로 네 대표 프레임을 먼저 확인하고 `-- --render`로 출력합니다. 이 환경의 Windows Blender 실행 방식은 [기존 Blender 제작 문서](../BLENDER_PRODUCTION.md)를 따릅니다. 장면 스크립트 경로만 `ep01_fk/blender_scene.py`로 바꿉니다. 동일 자세의 정지 구간은 프레임을 재사용하며 움직이는 구간은 30fps입니다.

```bash
uv run --offline python topics/01_robot_manipulator/ep01_fk/finish_video.py
uv run --offline python topics/01_robot_manipulator/ep01_fk/validate_delivery.py
```

합성은 FFmpeg로 프레임 단위 배치와 자막·음성 결합을 수행합니다. DaVinci Resolve에는 이번 영상 전용 프로젝트와 검토용 타임라인을 별도로 보관합니다. 자막은 음성 인식 결과가 아닌 제작 대본의 축약문이며, 각 합성 발화의 시작과 끝을 기준으로 표시합니다.
