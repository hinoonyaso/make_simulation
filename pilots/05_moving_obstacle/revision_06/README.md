# 계획한 길을 실제 바퀴 움직임으로 연결하기 — revision 06

## 결과와 범위

`output/planner_physics_ko_v6.mp4`는 한국어 나레이션·문장 자막을 포함한 72.20초, 1920×1080, 30fps 영상이다. 최종 파일 생성과 기술 검증은 완료했다. 최종 게이트 결과는 아래에 기록한다.

질문은 “새 경로를 고르면 실제 로봇도 장애물을 피하는가?”이다. 독립적으로 구현한 **교육용 A* + heading/lookahead 추종 제어기**가 Blender 5.2.1 LTS의 Bullet 강체 바퀴 모터를 실제로 구동한다. **Nav2/DWB 실행, 실제 로봇 실험, 움직이는 장애물 실험이 아니다.** 드럼은 처음부터 정적인 물리 장애물이며 2초에 이상화한 지도 정보만 추가된다. 센서·지각을 시뮬레이션하지 않는다. 영상의 Nav2 제한 설명과 README의 모형 범위는 같은 뜻이다.

## 결정 근거와 데이터 경계

revision 05는 설명용 지도 모형과 별도 개방 루프 접촉 실험을 연결했다. 사용자 요청에 따라 이번에는 계획·제어·물리 반응을 한 실행 안에 연결한다. 단순 운동학 적분 또는 미리 정한 위치 키프레임은 바퀴 명령과 접촉을 증명하지 못하므로 선택하지 않았다. 설치된 Blender의 강체·힌지·모터로 새 실험을 실행했다. 외부 엔진이나 의존성을 추가하지 않았다.

- `planner.py`: 독립 A*, 0.05m 격자, 반경 0.25m + 여유 0.22m + 드럼 0.30m. 금지 반경 0.77m. 현재 solver 위치에서 지도 갱신 후 재계획한다.
- `physics_closed_loop.py`: `../../06_physics_probe/physics_run.py`의 물리 빌더만 읽기 전용으로 사용한다. 모터의 기존 애니메이션을 제거하고 30Hz로 실제 이전 위치를 읽어 명령을 갱신한다. 물리 실행 중 로봇 위치 키프레임은 없다.
- `data/baseline_*`, `repeat_*`, `fine_*`: 각각 기본, 동일 반복, substeps 8→16 실행의 새 solver 기록. 기존 topic 데이터·영상·장면 코드를 사용하거나 수정하지 않았다.
- `reasoning_scene.py`, `blender_scene.py`: 같은 baseline 실행의 계획·실제 상태를 재생한다. 렌더용 키프레임은 이미 실행된 solver 기록의 재생 수단이며 물리 실행을 대신하지 않는다.
- `visual_manifest.json` 하나만 비트·대본·음성 측정 길이의 원본이다. `assemble.py`는 이것에서 컷을 만든다.

물리 조건은 중력 −9.81m/s², 차체 질량 1.6kg, 바퀴 반경 0.033m/트랙 0.288m, 차체 충돌 상자 0.26×0.22×0.06m, 이상화한 캐스터, 모터 impulse cap 0.002, solver 50회, 30fps×8 substeps이다. 세부 마찰·질량·접촉 설정은 trace `config`와 재사용 빌더에서 확인한다. 복도 벽은 runner에서 (0,±1.5,0.16), 크기 (5,0.1,0.32)m로 추가되어 안쪽 면 ±1.45m이다. 렌더 벽은 두께가 다르지만 안쪽 면을 맞췄다. 실사 메시에 대한 정밀 충돌·보정된 모터/타이어/센서·실기 검증은 아니다.

## 실행 근거

`output/run_review.json`에 수치·허용 기준을 기록했다.

| 조건 | 최종 목표 오차 | 결과 | 기본↔세밀 실행 끝 위치 차이 |
| --- | ---: | --- | ---: |
| 계획·제어 없음 | 1.667m | 드럼 접촉으로 진행 정체 | 0.0223m |
| 계획·제어 연결 | 0.1122m | 반경 0.15m 목표 범위에서 정지 | 0.0482m |

