# ROS2 Nav2는 로봇을 목적지까지 어떻게 보내는가?

시리즈 4편. 한국어 내레이션·자막, Manim 구조 설명, Blender 주행 비교, 1920×1080 / 30 fps / 약 6분 30초.

## 학습 목표와 증거 범위

목표 입력 → 경로 계획 → 속도 제어 → 로봇 이동의 관계, 위치/코스트맵의 지속적 갱신, Behavior Tree의 조율 역할을 이해한다. 실제 ROS 2/Nav2 실행이 아닌 **교육용 통합 모형**이다. AMCL은 구조만 복습하고 실험에서는 이상적 Pose를 사용한다. 실제 Nav2 장애물 레이어, rolling grid, controller 플러그인, BehaviorTree.CPP를 재현하지 않는다.

## 코드와 산출물

- [storyboard.json](storyboard.json): 10개 장면, 한국어 대본과 짧은 자막.
- [model.py](model.py): 모의 LiDAR → 원형 장애물 추정 → 비용 가중 A* → 후보 속도 평가 → 차동 구동 운동학의 폐루프.
- [lesson.py](lesson.py): Manim 지도·코스트맵·후보 궤적·데이터 흐름.
- [blender_scene.py](blender_scene.py): 동일 trace의 AMR, 바퀴 회전, 사람, 경로. 저장한 blend를 다시 열어 Pose와 바퀴 각도를 검증한다.
- [prepare_audio.py](prepare_audio.py): 한국어 TTS와 Whisper 기반 알려진 대본 강제 정렬.
- [finish.py](finish.py): 공간 영상 합성, 시간 표시, 썸네일, 게시 패키지.
- [validate.py](validate.py): 운동학·바퀴 변환·속도 제한·센서·100 Hz 간격 평가·도착·자막·미디어 검사.
- [lesson.json](lesson.json): 실험 계약, 출처, 가정, 결과.
- [output/trace.json](output/trace.json): 모든 관측/상태/명령/계획 기록.
- [output/timeline.json](output/timeline.json): 영상 시간과 공간 재생 샘플 대응; 재계획 설명 정지 포함.
- [output/validation.json](output/validation.json): 검증 결과.
- [output/nav2_education_ko.mp4](output/nav2_education_ko.mp4): 최종 영상.
- [publish/package.json](publish/package.json): 제목, 설명, 공개 설정, 채널, 자막, 썸네일.

## 실험

출발 (-3,0,0), 목표 (3,0,0), 단위 m/rad. 센서·제어 10 Hz, 계획은 1초 간격 또는 경로 무효 시. 반지름 0.25m 원형 로봇, 장애물 반지름 0.30m, 바퀴 반지름 0.10m, 트랙 0.45m. 120방향 LiDAR, 범위 3.2m, 가우시안 거리 잡음 σ=0.002m, seed=14.

새 사람은 t=2초에 (0,0.4)에서 나타나 (0,0)까지 이동한다. 정적 지도와 불일치하는 센서 반환점의 최소제곱 원 적합으로 중심을 추정한다. 센서의 실제 물체 라벨/중심은 추정기에 입력하지 않는다. Pose는 명시적으로 이상적 입력이다. 알려진 장애물 반지름을 계획에 사용한다. 관측이 없으면 마지막 장애물 추정을 유지하는 단순화가 있다.

0.15m 8방향 A*, 대각선 모서리 통과 금지, 유클리드 휴리스틱. 비용은 거리와 비음수 장애물 비용을 더한다. 정적 벽과 추정된 장애물에서 공통 거리장을 계산한다. 글로벌 계획은 격자 비용, 로컬 후보 검사는 연속 거리장을 사용한다. 두 독립 Nav2 코스트맵 인스턴스를 실행한 것은 아니다. 그림의 Local window는 설명용 범위다.

컨트롤러는 v∈[0,0.55]m/s, |ω|≤1.5rad/s 후보를 1.5초 동안 예측해 목표점 거리·방향·여유 거리·전진 속도로 평가한다. 경로 무효 시 0 속도로 즉시 전환하는 이상적 정지다. 제어 입력으로부터 정확한 constant-twist 적분을 수행하며, 접촉력·미끄러짐·실제 모터 추종을 계산하지 않는다.

