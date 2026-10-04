# Pilot 01 — TEB band reference shots

목표: 이 번들로 **bRd 3D 수준의 3D 메커니즘 샷**과 **3Blue1Brown 수준의 연속 변형 샷**을 실제로 만들 수 있는지 확인하고, 이후 에피소드가 따라갈 기준(reference)을 만든다. 현재 판은 한국어 TTS 나레이션과 문장 단위 자막을 넣은 약 71초 영상이다(BGM 없음). 사용자 검토 후 이 방식을 번들 기준으로 채택했다(2026-10-04).

## 구성

| 비트 | 샷 | 도구 | 내용 | 데이터 |
|---|---|---|---|---|
| B01 | S1 | Blender | hero 자세의 TurtleBot3, 초기 밴드가 드럼을 관통, 탑뷰로 크레인 | `data/band_trace.json` 스냅샷 0 |
| B02–B06 | S2 | Manim | 금지 영역 → 밴드 최적화(J 759→1.22) → ΔT 시간표 → 첫 구간만 실행 → 줌아웃 | `data/band_trace.json` |
| B07 | S3 | Blender | `teb_obstacle` 실제 주행, 0.2초마다 예측 밴드 갱신, 실행 궤적 누적 | `data/drive_trace.json` |

S1 마지막 프레임과 S2 첫 프레임은 같은 월드 창(폭 5.6m, 중심 원점)을 쓴다. 두 프레임을 겹쳐 정렬을 확인한 뒤 0.6초 디졸브로 잇는다. S2→S3는 "한 번의 결정 해부"에서 "반복되는 결정"으로 넘어가는 의미 전환이라 컷으로 처리한다.

## 타이밍

`core/narration/prepare_audio.py tts visual_manifest.json`이 실제 음성 길이를 `sec`에 기록한다(`min_sec`보다 짧으면 무음 패딩). Blender는 `sec × 30`프레임으로 렌더하고, Manim은 `BeatClock`으로 비트마다 정확히 `sec`를 쓴다. 따라서 영상 길이 = 나레이션 길이이며, `validate_delivery.py`가 ±0.12초로 검사한다. 자막은 Whisper 단어 시각으로 문장 경계를 나눈다.

## 데이터와 정직성

- 출처: `topics/09_dwb_teb/model.py`의 TEB형 교육용 모형. 실제 ROS 2 TEB 실행이 아니다.
- `extract_trace.py`가 09편 `output/trace.json`을 **읽기만** 해서 V9 trace 두 개로 변환하고 `validate_trace.py`로 검증한다. 30Hz 보간은 모델과 같은 constant-twist 적분식을 쓴다. 마지막 샘플이 모델의 `next_pose`와 1e-9 이내로 일치하는지 assert한다.
- **hero 자세 (-1.25, 0, 0)는 별도의 가정 계산이다.** 실제 주행에서 로봇이 x=-1.25를 지날 때 위치는 y≈0.30이다. 그래서 S1/S2(hero)와 S3(실제 주행)를 하나의 연속 장면처럼 잇지 않고 컷으로 분리했다.
- S2의 최적화 스냅샷은 실제 값이다. 스냅샷 사이 프레임은 시각적 보간이다(자세는 선형, 비용은 로그 공간).
- 금지 영역 반지름 0.72m = 드럼 0.30 + 로봇 0.22 + 모델의 장애물 비용 임계 0.20. 밴드 점 색은 이 기준의 실제 여유 거리로 정한다. 수렴한 밴드의 오른쪽 일부가 경계에 살짝 걸치는데, 페널티 방식이라 장애물 비용 0.001이 남기 때문이다(09편 README의 한계와 같다). 숨기지 않았다.
- S2-B05의 0.2초 실행은 슬로모션이다.
- **로봇 형상:** TurtleBot3 Waffle Pi 실제 메시(`assets/turtlebot3`, Apache-2.0)를 URDF 배치대로 불러온다. 모델의 원형 footprint 반지름 0.22m는 Nav2 bringup 기본값 `robot_radius: 0.22`(main 브랜치, 2026-10-04 확인)와 같다. Waffle Pi의 외접 반지름은 약 0.24m라 근사다. 바퀴 회전은 모델의 가상 바퀴(r=0.10m, 간격 0.42m)가 아니라 **보이는 TB3 형상**(r=0.033m, 간격 0.288m)으로 같은 (v, ω)에서 다시 적분했다. 미끄러짐 없이 구르는 것처럼 보이게 하기 위해서다.

## 결정과 근거

