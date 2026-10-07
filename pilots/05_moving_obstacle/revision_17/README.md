# R17 — 말로 안내하는 기하·보정 반전·같은 상태의 공간 전환

## 범위와 완료 목표
R16의 검증된 기존 물리 기록/성공한 표현/승인된 도출 속도를 유지하며 새 스킬을 시험한다. 교육용 계획·제어와 Bullet 모형이며 Nav2 DWB/실기/센서 실행 검증이 아니다. 공용 키트와 topics, 이전 리비전은 읽기 전용이다.

| 목표 | 확인할 실제 증거 |
|---|---|
| 말과 기하 대응 | B14 같은 각도/호 길이/반지름 차이를 문장과 그림으로 안내 |
| 보정 반전 | B19 실제 source4초의 음수 오차→오른쪽 보정 요청→왼쪽 목표가 큼 |
| 같은 상태 전환 | B19 끝의 source4초 pose/target/landmark→B20 source4초 |
| 굴림 근접 | B08 기록 wheel phase와 고정 바닥 기준점을 낮은 뷰에서 함께 보여줌 |
| 표면 경계 | 같은 pose/camera의 표면 후보에서 상판층/타이어/바닥 경계를 비교 |

B14/B19/B20만 변경된 교육 대본으로 음성을 생성한다. 나머지 승인 음성은 재사용한다. 회전·pose는 기존 solver 기록이며 새 물리 실행이 아니다. 설명용 차축/방향/phase 표시와 지면 history는 render annotation이다. 정확한 접촉력/미끄럼 데이터는 없으며 발명하지 않는다.

## 검증
기술 검증과 표본 프레임 검토 완료. 정상 속도 시청·청취와 초보자 검증은 아래와 같이 구분한다.

## 제작 결정과 데이터 경계
- R16에서 승인된 속도를 출발점으로 삼았으나, R17 새 대본의 최초 미리보기에서 사용자가 “수식들이 너무 빠르게 휙휙 넘어가버려”라고 보고했다. B14 음성의 문장 사이에 2/3/4초의 읽는 시간을 로컬로 삽입하고 수식별 전환 사이를 3초로 분리했다. 새 외부 TTS 전송은 없다. 원본 음성과 편집 기록은 `narration_update/assets/audio/B14_before_reading_pauses.wav`, `output/pacing_edit.json`에 보존했다.
- 측정된 22개 비트/70개 문장 길이의 합은 382.4초(6분22초). 이전 4–6분 제작 가정에서 22초 늘어난 이유는 새 기하 안내와 사용자 피드백에 따른 읽는 시간이다. 최종 재현 스크립트의 범위도 이에 맞춰 390초까지로 조정했다. 검증을 우회하는 미디어 길이 조작은 하지 않았다.
- B14는 미끄럼 없는 이상적 기하이다. 회전하는 두 바퀴가 같은 θ를 공유하고, 반지름을 같은 시작점의 길이로 펼쳐 공통 길이를 제거한다. 호 길이 식에서 반지름과 θ를 복사해 거리 차이/각도/회전 속도로 연결한다. 실제 Bullet 궤적과 동일하다는 주장은 하지 않는다.
- B19는 R06 한 실행의 pose59→115→119를 순서대로 표시한다. 다음 명령의 실제 lookahead도 매 기록마다 갱신한다. command116의 오차는 +0.007164rad, command117은 −0.014684rad로 부호가 바뀐다. 마지막 command120의 오차는 −0.071523rad, 음의 보정 회전과 왼쪽 목표가 더 큰 관계를 보여준다.
- B19 마지막 물리 장면은 pose119(3.9667초), 다음 목표는 command120(4초)이다. Blender에서 실제 자세와 투영점을 기록한다. B20은 같은 그림을 1.5초 유지한 뒤 R12 영상의 317프레임(source120)부터 계속된다. 기록에 없는 자세를 보간하지 않는다. R10의 비선형 source-time 매핑을 그대로 `final_assembly.json`에 남긴다.
- 물리 데이터는 R14 12개 JSON과 동일하며 R06 회피 실행, R10 원본 studio asset, R12 원본 기록 영상, R16 변경 없는 장면/19개 WAV를 읽기 전용 재사용한다. R17은 새 시뮬레이터 실행이 아닌 같은 물리 기록의 새 렌더 실험이다. `validate_cases.py`는 기존 반복·시간 간격 실험의 기록을 재검증한다.
- B08은 두 바퀴 비교를 먼저 보여주고 frame100–125만 한 바퀴와 바닥을 가까이 보여준다. 파란 위상 표시는 설명용으로 실제 기록의 wheel quaternion을 따른다. 바닥 타일/누적 궤적은 세계 좌표에 고정되어 있다. 접촉력·접촉점·정확한 미끄럼량은 데이터가 없으므로 표시하지 않는다.

