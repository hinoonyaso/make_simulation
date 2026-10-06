# R09 — 정의한 목표의 다음 렌더 테스트

## 렌더 전 완료 기준

- C1 (Manim): R08의 서로 다른 한국어 문장 Transform을 국소 순차 페이드로 교체한다. 전환 시작/중간/끝에서 흩어진 글자와 중복 문장이 없고 로봇·경로·목표 관계는 유지한다. 교체 후 참조는 실제 표시 객체를 가리킨다.
- C2 (Blender): R08 동일 카메라·solver pose에서 초록 참고 경로와 파랑 실제 이력이 밝은 바닥에 묻히는 정도를 줄인다. 경로 중심선/반경/시간은 유지하고 재질만 변경한다. 회피·목표·최종 비교에서 두 색의 뜻이 구분돼야 한다.
- C3 (편집 회귀 확인): 컷 진입/주요 사건/퇴장에서 로봇과 접촉·여유·목표 관계가 잘리지 않고 최종 합본의 안내·자막이 서로 또는 주요 피사체와 충돌하지 않는다. R08의 승인된 설명·음성·73.93초 길이를 유지한다.

목표 충족과 필수 기술 게이트 완료를 이번 범위의 종료 조건으로 둔다. 새 미적 요구를 추가하지 않는다. 직접 정상 속도 시청·청취와 초심자 첫 이해는 별도 미확인 상태다.

## 결정과 데이터 경계

R08 동일 대본·음성·문장 타이밍과 R06 Bullet 실행 6개를 읽기 전용으로 재사용한다. 새 물리 실행이나 회피 성능 향상 비교가 아니다. 교육용 A* + lookahead/heading 제어 모형이며 Nav2/DWB·실기·센서 실행이 아니다. 방향 정렬 가정은 설명용이며 solver 결과에 넣지 않는다. 공유 trace 및 source-time mapping은 유지한다.

STL 로봇은 키트에서 이미 angle smoothing을 적용한다. 메시의 상세 실루엣을 임의 subdivision으로 바꾸지 않고 이번에는 확인된 경로 재질 문제에 집중한다. 카메라·조명·충돌 형상은 R08 그대로다. 변경되지 않은 B01 프레임은 R08 산출물을 복사해 재사용하며 기록한다. B05와 최종 OFF/ON 비교는 새 렌더한다. B01의 목표 링은 R08 재질을 유지하고 B05 재생 컷에서 대비를 강화한다. 목표 링의 material key도 같은 조건을 재현하도록 명시한다. 나레이션을 재생성하지 않으므로 외부 TTS 전송이 없다.

## 키트·스킬 관찰

공유 키트와 topics 및 기존 revision은 수정하지 않는다. 로컬 후보는 문장 교체 후 live reference 갱신과 국소 페이드, 같은 pose의 경로 재질 비교다. 어두운 재질만으로 대비 개선을 단정하지 않고 실제 프레임으로 후보를 선택한다. 기존 FFmpeg finishing을 사용하며 Resolve 연결은 이번 환경에 없다.

## 결과

- 최종: `output/planner_physics_ko_v9.mp4` — 73.93초, 1920×1080, native30fps, H.264/AAC, 한국어 문장 자막17개.
- 비교: `output/comparison.html` — 같은 영상 시점의 R08/R09 재생 및 동일 solver 상태의 경로 재질 비교. 핵심 발췌 `output/critical_excerpt.mp4` — 33.27초, 960×54030, 음성 포함. 발췌본은 최종 상태로 새로 조립했다.
- `validate_visual_manifest.py --require-media`, `scripts/check_scene_style.py` (Manim/Blender 모두), staging6구간: PASS. `output/manifest_validation.txt`, `output/scene_style_validation.txt`, `output/sequence.json`.
- `validate_delivery.py --require-audio --fps 30 --audio-manifest assets/audio/manifest.json --caption-timing output/caption_timing.json --full-decode`: PASS. 발췌본도 명시적인 preview 최소 크기로 PASS. `output/delivery_validation.txt`, `output/critical_delivery_validation.txt`.
- 6개 V9 trace와 기존 물리 probe/실제 제어 입력/정렬 가정 명령 검증: PASS (`output/run_validation.txt`). 새 solver 실행·time-step convergence·실기 검증은 아니다.
- 698개 PNG의 1080p 크기/IEND와 최종 전체 decode: PASS. B01 frame1–278은 R08과 동일한 시작 화면을 재사용하고 B05 frame279–698은 새로 렌더했다. 최종 OFF/ON 비교는 새로 렌더했다. provenance와 입력/영상 해시는 `output/reuse_provenance.json`, `output/input_identity.json`, `output/delivery_identity.json`.
- render-reviewer 스킬 1회 실제 프레임 검토 + 라벨 겹침 수정의 국소 재검토: 최종 합본33시점/핵심 native 원본 확인에서 남은 blocker/high0개. C1/C2/C3 모두 **정의한 프레임 검사 범위에서 met** (`output/final_review.json`). 여기서 제작/정의한 화면 개선은 종료한다.
- 직접 정상 속도 움직임·청취는 도구 접근이 없어 `incomplete`, 실제 초심자 첫 이해는 `not_assessed`. 음성/타이밍은 R08과 byte-identical이지만 이 사실을 청취 PASS로 바꾸지 않는다. 기존 STL/목표 링의 각진 실루엣은 관찰이며 새 종료 조건으로 추가하지 않는다.

## 개선 효과와 재현

같은 물리 상태에서 초록/파랑 경로가 더 진하고 구분되며, 관계 설명 글자가 경로선과 겹치지 않는다. 바뀐 문장은 글자 형태를 변형하지 않고 사라짐→나타남으로 국소 교체되어 중간 프레임의 흩어진 획을 없앴다. 로봇/지도/드럼/선은 계속 유지된다. 이번은 시각 표현 비교로, 길이/대본/물리 성능을 개선했다는 실험이 아니다.

재현: `uv run manim --disable_caching -r 1920,1080 --fps 30 --media_dir pilots/05_moving_obstacle/revision_09/output/final_render pilots/05_moving_obstacle/revision_09/reasoning_scene.py ClosedLoopReasoning` → Windows Blender에서 `blender_scene.py` (`--start-frame N --end-frame M --batch`로60프레임 이하 구간) → `uv run python pilots/05_moving_obstacle/revision_09/assemble.py`. 전체 Blender 렌더도 같은 B01 목표 링 상태를 material key로 재현한다. 재현 조건 보완 후 frame628이 기존 최종 PNG와 pixel-identical임을 확인했다. 출력과 자격증명은 기존 gitignore 정책을 유지한다.

검토 중 방향 설명 글자와 경로·금지 영역 선이 겹치는 기존 관찰을 확인해 두 라벨만 빈 공간으로 옮겼다. 문장 교체를 로컬 change_sentence helper로 묶었다. 초기 static checker는 국소 FadeOut 개수를 전체 장면 reset 위험으로 WARN 처리했지만 실제 지오메트리는 계속 보이며 helper 정리 후 동일 규칙 PASS다. 규칙이나 공유 키트는 수정하지 않았다.

추가 재현 확인: R09 소스로 새로 생성한 B01 컷 진입 frame183도 재사용한 R08 PNG와 pixel-identical PASS. 공용 두 키트의 입력 해시도 최종 기록 시점과 동일하다.