| 조건 | 목표 도달 | 모형 시간 | 최종 위치 오차 | 방향 오차 | 외곽 최소 간격 |
|---|---|---:|---:|---:|---:|
| 장애물 없음 | 성공 | 14.0 s | 0.11773 m | 0 rad | 1.25 m |
| 새 장애물 | 성공 | 17.2 s | 0.11563 m | 0.06844 rad | 0.39811 m |

위치 0.12m 미만 + 방향 0.08rad 미만을 도착으로 정의한다. 새 장애물 조건의 경로 무효 재계획은 1회, 주기적 계획 포함 총 계획 18회. 장애물 중심의 최대 오차 0.01695m. 최소 간격은 100Hz 추가 샘플 검사이며 연속시간 충돌 안전 증명이 아니다. 1회씩의 합성 실험이며 일반 성능/실제 시스템 안전성 평가가 아니다.

## 재현 명령

프로젝트 루트 `/home/sang/make_simulation`에서 실행한다. 의존성은 프로젝트 README와 pyproject.toml을 따른다.

```bash
uv run python topics/08_nav2/model.py
uv run python topics/08_nav2/prepare_audio.py tts
uv run python topics/08_nav2/prepare_audio.py captions
# 빠른 레이아웃 미리보기 (최종 파일과 다른 폴더)
uv run manim -ql --media_dir topics/08_nav2/output/preview topics/08_nav2/lesson.py Nav2Lesson
# 최종 Manim
uv run manim -qh --fps 30 --disable_caching --media_dir topics/08_nav2/output/manim topics/08_nav2/lesson.py Nav2Lesson
# 설치된 Windows Blender 5.2 / WSL Ubuntu-24.04
'/mnt/c/Program Files/Blender Foundation/Blender 5.2/blender.exe' --background --factory-startup --python '\\wsl.localhost\Ubuntu-24.04\home\sang\make_simulation\topics\08_nav2\blender_scene.py'
uv run python topics/08_nav2/finish.py
uv run python topics/08_nav2/validate.py
uv run python youtube-education-publishing-skill/scripts/preflight.py topics/08_nav2/publish/package.json
# 사용자 요청에 따른 공개 게시, 기존 receipt가 있으면 동일 ID로 이어서 처리
uv run python youtube-education-publishing-skill/scripts/upload_video.py topics/08_nav2/publish/package.json
```

## 변경 지점

장애물 등장과 이동은 `model.py:person`, 센서 노이즈/범위는 `lidar`, 비용 지도는 `costmap`, 후보/평가는 `control`, 주기/종료 조건은 `run`을 수정한다. 수정 뒤 모델 검증부터 모든 영상·내레이션의 수치를 맞춘다. 대본은 storyboard.json, 레이아웃은 lesson.py, 공간 카메라는 blender_scene.py, 재생 속도/정지는 finish.py에서 바꾼다.

## 공식 참고

- [Nav2 Behavior Trees](https://docs.nav2.org/rolling/getting_started/nav2_behavior_trees/): 플래너·컨트롤러와 실행 조율.
- [Detailed BT walkthrough](https://docs.nav2.org/jazzy/getting_started/nav2_behavior_trees/detailed_behavior_tree_walkthrough/detailed_behavior_tree_walkthrough/): 상태, 재계획, 복구 역할.
- [Inflation layer](https://docs.nav2.org/jazzy/configuration_and_development/configuration_guide/core_servers/costmap_2d/costmap_plugins/inflation/): 반경 및 비용 감소.
- [Tuning guide](https://docs.nav2.org/rolling/configuration_and_development/tuning_guide/): 플래너/컨트롤러/비용 지도와 로봇 특성.

공식 문서 확인: 2026-09-21. 그림은 개념도이며 특정 배포판의 전체 실행 그래프를 복제하지 않는다.

## 게시 완료

[YouTube 영상](https://www.youtube.com/watch?v=VL8sFwjCCfU) — 공개, 처리 완료, 한국어 자막 serving, 썸네일 등록 확인. 검증 시각: 2026-09-21T23:30:23.905587+00:00. 게시 기록: [receipt.json](publish/receipt.json).
