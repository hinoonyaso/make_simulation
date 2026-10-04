# A*는 어떻게 최단 경로를 찾을까?

SLAM·AMCL 후속 입문편. Manim 8장면, 한국어 TTS·자막, 1920×1080 / 30 fps.
학습 목표: g+h로 Open의 후보를 선택하고, 비용/parent를 갱신하며, Goal에서 부모를 역추적해 최단 경로를 얻는 과정을 설명한다.

## 파일

- `model.py`: 동일 격자의 A* / h=0 Dijkstra / 독립 BFS 검증. 모든 후보 비용·부모 갱신·Open/Closed·선택 순서를 저장합니다.
- `storyboard.json`: 8장면 대본과 화면 자막. 오디오는 기존 `prepare_audio.py`의 Edge TTS, 알려진 대본에 대한 Whisper 강제 정렬을 사용합니다.
- `lesson.py`: 계산 기록을 재생하는 Manim 원본. 이 편은 2D 알고리즘 설명이므로 Blender를 사용하지 않습니다.
- `output/trace.json`: 탐색 상태, parent, 최종 경로 및 비교 결과.
- `output/render_events.json`: 화면 시각과 탐색 step의 대응.
- `finish.py`: 오디오 정규화·챕터 메타데이터·썸네일·공개 게시 패키지.
- `validate.py`: 알고리즘/화면 기록 연결, 자막 범위, 미디어 정보, 전체 디코딩 검증.
- `output/astar_education_ko.mp4`: 최종 영상.
- `publish/package.json`, 게시 후 `publish/receipt.json`: 공개 업로드 설정과 결과.

## 재현 명령

프로젝트 루트 `/home/sang/make_simulation`의 환경을 사용합니다.

```bash
uv run python topics/07_astar/model.py
uv run python topics/07_astar/prepare_audio.py tts
uv run python topics/07_astar/prepare_audio.py captions
uv run manim -qh --fps 30 --disable_caching --media_dir topics/07_astar/output/manim topics/07_astar/lesson.py AStarLesson
uv run python topics/07_astar/finish.py
uv run python topics/07_astar/validate.py
uv run python youtube-education-publishing-skill/scripts/preflight.py topics/07_astar/publish/package.json
```

## 알고리즘 계약과 한계

12×9 정적 격자. 좌표 (열,행), 행은 아래로 증가합니다. Start=(1,4), Goal=(10,3). 상하좌우 이동만 허용하며 모든 이동 비용은 1입니다. 장애물은 `model.py`의 BLOCKED입니다. 확률성이 없으므로 seed는 없습니다.

A* 우선순위는 (f, h, 삽입 순서)입니다. 이웃은 오른쪽→위→아래→왼쪽 순으로 검사합니다. g는 현재 알려진 최선 비용이며 개선되면 parent를 갱신합니다. 중복 heap 항목은 pop 시 현재 g 및 Closed와 비교해 버립니다. h=Manhattan distance는 이 그래프에서 consistent하므로 Closed를 다시 열지 않습니다. 비일관된 heuristic이나 다른 비용 모델을 이 구현에 그대로 넣으면 최적성을 보장할 수 없습니다. Goal을 발견할 때가 아니라 유효한 최소 f로 꺼낼 때 종료합니다.

Dijkstra 비교는 동일 구현에서 h=0을 사용합니다. 균등 비용이므로 BFS와 같은 거리 순서로 선택합니다. 최단 비용은 독립 queue BFS와 검증합니다. 장애물 없는 격자에서 비용 10, 예제 지도에서 비용 16, Goal 주변이 차단된 지도에서 도달 불가를 검증했습니다.

화면 숫자와 경로는 같은 trace에서 계산합니다. A* 41 / Dijkstra 89는 시작과 목표를 포함한 유효 pop 횟수이며 CPU 시간이나 일반 성능을 뜻하지 않습니다. 예시 g=5,h=7,f=12는 step 11의 (5,5)입니다. parent를 따른 경로와, 장애물을 무시한 h 설명용 점선을 구분합니다. 재생 시간은 내레이션에 맞추어 조절하며 실제 주행이 아닙니다.

Nav2 연결은 역할 설명입니다. Occupancy Grid → Global Costmap → Global Planner → Global Path → Controller. 로봇 크기·회전 제약·센서·인플레이션·NavFn potential 계산·추종 제어기는 이 모형에 구현하지 않았습니다. 비용 가중 격자에서는 최소 비용과 최소 기하학적 길이가 다를 수 있습니다.

수정 지점: `model.py`의 지도/시작/목표/이동 규칙, `storyboard.json`의 내레이션, `lesson.py`의 레이아웃, `finish.py`의 업로드 메타데이터. 예시 숫자가 바뀌면 대본과 관련 화면 라벨도 갱신해야 합니다.

참고:
https://www.redblobgames.com/pathfinding/a-star/introduction.html
https://docs.nav2.org/rolling/configuration_and_development/configuration_guide/planners_plugins/configuring_navfn/

## 게시 결과

https://www.youtube.com/watch?v=j5MNfkM39cc

기존 hinoonyaso 채널에 공개 게시했습니다. 영상 처리 succeeded, 한국어 자막 serving, 썸네일 첨부 완료를 API로 확인했습니다. 파일 해시와 검증 시각은 `publish/receipt.json`에 있습니다.
