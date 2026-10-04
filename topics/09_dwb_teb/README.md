# DWB와 TEB는 로봇 경로를 어떻게 다르게 제어할까?

시리즈 5편. 한국어 내레이션·자막, Manim 계산 과정, Blender 동일 복도 주행 비교. 1920×1080 / 30 fps / 5분 21초.

## 학습 목표

DWB의 **지역 속도 후보 탐색**과 TEB의 **시간 포함 궤적 최적화**를 구분하고, 둘 다 현재 명령을 실행한 뒤 갱신한다는 공통점을 이해한다. 이 결과는 두 교육용 모형의 계산 기록이다. 실제 Nav2 DWB 또는 ROS 2 TEB 플러그인 실행·벤치마크가 아니다.

## ROS 2 TEB 확인 범위

2026-09-22에 원 저장소의 브랜치·README·플러그인 XML·package.xml을 확인했다.

| 브랜치 | 확인 커밋 | 커밋 일자 |
|---|---|---|
| ros2-master | e4562a62bac75f6004b74661ba1538be9cd07608 | 2024-11-10 |
| humble-devel | 630a22e88dc9fd45be726a762edbb5b776bef231 | 2022-09-12 |

humble-devel의 `teb_local_planner_plugin.xml`은 `teb_local_planner::TebLocalPlannerROS`를 `nav2_core::Controller`로 선언한다. README에는 이전 Dashing 및 특정 Nav2 커밋 설명이 남아 있다. 브랜치 존재/명칭으로 최신 배포판 호환성을 단정하지 않는다. 이 제작에서는 해당 C++ 패키지를 빌드·실행하지 않았다. TEB는 별도 ROS 2 포트·플러그인 맥락이며 Nav2 기본 내장 컨트롤러로 소개하지 않는다. 응답 기록: [teb_sources.json](output/teb_sources.json).

## 파일 구조

- [storyboard.json](storyboard.json): 실험 계약, 8장면 대본, 26개 한국어 자막 문구.
- [model.py](model.py): DWB형 후보 rollout/비용 선택, TEB형 Pose·ΔT 최소제곱 최적화, 폐루프 운동학.
- [lesson.py](lesson.py): 후보 궤적, 비용 표, 포즈/시간, 최적화 중간값, 원리 비교.
- [blender_scene.py](blender_scene.py): 동일 trace로 AMR·바퀴·예측·실행 기록을 렌더링. 저장 blend를 재열어 샘플 Pose/바퀴 각도를 검증.
- [prepare_audio.py](prepare_audio.py): TTS와 Whisper 강제 정렬.
- [finish.py](finish.py): 공간 합성, 챕터, 썸네일, 게시 패키지.
- [validate.py](validate.py): 실제 수치·자막·최종 미디어 검사.
- [lesson.json](lesson.json): 출처, 단위, 인터페이스, 생략 항목과 결과.
- [trace.json](output/trace.json): 4개 주행 + 같은 Pose에서의 두 계산 예시.
- [timeline.json](output/timeline.json): 영상/시뮬레이션 시간 대응 및 최종 정지.
- [validation.json](output/validation.json): 수치 및 미디어 검증 결과.
- [최종 영상](output/dwb_teb_education_ko.mp4), [자막](output/subtitles.ko.srt), [썸네일](output/thumbnail.png), [게시 패키지](publish/package.json).

## 구현된 실험과 경계

시작 (-3,0,0), 목표 (3,0,0), 글로벌 경로 y=0을 두 모형에 동일하게 제공한다. 복도 폭 2.5m, 원형 로봇 반지름 0.22m, 장애물 중심 (0,-0.18)m·반지름 0.30m. 장애물 유무만 변경한 조건을 각각 1회 계산한다. 알고리즘 입력은 **이상적인 Pose와 완전한 정적 장애물 지도**다. LiDAR·AMCL을 실행하거나 센서 추정을 주장하지 않는다. 난수 없음.

두 모형 모두 dt=0.2s(5Hz), v∈[0,0.6]m/s, |ω|≤1.4rad/s, 정확한 constant-twist 차동 구동 적분을 사용한다. 바퀴 반지름 0.10m, 간격 0.42m. 접촉력·미끄러짐·모터 지연 없음. Blender 로봇 형상은 시각화이며 충돌 검사는 단순 원형 footprint 기준이다.

DWB형: 현재 속도 주변 후보 + 정지 후보, 2초 rollout/0.1초 샘플. 경로 편차, 목표 거리, 역여유 거리, 속도 선호, 회전 비용의 가중합. 예측 여유 거리 0.09m 이하 후보 제외. 실제 Nav2 critic/generator 구현과 다르며, 이 비용 항목이 기본 DWB 구성이라는 주장을 하지 않는다.