동일 반복 위치 배열은 오차 0m였다. substeps 16에서도 회피·목표 정지가 유지되고 목표 오차는 0.0643m였다. 이는 선언한 교육용 실험 기준 내 재현성과 민감도 확인이며 수렴 증명·하드웨어 성능 보장이 아니다.

ON의 root 중심 반경 0.23m 원형 proxy 최소 여유는 0.2312m, 방향을 반영한 실제 차체 상자와 드럼의 평면 여유는 0.3495m였다. OFF의 proxy 여유 −0.164m는 보수적 원의 겹침이며 실제 차체가 그만큼 관통했다는 뜻이 아니다. 차체 상자/드럼 최소 평면 여유는 약 −1.26μm이다. 이 지표는 접촉 힘/전체 메시 검증이 아니다. 계획 반경 0.25m를 쓰면 실제 추종 여유는 약 0.211m로 계획 여유 0.22m를 조금 밑돈다. 계획상 여유가 실제 궤적에 정확히 보장된다고 주장하지 않는다.

### 발견한 문제와 수정

첫 실행은 목표 진입 후 관성으로 약 0.323m까지 지나가고 다시 추종했다. `diagnostic_goal_overshoot_*`는 원래 진단 기록이다. 목표 가까이에서 감속하고 도착 상태를 latch하여 모터 0 명령을 유지하도록 고쳤다. 수정 후 모든 채택 실행을 다시 생성했다. 진단 파일은 채택 V9 검증 대상이 아니며 초기 메타데이터 누락도 남겨 구분한다.

초기 검사에서 모든 조건에 마지막 1초 순간 속도 <0.01m/s를 적용하면 OFF의 접촉 진동 0.01168m/s 때문에 실패했다. 목표 정지 ON에는 이 기준을 유지하고, 충돌 후 진행 정체 OFF에는 마지막 1초 순변위 <0.005m를 사용했다. OFF 순변위는 0.000624m이다. 접촉 조건을 완전 정지로 과장하지 않기 위한 기준 구분이며 불안정 신호를 숨기지 않는다.

최종 프레임 리뷰에서 B06의 파란 궤적이 짧게 잘린 것을 발견했다. 전체 애니메이션 렌더 종료 후 curve 데이터의 `bevel_factor_end` 애니메이션이 남아 정지 상태의 값을 덮었다. 비교 컷에서 object뿐 아니라 curve 데이터의 애니메이션도 제거하고 끝 계수를 1로 설정했다. `--final-only`로 비교 정지 화면만 재생성해 실제 전체 궤적을 확인했다. 원본 물리 실행과 B05 움직임은 바꾸지 않았다.

## 시간과 연출

B01은 질문 동안 시작 상태를 유지하고 실제 OFF 0→8초를 재생한다. B02–B04는 ON 지도 갱신 2초와 그 이후 실제 2→12초 피드백을 설명한다. B05는 **같은 실행 다시 보기**라고 표시하고 ON 2→30초를 14초에 재생한다. 접근·정지 문장에 맞춰 표시 속도를 바꿨으며 solver 시간은 바꾸지 않았다. 매 프레임 원본 인덱스는 `output/blender/source_mapping.json`에 있다. 초록은 참고 계획, 파랑은 실제 과거 궤적이다. B06은 동일 카메라에서 두 조건의 실제 30초 끝 상태를 순서대로 보여준다.

핵심 설명 B02–B04는 35.2초 유성 미리보기 `output/critical_excerpt.mp4`로 만들었다. 실제 프레임과 강제 정렬 문장 시점은 확인 가능하지만 도구에서 정상 속도 영상 시청·음성 청취가 불가능하다. 사용자는 해당 35초 유성 미리보기를 정상 속도로 확인한 뒤 나레이션과 설명 속도를 “자연스러움”으로 확인했다. 이는 발췌본의 속도·음성에 대한 사용자 확인이며, 도구 자체의 청취나 전체 영상의 정상 재생 검토를 대신하지 않는다. 전체 영상 교육적 최종 승인은 아직 `incomplete`이다.

