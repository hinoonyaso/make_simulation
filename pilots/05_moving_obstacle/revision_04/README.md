# 장애물 정보가 바뀌면, 같은 길은 어떻게 될까? — Revision 04

강화된 Director/Renderer/Reviewer 스킬을 실제 제작에 적용한 새 버전이다. 작업 범위는 이 폴더이며 기존 영상, `topics/`, 공유 키트는 수정하지 않는다. 업로드는 이번 요청 범위에 포함되지 않는다.

## 연출 결정

- 이전 버전은 3D 도입과 평면 설명이 분리되어 있었다. 이번 설명의 핵심은 지도와 경로를 동일 좌표에서 비교하는 것이므로 전체를 하나의 Manim 공간으로 구성했다. 3D 장면을 더 만드는 대안은 이번 핵심 추론에 필요한 깊이 정보를 추가하지 않아 선택하지 않았다. bRd3D의 재질·조명 품질까지 평가하는 실험은 아니다.
- 질문 → 로봇 크기/여유 → 2초 기준 경로 → 결과를 숨긴 예상 → 3초 지도 대입 → 겹침 발견 → 다음 저장 경로 → 실제 움직임 → 조건부 적용으로 구성했다.
- 이전 경로를 남겨두고 정보를 바꾸며, 실제 비용 배열과 경로 점으로 만든 확대창에서 겹침을 확인한다. 이미 기록된 결과를 연출하는 것이며 새 제어/계획 실험을 실행하지 않는다.
- 로봇 실제 위치는 비교가 끝난 뒤 재생한다. 파란 궤적은 해당 순간까지의 위치만 표시해 미래 경로처럼 보이지 않게 했다. 기준 경로와 실제 궤적은 색과 범례로 구분한다.
- TTS 측정 길이가 비트 길이다. 유일한 `visual_manifest.json`에서 핵심 구간의 beat IDs를 선택하며 별도 비트 정의를 만들지 않는다. B04–B06의 30.53초에는 예상부터 새 경로까지의 맥락이 필요해 권장 15–25초보다 길다.

## 데이터·주장 경계

`../data/trace.json`의 원형 장애물, 비용 지도, 저장 경로, 로봇 위치를 읽기 전용으로 사용한다. 출처는 `topics/08_nav2` 사용자 정의 교육용 통합 모형이다. **실제 ROS 2 / Nav2 / Nav2 DWB 실행이 아니다.** 원형 사람형 장애물을 동일 반지름 0.30m의 드럼으로 표현했다. 로봇 반지름 0.25m와 추가 여유 0.22m는 원본 모형의 계획 임계값이며 Nav2의 기본 설정이라고 설명하지 않는다.

`derive_evidence.py`와 `evidence.json`은 입력 SHA와 정점 판정을 기록한다. 2초 아래 경로는 2초 지도에서 금지 정점 0개, 3초 지도에서는 3개, 다음 3초 경로는 0개다. 이는 저장 경로의 **격자 정점** 검사이며 연속 충돌 안전성이나 전역 최적성의 증명이 아니다. 3초 계획은 `periodic_replan`이며 두 번째 `path_invalid` 이벤트라고 주장하지 않는다. 마지막 “겹치지 않는다면 후보가 될 수 있다”는 조건부 추론이며 추가로 관측한 시뮬레이션이 아니다.

도입에서 지도 변화를 먼저 보여준 뒤 2초 상태로 돌아가는 설명 순서는 실제 시간 순서의 재생이 아니다. 지도/장애물 상태 사이 전환은 시각적 보간이며 실제 중간 센서 갱신값이 아니다. 실행은 원본 3→17.2초 위치 순서를 유지해 설명 길이에 맞춰 보간한다. 초록선은 3초 기준 경로다.

## 핵심 구간 검토와 발견한 문제

전체 제작 전에 실제 핵심 클립을 생성하고 프레임 및 측정된 발화 시점을 검토했다. 셀/라벨 위치, 결과 공개 시점, 확대창의 근거를 검사했다. 수정 내용:

1. 짧은 발음 앵커 “세”가 “보세요”에도 매칭되어 결과를 일찍 드러낼 수 있었다. 정확한 토큰 일치로 바꿨으며 측정 시점 7.80초를 검증했다.
2. 숫자 패널 변형 중 글자가 뭉개졌다. 이전 지도 숫자는 갱신 때 숨기고 새 결과는 발화 시점에 표시한다.
3. 지도마다 표시 셀 수가 달라 `Transform`이 다른 위치의 셀끼리 대응했다. 표시할 좌표의 합집합과 고정 순서를 사용하고 투명도를 바꾼다. 셀 개수와 중심 좌표가 동일함을 확인했다.
4. 확대창과 새 경로 라벨이 동시에 남는 중간 프레임을 수정했다. 비교 확대창을 내린 뒤 새 경로 라벨을 표시한다.
5. “아까 통과한 길”은 전체 경로를 이미 주행했다는 근거 없는 인상을 준다. 생성된 음성에서 해당 문장을 제거하고 질문만 남겼다. `apply_opening_trim.py`와 `output/local_audio_edit.json`에 원본 음성 SHA·절단 범위를 기록했다. 변경된 오디오의 자막/정렬은 다시 생성했다.