TEB형: 고정 12개 Pose와 11개 양의 ΔT, 최대 전방 2.4m 국소 목표, 단일 약한 굽힘으로 초기화한 밴드. SciPy `least_squares`로 시간·장애물·횡방향 운동학 잔차·속도 한계·경로 참조·평활 항목을 최소화한다. g2o, 자동 노드 증감, 다중 위상 경로, 실제 TEB 가속도 제약은 구현하지 않았다. 초기 밴드를 매번 구성하는 간소화이며 warm start가 아니다. 첫 구간으로부터 v/ω를 계산해 제한하고 실행 구간 충돌 검사를 거친다. 페널티 제약에 잔차가 남으므로 제약을 엄밀히 만족하는 최적해나 전역 최적을 주장하지 않는다.

속도 탐색 범위, 가속도 처리, 목적 함수와 예측 범위가 서로 다르다. 동일한 장면은 **원리 이해를 위한 통제 조건**이지 실제 패키지 간 공정 성능 평가가 아니다. 영상에는 우열 순위를 표시하지 않는다.

## 측정 결과

| 모형/조건 | 도착 | 모형 시간 | 최종 위치 오차 | 외곽 최소 간격 |
|---|---|---:|---:|---:|
| DWB형 / 빈 복도 | 성공 | 13.2s | 0.09674m | 0.58000m |
| DWB형 / 장애물 | 성공 | 14.2s | 0.09363m | 0.08996m |
| TEB형 / 빈 복도 | 성공 | 10.6s | 0.07919m | 0.58000m |
| TEB형 / 장애물 | 성공 | 10.8s | 0.08470m | 0.20060m |

도착 조건: 위치 오차 <0.10m, |yaw|<0.08rad. 간격 검사는 100Hz 샘플 기반이며 연속시간 안전 증명이 아니다. DWB 0.1초 예측 샘플의 0.09m 검사와 더 촘촘한 실행 검사 값이 약간 다를 수 있다. TEB 주행 중 최대 횡방향 밴드 잔차 약 0.00165m. 계산 예시 Pose=(-1.25,0,0)에서 밴드 목적 함수는 759.058 → 1.221로 감소했으며 실제 계산된 25개 중간 상태를 저장했다. 이는 동일 목적 함수의 초기/최종 비교이며 DWB 비용과 수치 비교할 수 없다.

## 재현

프로젝트 루트 `/home/sang/make_simulation`에서 실행한다. 프로젝트 README와 pyproject.toml의 환경을 사용한다.

```bash
uv run python topics/09_dwb_teb/model.py
uv run python topics/09_dwb_teb/prepare_audio.py tts
uv run python topics/09_dwb_teb/prepare_audio.py captions
uv run manim -ql --media_dir topics/09_dwb_teb/output/preview topics/09_dwb_teb/lesson.py ControllerComparison
uv run manim -qh --fps 30 --disable_caching --media_dir topics/09_dwb_teb/output/manim topics/09_dwb_teb/lesson.py ControllerComparison
'/mnt/c/Program Files/Blender Foundation/Blender 5.2/blender.exe' --background --factory-startup --python '\\wsl.localhost\Ubuntu-24.04\home\sang\make_simulation\topics\09_dwb_teb\blender_scene.py'
uv run python topics/09_dwb_teb/finish.py
uv run python topics/09_dwb_teb/validate.py
uv run python youtube-education-publishing-skill/scripts/preflight.py topics/09_dwb_teb/publish/package.json
# 사용자가 요청한 동일 채널 공개 게시. receipt/동일 ID로 재개하며 중복 업로드하지 않음.
uv run python youtube-education-publishing-skill/scripts/upload_video.py topics/09_dwb_teb/publish/package.json
```

수정 지점: `model.py`의 `dwb` 후보/비용, `residual` 최적화 항목, `teb` 초기화/노드 수/ΔT, 상단 복도/로봇/장애물 상수. 수정 후 모델부터 재검증하고 대본 수치·영상·문서를 동기화한다. 카메라와 재질은 blender_scene.py, 대본은 storyboard.json, 화면 배치는 lesson.py, 공간 영상 시간 변환은 finish.py.

## 출처

- [Nav2 DWB 문서](https://docs.nav2.org/rolling/configuration_and_development/configuration_guide/controller_plugins/dwb_controller/)
- [DWB 원 저장소](https://github.com/ros-navigation/navigation2/tree/main/nav2_dwb_controller): generator/critic 플러그인과 점수 합.
- [TEB ros2-master](https://github.com/rst-tu-dortmund/teb_local_planner/tree/ros2-master)
- [TEB humble-devel](https://github.com/rst-tu-dortmund/teb_local_planner/tree/humble-devel)
- [TEB optimal_planner.cpp](https://github.com/rst-tu-dortmund/teb_local_planner/blob/humble-devel/teb_local_planner/src/optimal_planner.cpp): Pose/TimeDiff 정점, 시간·장애물·운동학·경유점 관련 항목 및 속도 출력.

이전 편: [Nav2 종합편](https://www.youtube.com/watch?v=VL8sFwjCCfU).

## 게시 완료

[YouTube 영상](https://www.youtube.com/watch?v=BTvfIYZTzkA) — 공개, 영상 처리 완료, 한국어 자막 serving, 썸네일 등록 확인. 검증 시각: 2026-09-22T00:24:55.485219+00:00. [게시 기록](publish/receipt.json).
