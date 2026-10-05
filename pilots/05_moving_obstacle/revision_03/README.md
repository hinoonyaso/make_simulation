# 움직이는 장애물 — Revision 03

결과: `output/moving_obstacle_ko_v3.mp4` (98.67초, 1920×1080, 30 fps, 한국어 나레이션, 문장 자막 20개). 원본 공개 영상의 업로드 기록은 변경하지 않는다.

## 연출 결정과 근거

짧은 결과 나열에서 하나의 질문을 따라가는 설명으로 재제작했다. 기존 스튜디오 3D 장면을 도입에 사용하고, 같은 장애물·로봇·목표를 유지하는 Manim 평면 지도에서 계산 근거를 보여준다. 전체를 Blender로 다시 만드는 대안도 고려했지만, 이번 핵심은 정확한 격자점과 이전 경로의 비교이므로 평면 표현을 선택했다. 3D→2D 전환은 컷이며 공간을 연속 변환했다고 주장하지 않는다.

1. 드럼 반지름 0.30m + 로봇 반지름 0.25m + 모형의 여유 0.22m = 금지 반경 0.77m를 기하와 함께 보여준다.
2. 같은 2초 지도에서 원래 경로의 금지 점 9개와 첫 우회 경로의 0개를 비교한다.
3. 이전 우회 경로를 남겨두고 3초 지도로 바꾸면 금지 점 3개가 생기는 것을 보여준다.
4. 다음 저장 경로의 금지 점은 0개다. 비교가 끝난 뒤 실제 로봇 위치 기록을 재생한다.

타이밍은 새 TTS의 측정 길이에 맞췄다. 설명을 따라갈 시간을 확보해 약 99초가 되었다. 같은 질문·지도·경로를 유지하고 결과를 설명하는 과정이 이번 개선이다. 특정 채널과 동급이라는 평가는 이 검증으로 입증되지 않는다.

## 데이터 경계

`../data/trace.json`의 V9 데이터를 읽기 전용으로 사용한다. 원본은 `topics/08_nav2`의 사용자 정의 교육용 통합 모형이다. **실제 ROS 2 / Nav2 / Nav2 DWB 실행 결과가 아니다.** 영상 끝과 나레이션에도 이를 명시했다. 원본의 원형 사람형 장애물을 동일 반지름의 드럼으로 시각화한다.

`derive_evidence.py`가 저장 경로의 격자 좌표를 해당 스냅샷의 실제 비용 배열에 대입하여 `cost >= 255`인 점을 센다. 결과와 입력 SHA는 `evidence.json`에 기록한다. 9/0/3/0은 경로 정점 수이며 연속 경로의 충돌 검사나 후보 전체의 최적성 증명이 아니다. 3초 계획의 이유는 `periodic_replan`이다. 이를 두 번째 `path_invalid` 이벤트라고 해석하지 않는다. 여유 0.22m는 원본 `model.py`의 계획 금지 임계값이며 Nav2 기본값이 아니다.

2→3초 장애물/지도 전환과 로봇 위치 보간은 표현을 위한 것이다. 시간은 설명 길이에 맞춰 늘린다. 실행 구간은 3초부터 마지막 17.2초까지 원본 위치 순서를 유지하며, 표시한 초록 경로는 3초에 저장된 기준 경로다. 추가 계획이나 후보 점수를 생성하지 않았다.

## 실행

프로젝트 루트에서:

```bash
uv run python pilots/05_moving_obstacle/revision_03/derive_evidence.py
uv run manim --disable_caching -r 1920,1080 --fps 30 --media_dir pilots/05_moving_obstacle/revision_03/output/final_render pilots/05_moving_obstacle/revision_03/reasoning_scene.py MovingObstacleReasoning
uv run python pilots/05_moving_obstacle/revision_03/assemble.py
```

나레이션·강제 정렬 결과는 `assets/audio/`와 `output/caption_timing.json`에 있으며, 준비 절차는 루트 `ROUTING.md`를 따른다. `visual_manifest.json`이 8개 비트의 계약이다.

## 발견한 문제와 로컬 개선

공유 `studio_utils.py`와 `manim_kit.py`는 수정하지 않았다. 키트 이관 후보: 실제 비용 배열의 격자점별 오버레이, 저장 경로의 금지 점 표시, 패널 폭 제한과 trace 기반 위치 재생. 기존 Blender 오버레이는 네 모서리 최대값으로 셀을 색칠했으므로 이번 정확한 정점 비교에는 새 로컬 오버레이를 사용했다.

프레임 검토에서 목표 라벨과 수식 간격, 경로 위 라벨, 일부 패널 배치, 궤적 내부 채움 문제를 발견하고 수정했다. `VMobject` 경로는 `fill_opacity=0`을 명시하고, 흐리게 만들 때 `set_opacity()` 대신 `set_stroke(opacity=...)`를 사용한다. 전자는 채움도 다시 켜기 때문이다. 도움 함수 변경이 캐시된 애니메이션에 충분히 반영되지 않을 가능성을 제거하기 위해 최종 렌더에 `--disable_caching`을 사용한다. 다른 H.264 입력은 각각 디코딩한 후 동일 설정으로 재인코딩하여 조립한다. 인코딩 문제만이 이전 화면 차이의 원인이었다고 단정하지 않는다.

음성의 감정·자연스러움은 실제 청취 평가가 필요하다. 프레임·자막 시간·신호 검사는 청취 평가를 대신하지 않는다. 두 채널 수준의 연출 완성도를 자동 게이트만으로 판정할 수 없다.

## 최종 검증

- V9 `validate_trace.py`: PASS.
- 재계산 `derive_evidence.py`: PASS (9 / 0 / 3 / 0, `periodic_replan`).
- `validate_visual_manifest.py --require-media`: PASS.
- `scripts/check_scene_style.py pilots/05_moving_obstacle`: Blender·Manim 모두 PASS.
- `stage_segments.py`: PASS, 8개 비트.
- `scripts/validate_delivery.py ... --require-audio --fps 30 --audio-manifest assets/audio/manifest.json --caption-timing output/caption_timing.json --full-decode`: PASS, H.264 1920×1080 / AAC / 30 fps / 98.67초 / 자막 20개 / 전체 디코드.
- 최종 인코딩 프레임 5·18·29·38·52·65·83·94초를 직접 검토했다. 검사한 프레임·타이밍·데이터 비교에서 blocker/high 0개. 보고서: `output/review_report.yaml`. 독립 리뷰 에이전트나 연속 청취 검증으로 해석하지 않는다.