## 로컬 구현과 키트/스킬 개선 후보
- `phrase()`/`anchor()`: 실제 문장 자막의 시간에서 비트 상대 시간을 얻는다. 스킬의 ‘측정 음성에 맞춰라’만으로 새 대본의 읽는 속도는 보장되지 않았다. 그림 복사→수식 완성→읽는 시간을 서로 다른 검토 대상으로 삼아야 한다.
- `retime_audio.py`: 원본 WAV를 보존하고 특정 문장 사이에만 무음을 추가하며 이후 자막·비트 시간을 이동한다. 키트 후보는 비파괴 읽기 휴지 편집과 검증이다.
- `handoff_scene.py`: 다음 영상과 같은 카메라에서 solver pose/command/투영을 저장한다. 키트 후보는 renderer 전환의 source-pose 인접성과 투영 증거 저장이다.
- `cases_scene.py`: 동일 실제 pose/camera의 재질 후보 및 목적이 달라질 때만 바퀴·바닥 뷰를 만든다. 표면 후보의 차이는 작다. 더 진한 상판의 측면과 타이어/바닥 경계는 확인되지만 재질만으로 큰 세련됨 향상을 주장하지 않는다.
- 후보 PNG의 차이 측정에서 RGBA `getbbox()`는 알파 차이가 0이면 RGB 차이를 숨겼다. RGB로 변환해 비교해야 한다. 후보 차이의 평균은 채널당 약 1.8–2.2/255이다. 이를 동일 이미지나 큰 미감 향상으로 해석하지 않는다.
- 공용 `studio_utils.py`, `manim_kit.py`, topics와 이전 리비전은 수정하지 않았다. 보호된 키트를 변경하지 않고 모든 새 기능을 R17에 두었다.

## 최종 결과와 검증
- 최종 영상: `output/planner_control_long_ko_v17.mp4` — 382.40초, 1920×1080, 30fps, 한국어 음성, 문장 자막70개.
- `validate_visual_manifest.py --require-media`: PASS.
- `scripts/check_scene_style.py reasoning_scene.py cases_scene.py handoff_scene.py`: 모두 PASS.
- `stage_segments.py`: 22segments PASS.
- `scripts/validate_delivery.py --require-audio --fps 30 --audio-manifest assets/audio/manifest.json --caption-timing output/caption_timing.json --full-decode`: PASS. 실제 명령과 출력은 `output/delivery.log`.
- `validate_cases.py`: V9 trace12개/반복·시간간격 비교/기록 물리 검증 PASS. `validate_relations.py`: 기하·동일실행 피드백 PASS. `validate_render.py`: 원본 데이터/19개 동일 WAV/PCM 조립/바퀴 pose181개/pose119→120 연결 PASS.
- render-reviewer 방식으로 실제 최종109프레임을 한 차례 검토했다. `output/final_review/index.json`, `output/final_review_report.json`에 범위와 결과: 표본 프레임 blocker0/high0. B08 바퀴 뷰 진입·이탈, B14 중간식·문장 앵커, B19 보정 부호 반전, B19→B20 같은 pose를 포함한다.
- 최초 수식 미리보기의 빠른 전환은 사용자 피드백으로 재개방하고 수정했다. 수정 미리보기 B14/B15에 사용자가 “이제 따라가기 좋음”이라고 답했다. 이 답을 전체 영상·초보자 이해·기술 정확성 승인으로 확대하지 않는다.
- 5개 개선 목표는 **검토한 시각적 범위에서 met**. 표면 분리 개선은 작고, 바퀴/지면 근접 및 같은 상태로 이어지는 공간 전환이 더 큰 변화다. bRd/3Blue1Brown과 동급이라는 결론은 내리지 않는다.
- 전체 정상 속도 시청·청취는 도구로 직접 검사하지 못했다. 따라서 전체 educational acceptance는 **incomplete**이고, 기술 검증 및 표본 프레임 검토와 분리한다. 초보자 이해는 not_assessed이다.

## 재현
프로젝트 환경에서 `uv run python pilots/05_moving_obstacle/revision_17/render_cases.py`(Windows Blender 접근), `uv run manim -qh --fps 30 --resolution 1920,1080 --disable_caching --media_dir pilots/05_moving_obstacle/revision_17/output/final_render pilots/05_moving_obstacle/revision_17/reasoning_scene.py PatchB14 PatchB19`로 변경 장면을 만든 후 `uv run python pilots/05_moving_obstacle/revision_17/deliver.py --skip-render`를 실행한다. Manim CLI의 옵션은 실제로 `--fps 30 --resolution 1920,1080`처럼 띄어 쓴다. 최초 3D 연결 그림은 `handoff_scene.py`를 동일한 Windows Blender로 먼저 실행해야 한다. 읽기 휴지 편집은 이미 적용되어 있으므로 `retime_audio.py`를 반복 실행하지 않는다. TTS를 다시 전송할 필요가 없다.
