# R11 — 바퀴 명령의 작동 원리 렌더 실험

목표 M1: 목표 방향→좌우 바퀴 속도 목표→평균/차이→기록된 몸 응답을 같은 수치 예제로 연결한다. M2: 실물 부품과 단순 도식의 좌우 대응을 명확히 한다. M3: 같은 v에서 w=0인 변환 가정을 보여주되 새 물리 실행으로 오해시키지 않는다.

R06 Bullet 실행을 읽기 전용 재사용한다. 교육용 A*+lookahead 제어이며 Nav2/DWB 실행이 아니다. 새 solver 성능 실험이 아니라 표현 실험이다. 기존 R10 Blender 실행 영상은 재사용하고 sample60의 바퀴 명령 변환을 새 Manim으로 렌더한다. 접촉력/달성 바퀴 속도를 발명하지 않는다. topics, 이전 revision, 공유 키트는 수정하지 않는다.

## 결정 근거와 데이터 경계

sample60의 전진/회전 목표는0.172317m/s,+1rad/s다. 교육 모형의 바퀴 간격0.288m를 사용하면 right/left 접선속도 목표0.316317/0.028317m/s다. 저장 모터 축의 부호는−1이며 right/left 순서의 각속도 명령과 정확히 일치한다(`output/actuation_evidence.json`). 음수 모터 값을 후진으로 표시하지 않았다. 기록된 달성 바퀴 속도나 접촉력으로 주장하지 않는다. v 고정/ω0 도식은 변환 가정이며 새 물리 실행이 아니다.

Blender의 기존 스튜디오 파일에서 source2초 상태를 읽어 새로운 overhead 정지 프레임을 렌더했다. Manim은 이 이미지를 앞 방향 위로 정렬해 같은 좌우 바퀴에 대응시킨다. 기존 몸의 물리 응답 영상은 읽기 전용 재사용한다. 고해상도 component frame은 Cycles24samples이며 기존 실행 영상은 기존 EEVEE 렌더다. 렌더러 선택이 새 물리 계산을 의미하지 않는다. Resolve 설정은 변경하지 않았고 기존 FFmpeg 조립기를 사용했다.

## 발견한 문제와 수정

- 새 도식으로 전환할 때 금지 반경 원이 남았다. 해당 context geometry만 제거하고 실제 프레임으로 확인했다.
- 최종 자막을 합치면 두 줄 식/결론/실물 보조 글자가 가까워지거나 겹쳤다. 본문과 식의 위치를 나누고 보조 글자를 짧게 정리해 합본으로 재검사했다. 공유 키트 이관 후보는 caption safe area를 고려한 단순화 도식/식 배치 helper다.
- 측정 B04는23.13초여서 manifest validator의20초 제한을 넘었다. 한 연속 화면을 유지하며 바퀴 변환과 조건 비교를 B04/B04X 두 상태 전환으로 구분했다. 원래 음성을 프레임 경계15.70초에서 분할하고 자막 경계도 맞췄다. 총음성과 설명 속도를 늘리거나 줄이지 않았다. 이것이 향후 모든 문장을 짧게 끊어야 한다는 규칙은 아니다.
- 스튜디오 저장 상태의 실물 부품을 그대로 보여주면 도식과 바퀴 대응은 가능하지만 실제 바퀴 작동을 강조하는 영상은 아니다. bRd 수준의 부품 설명을 위해서는 faithful wheel pair 선택/확대와 기록된 orientation의 국소 재생이 다음 후보다. 키트를 직접 변경하지 않았다.

## 산출물

- `output/planner_physics_ko_v11.mp4`: 최종78.80초1080p30 한국어 영상.
- `output/comparison.html`: R10/R11과 공개 참고 발췌를 로컬에서 비교 재생.
- [COMPARISON.md](COMPARISON.md): 항목별 변화·남은 격차·미검사 항목.
- `output/actuation_evidence.json`, `run_review.json`, `input_identity.json`: 수치/기존 물리 evidence/보호 입력 검증.

기존 자료를 보존하기 위해 Blender frames는 이전 output을 가리키는 읽기 전용 재사용 경로다. 폴더만 독립적으로 옮기면 상대 reference와 링크를 함께 보존해야 한다. 유튜브 업로드/푸시는 이번 요청에 포함하지 않았다.

## 최종 검증

- manifest `--require-media`: PASS; staged7segments PASS.
- 모든 새 Manim/Blender 장면 style: PASS.
- delivery `--require-audio --fps 30 --audio-manifest … --caption-timing … --full-decode`: PASS(1920×1080,78.80초,17문장).
- 기존6개 V9 trace/physics probe 및 제어 규칙 PASS. sample60의 바퀴 변환/순서/축 부호 PASS.
- R10이 보존한 공유 키트/기존 입력10개 해시 유지 PASS.
- render-reviewer 적용:20개 합본 프레임의 overview와 핵심 native 프레임, 수정 구간 native 재검사. 검사한 프레임 범위의 blocker/high0개. M1/M2/M3 met. `output/final_review.json`에 범위와 결함 수정 근거 기록.
- 정상 속도 움직임/음성은 incomplete; 초심자 이해 not_assessed. 전체 교육 검토 PASS나 두 채널 동급 판정은 하지 않았다.

재현: 기존 측정 음성 복사→바뀐 B04 TTS/forced alignment→B04/B04X 프레임 경계 분할→저장 Blender의 component_scene.py 정지 프레임→Manim 저해상도 발췌/1080p 렌더→assemble.py→위 게이트/프레임 검토. 새 물리 실행은 없다.
