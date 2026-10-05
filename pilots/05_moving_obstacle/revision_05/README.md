# 장애물 정보와 실제 움직임 — Manim + Blender 물리 연결판

## 제작 결정
사용자가 선호한 revision_04의 발견 중심 설명을 유지하고 실제 물리 실험을 앞뒤에 연결한다. 완성본의 계획 길이는 **136.73초**다. 기존 설명을 빠르게 줄여 넣는 대신 물리 입력·반응과 지도 확인의 관계를 먼저 보여준다.

- 도입: 같은 바퀴 명령만으로 드럼을 알아서 피할까? 로봇은 질문 동안 정지 화면에 있고 질문 뒤 기록된 물리 주행을 재생한다.
- Manim 비교: 동일 명령, 장애물 없음/있음의 두 물리 실행을 같은 시간축으로 나란히 재생한다. 전진 거리는 solver root 좌표에서 직접 계산한다.
- 연결: 이번 개방 루프 실험에는 경로 계획기가 없다. 충돌 이전에 지도에서 크기·여유를 확인해야 하는 이유로 넘어가며 **여기부터 별도의 교육용 지도 모형**이라고 말하고 화면에 표시한다.
- 기존 설명: 지도 변화 → 이전 경로와 금지 영역 겹침 → 새 저장 경로 → 해당 교육용 모형의 위치 기록. 기존 검증된 영상·음성을 보존한다.
- 결론: 계획과 물리 주행은 다른 단계이며 둘 다 확인해야 한다. 앞의 물리 실험을 다시 보여준다. 계획기의 물리 회피 성공을 입증하는 영상으로 주장하지 않는다.

기존 경로를 새 물리 로봇에 강제로 따라가게 만드는 대안은 사용자 요청의 물리 근거를 훼손하므로 선택하지 않았다. 새 피드백 제어기를 구현하는 대안은 새 실험·추종 검증이 필요한 별도 작업이다. 이번에는 실제로 확인한 단순 개방 루프 실험과 기존 계획 설명을 명확한 경계로 연결한다.

## 단일 계약과 파일
`visual_manifest.json`이 비트·대본·시간·자료의 단일 원본이다. `new_audio.json`은 생성 때 파생한 새 4비트 TTS 입력 부분집합이며 별도 연출 원본이 아니다. 이전 B01–B08 음성은 읽기 전용 참조한다. `build_timeline.py`가 새 음성과 기존 음성의 측정 시간·문장 자막을 하나로 합친다.

`physics_reasoning.py`와 `blender_physics.py`는 manifest의 같은 물리 trace 두 개를 소비한다. `assemble.py`는 비트 계약에서 영상 컷과 소스 시간 매핑을 만들며 자막을 화면에 표시하고 선택 가능한 SRT 파일도 제공한다.

## 데이터 경계와 물리 근거

| 영상 부분 | 원본 | 허용하는 설명 |
| --- | --- | --- |
| 새 Blender 및 물리 Manim | `../../06_physics_probe/data/baseline_clear.json`, `baseline_blocked.json` | 실제 Blender/Bullet 동적 바퀴 모터·접촉 실험의 기록 재생 |
| 기존 지도·경로·위치 설명 | `../data/trace.json`, `../revision_04/` | 사용자 정의 교육용 계획 모형의 저장 결과; Bullet 결과가 아님 |

두 부분은 **같은 센서/계획/물리 통합 실행이 아니다**. 두 렌더러가 물리 반응을 설명할 때는 같은 새 물리 실행을 소비하고, 기존 계획 데이터로 바뀔 때는 음성·화면에 경계를 표시한다. 실제 ROS 2/Nav2/DWB 실행 및 실제 로봇 실험이 아니다.

새 실험은 Blender 5.2.1 LTS, 30fps, frame당 8 substeps, solver 50회, 중력 −9.81m/s². 0.5초 안정화 후 양쪽 바퀴 각속도 목표 −6.060606rad/s. solver 전용 `../../06_physics_probe/physics_run.py`는 로봇 pose를 키프레임으로 입력하지 않았다. 렌더의 pose 키프레임은 저장 결과를 재생하는 단계이다. 단순 차체 상자·고정 저마찰 캐스터·자동 관성·설정된 마찰을 사용하며 실제 TurtleBot3 동역학으로 보정하지 않았다. 시각 메시와 충돌체는 정확히 같지 않다. 접촉 힘은 측정하지 않았다.

