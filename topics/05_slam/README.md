# SLAM은 어떻게 지도와 로봇 위치를 동시에 찾을까?

Level 1 입문 영상, 8장면, 한국어 합성 음성, 한국어 자막, 1920×1080 / 30 fps.
Graph SLAM과 루프 폐쇄는 범위 밖입니다.

## 파일

- `storyboard.json`: 학습 목표를 8장면으로 나눈 내레이션·화면 자막. 음성 파일 길이가 장면 길이를 결정합니다.
- `model.py`: 광선-선분 교점, 잡음, 이동 추정 오차, scan-to-scan point-to-point ICP, 간단한 점유 격자.
- `output/trace.json`: 16개 관측/정답/예상/보정 Pose, ICP 반복, 점유 격자. 공간 영상용 96개 추가 관측도 같은 방과 센서 모형에서 생성합니다.
- `lesson.py`: Manim 도식·좌표·스캔 정합·오차 비교·지도·반복 구조.
- `blender_scene.py`: 같은 trace의 AMR와 LiDAR 공간 표현. 240개 광선 중 매 5번째 표시.
- `prepare_audio.py`: 기존 프로젝트의 Edge TTS·Whisper 파이프라인을 이 주제에 복사하여 사용.
- `finish.py`: 3D 장면 합성, 음량 정규화, H.264/AAC 합본, 썸네일, 챕터, 업로드 패키지.
- `output/slam_education_ko.mp4`: 최종 영상.
- `publish/package.json`: 업로드 설정. 사용자 요청에 따라 public으로 게시 완료.

## 재현

프로젝트 루트 `/home/sang/make_simulation`의 환경을 사용합니다.

```bash
uv run python topics/05_slam/model.py
uv run python topics/05_slam/prepare_audio.py tts
uv run python topics/05_slam/prepare_audio.py captions
uv run manim -qh --fps 30 --disable_caching --media_dir topics/05_slam/output/manim topics/05_slam/lesson.py SlamLesson MapChapter
blender --background --factory-startup --python topics/05_slam/blender_scene.py
blender --background --factory-startup --python topics/05_slam/check_blender.py
uv run python topics/05_slam/finish.py
uv run python topics/05_slam/validate.py
uv run python youtube-education-publishing-skill/scripts/preflight.py topics/05_slam/publish/package.json
```

현재 환경에서는 Blender 5.2 Windows 실행 파일과 `wslpath -w`로 변환한 스크립트 경로를 사용했습니다. 재생 시간은 시뮬레이션 실시간이 아니며 내레이션에 맞추어 늘리거나 멈춥니다.

## 모형과 한계

평면 정적 공간, 미터/라디안. 첫 Pose `(0,0,0)`이 지도 원점입니다. 240개 방향의 최초 벽 교점에 독립 거리 잡음 σ=0.012 m를 더합니다. seed 21. 이전 보정 Pose에서 오차가 있는 상대 이동을 적분하여 초기 추정으로 사용합니다. 35회 ICP에서 가까운 점을 대응시키고 SVD로 강체 변환을 구합니다. 벽 형상과 정답 Pose는 관측 생성/평가에만 사용하며 ICP에는 제공하지 않습니다. 교육용으로 이전 스캔과 정합하며 전체 지도 최적화는 하지 않습니다.

공간 영상의 96개 보간 Pose는 seed 22로 별도 광선 관측을 생성합니다. 이 조밀한 관측은 시각화 전용이며, 표시된 오차는 16개 추정 실험의 값입니다. 모든 좌표 및 관측이 trace에 기록됩니다.

점유 격자는 0.125 m 칸, 통과 -0.32 / 끝점 +1.4 근거, log-odds 범위 [-5,5]입니다. 고정 ray endpoint/통과 갱신의 간단한 교육용 예제이며 반사율·유리·동적 물체·주행 역학·실제 엔코더·확률적 센서 융합은 모델링하지 않습니다. 스캔 정합도 추정이므로 오차가 남습니다.

16개 Pose 위치 RMSE: 오도메트리 0.575712 m, 보정 0.074135 m. sample 1 예상 0.079057 m, 보정 0.009038 m. 단일 합성 실험이며 실제 로봇 성능이 아닙니다.

수정 지점: `model.py`의 WALLS/잡음/이동량, `storyboard.json`의 문장·음성 속도, `lesson.py`의 색·배치, `blender_scene.py`의 카메라·해상도. 변경 후 trace, 음성, 장면, 합본을 순서대로 다시 생성합니다.

기본 구조 참고: https://google-cartographer-ros.readthedocs.io/en/latest/algo_walkthrough.html
Cartographer의 구현 재현이 아닙니다.

## 게시 결과

https://www.youtube.com/watch?v=VGIooUDrPbM

공개 상태, 영상 처리 성공, 한국어 자막 serving, 썸네일 첨부 완료를 API로 확인했습니다. 검증 시각과 파일 해시는 `publish/receipt.json`에 기록했습니다.