공유 키트 이관 후보: 동일 격자 identity를 보장하는 비용 오버레이, 실제 셀/정점을 확대하는 설명 창, 알려진 발화의 정확한 토큰 앵커, 미래를 먼저 표시하지 않는 trace 궤적. 아직 한 파일럿에 적용한 로컬 구현이므로 범용성 검증 없이 키트에 옮기지 않는다.

## 음성 생성과 실행

사용자가 새 교육 대본/음성 설정의 Edge TTS 전송을 명시적으로 승인한 뒤 생성했다. 최초 제한 네트워크 실행은 음성을 생성하지 못해 중단했다. 이후 수정 문장의 재전송은 자동 승인 검토에서 거절되어 외부 재전송 없이 기존 로컬 음성을 편집했다.

현재 `B01_original.wav`는 최초 승인된 생성 결과이고, `B01.wav`는 그 4.0초 이후의 질문이다. 재현할 때 확보된 음성에 `apply_opening_trim.py`를 적용한다. 최종 manifest로 TTS를 일괄 재생성하면 이 로컬 편집의 원본 전제가 달라지므로 그대로 섞어 쓰지 않는다.

프로젝트 루트에서 확보된 음성을 사용:

```bash
uv run python pilots/05_moving_obstacle/revision_04/apply_opening_trim.py
uv run python core/narration/prepare_audio.py captions pilots/05_moving_obstacle/revision_04/visual_manifest.json
uv run manim --disable_caching -r 960,540 --fps 30 --media_dir pilots/05_moving_obstacle/revision_04/output/critical_render pilots/05_moving_obstacle/revision_04/discovery_scene.py CriticalInference
uv run python pilots/05_moving_obstacle/revision_04/assemble.py --critical
uv run manim --disable_caching -r 1920,1080 --fps 30 --media_dir pilots/05_moving_obstacle/revision_04/output/final_render pilots/05_moving_obstacle/revision_04/discovery_scene.py ObstacleDiscovery
uv run python pilots/05_moving_obstacle/revision_04/assemble.py
```

## 품질 판정의 한계

실제 프레임, 데이터, 측정 시간, 오디오 신호는 검사할 수 있었지만, 이 세션에는 연속 영상/음성을 직접 지각해 재생·청취하는 도구가 없다. 스틸과 디코드·ASR 결과를 청취로 부르지 않는다. 작성자가 소스를 이미 알고 있는 자기 검토이므로 독립 시청자/블라인드 이해도 검사가 아니다. 따라서 교육 품질 전체 승인은 **incomplete**이며, creator parity를 입증하지 않는다. 기술적 완료와 남은 리뷰를 구분해 제공한다.

## 결과와 검증 기록

- 최종 영상: `output/moving_obstacle_ko_v4.mp4`, **84.97초 / 1920×1080 / 30 fps / H.264 / AAC / 한국어 문장 자막 20개**.
- 핵심 프리뷰: `output/critical_excerpt.mp4`, 30.53초, 960×540. 최종 납품 파일과 구분한다.
- V9 trace, evidence 정점 검사, 동일 셀 identity/좌표 확인: PASS.
- `validate_visual_manifest.py --require-media`: PASS.
- `scripts/check_scene_style.py pilots/05_moving_obstacle`: 기존 Blender 및 Revision 03/04 Manim 모두 PASS.
- `stage_segments.py`: PASS, 8개 비트.
- `scripts/validate_delivery.py ... --require-audio --fps 30 --audio-manifest ... --caption-timing ... --full-decode`: PASS.
- 최종 인코딩 프레임 1·9·21·29.5·34·41.5·47.7·51·60·64·72·82초를 직접 검토했다. 검사 범위에서 남은 blocker/high 0개. 실제 연속 재생/청취를 했다는 뜻은 아니다.
- `silencedetect` -45dB / 최소 0.4초 기준 가장 긴 조용한 구간 1.554초, 3초 초과 0개. 신호 측정이며 전달력 판정이 아니다.
- Manim 출력은 프레임 양자화로 측정 길이보다 0.200초 짧았다. 조립에서 마지막 요약 프레임으로 그 차이만 보충해 나레이션 끝과 맞췄다.
- 최종 품질 보고서: `output/review_report.yaml`. 핵심 제작 전 리뷰: `output/critical_review.yaml`. 전체 교육 품질은 **incomplete** — 연속 재생·청취·시청자 이해도 평가가 남아 있다.

이번 강화 스킬은 전체 렌더 전에 정확한 앵커, 셀 대응, 숫자 전환과 라벨 겹침 결함을 찾는 데 사용됐다. 이는 관찰된 제작 개선이다. 자연스러운 음성이나 독립 시청자의 학습 효과까지 검증됐다는 결론으로 확대하지 않는다.