물리 파일럿의 repeat·substeps 16 검사에서 동일 조건 위치 차이 0m, 계산 간격 변경 끝 위치 차이 0.05348m/0.02452m. 진행/정지 구분은 유지되지만 옆방향 미끄러짐이 계산 간격에 민감하다. 정확한 하드웨어 접촉·안전거리 또는 시간 간격 수렴을 주장하지 않는다. 자세한 설정·검증 근거는 `../../06_physics_probe/README.md`와 `output/physics_review.json`에 있다.

기존 금지 반경 0.77m는 원본 계획 모형의 0.30+0.25+0.22m다. 새 물리 충돌체나 Nav2 기본값과 같지 않다. 격자 정점의 금지 검사이지 연속 충돌 안전성 증명이 아니다.

## 시간과 화면
- P01: 질문 동안 첫 solver 상태를 4.1초 유지한 뒤 8초 물리 기록을 나머지 발화 시간에 압축 재생한다. 카메라/시간 편집은 렌더 단계이고 물리 결과를 바꾸지 않는다.
- P02: source 0→8초를 같은 시간축으로 재생한 뒤 결과를 비교할 시간을 둔다.
- P03: 마지막 물리 상태를 유지하고 표현을 크게 만든다. 지도 확인은 개념적 연결이며 새 물리 상태가 아니다.
- P04: 장애물 없는 0→8초, 드럼 있는 0→8초를 순서대로 재생한다. 사건을 하나의 연속 실행인 듯 이어 붙이지 않는다.
- 기존 B01–B08: 원래의 설명용 시간 보간을 그대로 유지한다. 원본 모형의 2초/3초 지도 비교와 실행 기록 순서는 revision_04 README에 있다.
- 렌더는 native 30fps, 1080p, 스튜디오 EEVEE/AgX. 최종 물리 장면은 64 samples와 드럼 측면 smooth shading으로 파일럿의 노이즈·면 분할을 줄인다. 공용 키트는 수정하지 않는다.

## 발견한 제작 문제와 로컬 후보
1. ASS 자막 크기는 영상 픽셀 크기가 아니다. 기본 PlayRes에 큰 숫자를 넣으면 프리뷰 자막이 커지고 설명 문구와 겹친다. 실제 인코딩 프레임에서 발견해 크기·하단 공간을 조정했다.
2. 음성의 “멈춥니다”보다 물리 정지 재생이 늦으면 인과 설명이 어긋난다. P02는 source 8초를 발화 초기 8초에 재생하고 마지막 비교 문장에는 끝 결과를 유지한다.
3. 계획 데이터와 물리 trace는 좌표·충돌체·실행이 다르다. 이관 후보는 source-time handoff 계약, 같은 solver root의 전진 거리 비교, measured wheel quaternion replay, 자막 안전 영역이다.
4. `new_audio.json`에 TTS를 재실행하면 측정 길이와 자막 정렬을 다시 생성하고 타임라인을 재구성해야 한다. 원본 B01의 로컬 음성 편집 전제를 바꾸지 않는다.

새 한국어 교육 문장 4개와 SunHi 설정만 Edge TTS에 보내 생성했다. 이전 문장은 로컬 재사용이며 대본 외 다른 프로젝트 내용은 전송하지 않았다. 새 발화의 정렬은 Whisper known-text alignment로 측정한다. 정렬은 청취/발음 품질의 증거를 대신하지 않는다.

## 실행
저장소 루트에서 `uv run`을 사용한다.

