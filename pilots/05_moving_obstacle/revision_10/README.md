# R10 — 발견 연결과 표면 표현의 렌더 실험

## 렌더 전 목표

- D1: 금지 영역 때문에 새 참고 경로가 필요하다는 발견이, 길만으로 몸이 움직이지 않으므로 제어 입력이 필요하다는 다음 질문으로 이어진다. 목표점/현재 방향/보정 관계를 계속 보이고 기록된 실제 응답으로 돌아간다. B03→B04→B05의 연결을 새 음성 포함 발췌본에서 검사한다.
- S1: R09 동일 solver pose/카메라/조명에서 analytic 드럼과 목표 링의 원형 실루엣/측면 highlight의 각짐을 줄이고 실제 반경/높이와 여유를 유지한다. faithful robot STL은 그대로 유지한다. 같은 상태의 candidate를 먼저 비교한다.
- R1: 1080p30, 한국어 문장 자막, 입력·명령·응답/가정 구분, 컷 진입·사건·퇴장의 로봇/여유/목표/글자 겹침 회귀 없음. 음성이 바뀐 문장은 재측정/재정렬한다.

## 데이터 경계와 결정

기존 R06 Bullet 실행6개를 읽기 전용 재사용한다. 새 solver 성능 실험이 아니라 대본 연결/렌더 표현의 실험이다. 교육용 A*와 lookahead/heading 제어이며 Nav2/DWB/실기/센서 실행이 아니다. 동일한 원형 드럼의 렌더 표면 tessellation만 로컬에서 높인다. 충돌 형상과 solver 결과는 변경하지 않는다. 로봇 STL의 각진 실루엣을 임의 subdivision으로 바꾸지 않는다. 공유 키트와 topics 및 이전 revision은 수정하지 않는다.

## 비교 분석 범위

두 채널에서 구체적인 영상·확인한 구간·접근 방식을 기록한다. 원본 프레임/전개를 확인하지 못하면 그 항목은 미확인으로 둔다. 1분대 실험과 긴 강의를 영상 전체 길이만으로 동일 평가하지 않고 대응하는 설명 구간을 비교한다. 정상 속도 시청·청취/초심자 첫 이해와 informed frame review는 구분한다.

## 제작 상태

최종 렌더·기술 검증·정의한 프레임 목표 검토 완료. 정상 속도 시청·청취 및 초심자 이해는 미확인이다.

Surface 후보는 타이밍 변경 전 R09와 동일한 frame465/628(source/camera는 `surface_candidate_mapping.json`)에서 비교했다. 드럼 가장자리와 목표 링의 polygon facet이 줄어 후보를 선택했다. 바뀐 B03/B05만 TTS 재생성, 총74.93초/17문장으로 재측정·정렬했다. B05 목표 컷과 실험 시간 매핑은 새 세 번째 문장 시작 10.37초에 맞추며 solver 샘플 순서/최종값은 그대로다.

## 키트·스킬 및 환경에서 확인한 문제

- 키트의 원형 드럼/링 분할 수는 근접 컷에서 각진 외곽/반사를 만든다. 로컬 `add_faithful_drum`과 목표 링 생성의 분할 수를 높여 같은 상태의 native 프레임에서 개선을 확인했다. 키트 이관 후보는 크기를 보존하는 렌더 품질별 원형 소품 분할 수/평면 cap 보존 옵션이다. 공유 키트를 직접 변경하지 않았다.
- B05 음성이 길어지면 기존 고정 9.1초의 목표 카메라 전환은 문장과 어긋난다. 측정한 세 번째 문장 시작에서 카메라/소스 시간 구간을 전환하는 로컬 구현을 적용했다. 이관 후보는 narration cue 기반 event anchor이며 solver 시간과 편집 시간은 계속 분리해야 한다.
- Resolve MCP는 이번 세션에 있지만 read-only `project_manager.snapshot`이 `SCRIPTING_UNAVAILABLE`을 반환했다. 실행 중인 Resolve가 API에 응답하지 않고 bridge는 비활성 상태였다. 에디션/버전과 프로젝트/타임라인은 확인하지 못했다. Resolve 설정/기존 프로젝트를 변경하지 않고 기존 FFmpeg 조립기로 마무리한다. Resolve 사용 성공으로 기록하지 않는다.
- Windows Blender의 긴 일괄 렌더는 이전 작업에서 종료된 이력이 있어 60프레임 이하로 분할한다. 그 종료의 원인은 미확인이다. 각 배치 종료 상태와 PNG 크기/완전성, 최종 전체 디코딩을 검사한다.
- 스킬이 요구하는 정상 속도 시청·청취 및 실제 초심자 첫 답변은 이번 도구로 수행하지 못했다. 프레임 검사·타이밍 정렬이 그 검사를 대신하지 않는다. 이전 버전의 사용자 속도 승인을 새 음성의 승인으로 확대하지 않는다.