- **밝은 콘크리트 스튜디오(Blender) + 어두운 도식(Manim):** bRd 3D(CPU·전기차 모터 편 프레임 분석)는 실물 3D를 밝은 바닥 위에서, 추상 개념을 단색 배경 도식으로 보여준다. 로봇에서는 물리적 대상은 Blender, 계산 과정은 Manim으로 역할을 나눴다.
- **EEVEE + AgX Punchy, 발광 세기 낮게:** 처음 렌더에서는 발광이 강하고 조명이 밝아서 바닥과 밴드가 하얗게 바랬다. AgX는 밝은 발광의 채도를 낮추기 때문에, 밴드 발광을 1.6으로 낮추고 바닥 반사율을 0.30~0.37로 내렸다.
- **카메라를 매 프레임 직접 계산:** Track-To 제약은 정확한 탑뷰에서 up 벡터가 퇴화한다. 그래서 up 벡터를 Z에서 Y로 섞는 look-at을 매 프레임 키프레임으로 넣었다. 크레인은 거리를 먼저 늘린 뒤 방향을 바꿔서, 드럼 위를 가까이 지나가며 생기는 광각 왜곡을 없앴다(1차 미리보기에서 확인된 결함).
- **S3 카메라를 +y 쪽에 배치:** 로봇이 드럼의 +y 쪽으로 지나가므로, 반대편에 카메라를 두면 드럼이 로봇을 가린다.
- **키트로 승격(9.2):** 스튜디오 환경, 소품, TB3 로더, 바퀴 계산, 밴드, 궤적 공개, 탑뷰/크레인 카메라는 `core/.../templates/studio_utils.py`로 옮겼다. Manim의 `world_window`, `turtlebot3_top`, `BeatClock`, `beat_seconds`는 `manim_kit.py`로 옮겼다. 이 파일럿 스크립트는 이제 키트만 import해서 장면을 조립한다.

## 발견한 번들 결함

- `animation_utils.set_linear_interpolation`이 Blender 5의 layered action에서 `Action.fcurves`가 없어 실패했다. `fcurves()` 헬퍼를 추가해 수정했고, Blender 5.2.1에서 검증했다.
- 커브 `bevel_factor_mapping_end = "SEGMENTS"`는 점 인덱스에 비례하지 않는다. 1차 최종본에서 실행 궤적이 로봇보다 최대 0.31m 뒤처졌다(250프레임, `.blend`를 열어 측정). `SPLINE` 매핑에 매 프레임 누적 길이 비율을 키프레임하도록 바꿔서 오차를 4mm 이하로 줄였다. 궤적 공개 헬퍼로 키트에 승격할 후보다.
- 리뷰 중 S2 14초 지점의 비용 바가 대부분 노란색(운동학)이라 보간 왜곡을 의심했다. 확인해 보니 실제 스냅샷 1의 값이었다(운동학 613.71, 장애물 99.78). 첫 스텝에서 장애물 비용을 운동학 위반과 맞바꾼 것이다. 나레이션에서 설명할 만한 장면이다.
- V9 매니페스트는 "비트 하나 = 미디어 하나"를 가정했다. 이 파일럿에서는 S2 한 파일이 비트 다섯 개를 담는다. 그래서 `media_in`/`media_out`를 추가했고, 범위가 겹치면 `stage_segments.py`가 FAIL을 낸다(9.2).
- 비트 하나의 자막이 두 문장 11초라 읽기 어려웠다. 그래서 문장 단위로 자막을 나누도록 했다. 09편 출력은 바이트 단위로 그대로다(9.2).

## 재현

```bash
cd /home/sang/make_simulation
uv run python pilots/01_teb_reference/extract_trace.py
uv run python core/narration/prepare_audio.py tts pilots/01_teb_reference/visual_manifest.json      # writes measured sec
uv run python core/narration/prepare_audio.py captions pilots/01_teb_reference/visual_manifest.json
pilots/01_teb_reference/render.sh S1 PREVIEW stills 1 110 240      # 빠른 스틸 확인
uv run manim -ql --fps 15 --media_dir pilots/01_teb_reference/output/manim pilots/01_teb_reference/manim_shot.py BandDissection
pilots/01_teb_reference/render.sh S1 FINAL anim
pilots/01_teb_reference/render.sh S3 FINAL anim
uv run manim -qh --fps 30 --media_dir pilots/01_teb_reference/output/manim pilots/01_teb_reference/manim_shot.py BandDissection
uv run python pilots/01_teb_reference/assemble.py
```

Blender 5.2.1 (Windows, WSL에서 `render.sh`로 실행), Manim CE 0.21.0, RTX 4060 Laptop. EEVEE 1080p/64샘플 기준 약 1.5초/프레임.