```bash
uv run python pilots/05_moving_obstacle/revision_05/build_timeline.py
uv run manim --disable_caching -r 960,540 --fps 30 --media_dir pilots/05_moving_obstacle/revision_05/output/critical_render pilots/05_moving_obstacle/revision_05/physics_reasoning.py PhysicalReasoning
uv run python pilots/05_moving_obstacle/revision_05/assemble.py --critical
uv run manim --disable_caching -r 1920,1080 --fps 30 --media_dir pilots/05_moving_obstacle/revision_05/output/final_render pilots/05_moving_obstacle/revision_05/physics_reasoning.py PhysicalReasoning
```

Windows Blender에는 `blender_physics.py`를 전달하며 `-- --preview`는 대표 프레임만 렌더한다. 전체 PNG를 `bash pilots/05_moving_obstacle/revision_05/encode_physics.sh`로 30fps 인코딩한 뒤 `uv run python pilots/05_moving_obstacle/revision_05/assemble.py`로 조립한다. 이전 원본과 `topics/`, 스킬·키트는 이번 작업에서 수정하지 않는다.

`output/controlled_input_review.json`에서 두 물리 실행의 설정·엔진 설정·모터 입력 배열이 동일함을 확인했다. 새 드럼의 추가가 비교 조건이다. manifest 기본 검증기는 추가 `comparison_trace` 필드를 자동 검사하지 않아 두 trace를 별도로 `validate_trace.py`로 검증했다. 다중 trace 비교를 지원하는 계약/검증은 이후 키트 후보이며 이번에는 공유 스키마를 변경하지 않는다.

핵심 프리뷰는 35.43초, 960×540로 별도 표시한다. 수정 후 스타일·음성 존재·30fps·측정 길이·자막 범위·전체 디코딩 PASS. 검토 프레임의 자막 겹침·정지 발화 시점·지도 모형 경계 공개 시점을 수정했다. 정상 속도 재생과 청취는 이 세션에서 직접 수행할 도구가 없어 미완료이며 사용자 프리뷰 피드백을 요청했다. 그 검사를 완료한 것으로 간주하지 않고 본편 렌더는 잠정 리뷰 상태로 진행한다.

음성 신호 검사: −45dB, 최소 0.4초 무음 검출 기준 가장 긴 무음 1.55379초, 3초 초과 0개. 이는 신호의 간격 검사이며 TTS 자연스러움·발음의 청취 평가가 아니다.

후반 조립은 이전 revision_04와 같은 FFmpeg 경로를 사용한다. 현재 세션에는 연결된 DaVinci Resolve MCP가 노출되지 않아 Resolve 타임라인을 직접 생성하거나 검증했다고 주장하지 않는다. 단일 manifest를 `stage_segments.py`로 검증 가능한 편집 시퀀스로 내보내고, 컷·음성·자막·납품 검사는 로컬 조립에서 수행한다.

## 최종 결과와 검증

- 최종 영상: `output/moving_obstacle_physics_ko_v5.mp4`, **136.73초 / 1920×1080 / 30fps / H.264 / AAC / 한국어 문장 자막 31개**.
- `validate_visual_manifest.py --require-media`: PASS.
- `check_scene_style.py revision_05 revision_04/discovery_scene.py`: 새 Manim/Blender와 재사용한 Manim 모두 PASS.
- `stage_segments.py`: PASS, 12개 구간. 편집 시퀀스는 `output/sequence.json`.
- `validate_delivery.py --require-audio --fps 30 --audio-manifest assets/audio/manifest.json --caption-timing output/caption_timing.json --full-decode`: PASS.
- 인코딩된 최종 프레임 21개를 실제로 검사했고 해당 범위 blocker/high 0개. 정상 속도 재생·청취는 미완료이며 전체 교육 리뷰는 `output/review_report.yaml`에 incomplete로 기록했다.
- 문장 자막은 영상에 표시하고 SRT도 별도 제공한다. MP4 선택 자막을 default off로 remux해도 실제 검사에서 default=1이 유지되어, 자동 두 겹 표시를 피하도록 내부 자막 트랙만 제거했다. 영상·음성은 복사해 품질과 시간을 보존했다.
- 최종 시점에 읽기 전용 원본과 공유 키트의 SHA 일치를 확인했다. 이전 영상·topics·공유 키트는 수정하지 않았다.