## 산출물과 비교 자료

- 최종 영상: `output/planner_physics_ko_v10.mp4`
- 47.47초 발췌본: `output/critical_excerpt.mp4` — B03/B04/B05 연결 전체를 담아 일반적인 짧은 발췌보다 길다.
- 비교 분석: [COMPARISON.md](COMPARISON.md)
- 로컬 재생/표면/참고 샘플 비교: `output/comparison.html`
- 같은 상태 표면 비교: `output/surface_comparison.jpg`
- 읽기 전용 입력/공유 키트 해시: `output/input_identity.json`

공개 참고 영상의 실제 storyboard 프레임으로 개념 전개/프레이밍을 비교했다. 원본 영상의 연속 재생·청취와 고해상도 표면 검증은 하지 못했다. 비교 자료는 로컬 Git 제외 output에 두며 유튜브 업로드는 이번 요청 범위에 없다.

## 최종 검증 결과

- `validate_visual_manifest.py visual_manifest.json --require-media`: **PASS**.
- `scripts/check_scene_style.py reasoning_scene.py blender_scene.py`: **두 파일 PASS**.
- `stage_segments.py visual_manifest.json output/sequence.json`: **6 segments PASS**.
- `scripts/validate_delivery.py output/planner_physics_ko_v10.mp4 --require-audio --fps 30 --audio-manifest assets/audio/manifest.json --caption-timing output/caption_timing.json --full-decode`: **PASS** — 1920×1080,30fps,74.93초,17문장,음성1stream,전체디코딩.
- `validate_evidence.py`: 기존6trace와 제어 규칙·repeat/fine probe 기준 **PASS** (`output/run_validation.txt`, `output/run_review.json`). 새 solver 실행/시간 간격 수렴/실기 검증은 아니다.
- 722개 PNG와 최종 비교2개: native1080p/완전성 PASS. B05 소스 샘플 순서와 최종30초 상태 PASS. 입력/공유 키트 해시 유지 PASS (`output/native_frame_validation.json`).
- render-reviewer 적용1회 이상: 실제 발췌14시점, native 표면 비교, 최종 합본38시점/핵심 native 원본을 확인했다. **검사한 프레임 범위의 blocker/high0개**. D1/S1/R1의 정의한 기술·프레임 목표 met (`output/critical_review.json`, `output/final_review.json`).
- 정상 속도 움직임/TTS 자연스러움은 incomplete, 실제 초심자 첫 이해는 not_assessed. 전체 교육 검토 PASS나 두 채널 동급으로 표기하지 않는다.

## 실험 결과

R09 대비 새 길→제어→실제 응답 연결을 대본과 지속 화면으로 명시하고, 동일 상태의 드럼/목표 링 각짐을 줄였다. 길이는1초 증가해74.93초이며 설명 중간을 줄이지 않았다. 로봇 STL·충돌·물리 성능은 그대로다. 정의한 화면 목표와 기술 게이트를 충족해 이번 국소 실험은 여기서 종료한다. 비교 분석에서 제안한 부품 작용/새 조건 실행은 다음 제작 후보이며 이번 완료 기준에 새로 추가하지 않는다.

재현 경로: 측정 음성/문장 정렬→발췌 Manim540p30 및 Blender `--critical`→`assemble.py --critical`→실제 프레임 검토→Manim1080p30 및 Blender 전체60프레임 이하 배치→PNG검사→`assemble.py`→위 게이트/합본 프레임 검토. Windows Blender는 WSL UNC경로로 실행했다. batch stdout은 `output/native_*.log`, 렌더/합본 식별은 `output/delivery_identity.json`에 있다.