Edge TTS SunHi +0%, 측정 음성 길이와 15개 문장 자막을 사용한다. FFmpeg loudnorm −16 LUFS/−1.5dBTP로 마무리한다. 자막은 영상에 굽고 외부 SRT를 제공한다. 내부 subtitle stream을 추가하면 플레이어에 따라 자막이 겹치는 이전 문제를 피한다. Resolve MCP가 현재 제공되지 않아 FFmpeg로 가역적인 부품/최종 출력을 만들고 기존 staging gate를 사용한다.

## 키트·스킬 개선 후보

공용 `studio_utils.py`, `manim_kit.py`는 수정하지 않았다. 파일럿 로컬 후보:

1. 바퀴 힌지·모터·이상화 캐스터의 물리 빌더 및 feedback runner. 단위·엔진·실행 설정을 같이 보존해야 한다.
2. 계획/실제 궤적, 휠 quaternion, solver→표시 시간 매핑을 공유하는 재생 helper.
3. 접촉 proxy/차체 거리와 목표 정지·반복·계산 간격 민감도를 분리하는 검증 helper.
4. comparison_trace 등 보조 데이터 참조를 manifest validator가 자동 검증하는 기능. 현재 수동으로 6개 V9를 모두 검증했다.
5. Windows 실행 trace는 LF로 저장하여 Git CRLF 공백 검사 혼동을 줄인다.
6. 정상 속도 영상·청취를 지원하는 reviewer 연결이 없으면 교육적 acceptance를 완료할 수 없다. 프레임 PASS를 완전 PASS로 승격하지 않는 현재 스킬 규칙을 유지한다.

## 재실행과 전달 검증

```bash
# Windows Blender에서 physics_closed_loop.py 실행: 기본, --name repeat,
# --name fine --substeps 16. 각 실행은 ON/OFF를 함께 저장한다.
uv run python pilots/05_moving_obstacle/revision_06/validate_run.py
uv run manim --disable_caching -r 1920,1080 --fps 30 --media_dir pilots/05_moving_obstacle/revision_06/output/final_render pilots/05_moving_obstacle/revision_06/reasoning_scene.py ClosedLoopReasoning
# Windows Blender에서 blender_scene.py 실행; --preview는 저비용 프레임 확인.
uv run python pilots/05_moving_obstacle/revision_06/assemble.py
```

기존 변경 커밋 `b51fb55`는 사용자의 대상별 승인 후 GitHub `origin/main`에 일반 push했다. revision 06은 별도 로컬 변경이며 위 승인에 섞어 push하지 않았다. 생성 영상·오디오는 Git 제외 대상이다.

## 최종 게이트 결과

- `validate_run.py`: 채택 6개 V9 schema PASS + 반복/세밀 계산/목표/여유 검사 PASS.
- `validate_visual_manifest.py --require-media`: PASS.
- `scripts/check_scene_style.py revision_06`: Manim/Blender 장면 모두 PASS.
- `stage_segments.py`: PASS, 6개 구간.
- `validate_delivery.py --require-audio --fps 30 --audio-manifest assets/audio/manifest.json --caption-timing output/caption_timing.json --full-decode`: PASS, 1920×1080, H.264/AAC, 72.20초, 문장 자막 15개, 전체 decode 통과. 실제 결과는 `output/delivery_validation.txt`.
- render-reviewer 기본 1회 + B06 결함의 제한된 수정 확인: 실제 합본 프레임 1/40.3/44.6/49/56.7/60/65/70초와 핵심 구간의 전·중·후 프레임을 확인. 발견된 B06 표시 결함을 수정한 최종 65초 프레임에서 전체 실제 궤적을 다시 확인. **검토 범위에서 남은 blocker/high 0개**.
- 프레임의 설명 관계와 물리 실행 근거는 PASS. 최종 정상 속도 재생·청취는 도구 접근 한계로 **incomplete**. 사용자 확인은 핵심 35.2초 발췌본의 음성/설명 속도에 한정한다. 완전한 교육적 최종 승인이나 다른 채널과의 동급 품질을 주장하지 않는다.

최종 영상: `output/planner_physics_ko_v6.mp4`. 외부 문장 자막: `output/final.ko.srt`. 검토 기록: `output/final_review.json`.
