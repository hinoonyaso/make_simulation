# Bearing 6204 Visual Excellence R6 — QA 기록

## 범위와 기준

- 기준 커밋: `97d05464b345f492ba5ea969dbcffabcf69983b3`
- R5 비교 기준: `d67ac691e3e1988699cf55ddd0715f1a8e7e1990`
- R6 기준 브랜치 시작점: `9c8987dede01dd5cabd2d89edce67d0bdf7ee233`
- 수업: `examples/education/bearing.json` — “볼 베어링은 어떻게 마찰을 줄일까?”
- R6 scene source SHA-256: `4b41565e20e2c39ad0a75730269dfffd1443b2d231ae186de05b377af832fec8`
- R6 Preview SHA-256: `c44219f83365482ef12e0223994b59c0022ff849a83e8c59655d9480109bd457`

모든 영상은 로컬·무음 Preview다. 사용자 대상 내레이션, 1080p 최종 영상, 전체 속도 사람 검수는 이 QA 범위에서 실행하지 않았다.

## 발견 사항과 수정

1. R5 장면은 높이 2.0인 중앙 축 참조 형상이 볼을 가렸고, 설명 라벨이 여러 장면에 계속 남았다. R6은 축 높이를 0.72로 낮추고 프레임을 재구성해 볼 궤도와 내륜을 더 잘 보이게 했다. 라벨은 부품 설명·재조립 구간에서만 표시한다.
2. 한글 폰트 경로가 `C:/Windows/Fonts/malgun.ttf`로 고정되어 다른 OS에서 기본 폰트로 조용히 대체될 수 있었다. R6은 명시 경로, OS별 설치 폰트, Hangul cmap 검사를 사용한다. Blender에서 실제 Malgun Gothic 로드 메시지를 확인했다. 필요한 글리프가 없거나 Blender가 열 수 없는 폰트면 명확한 오류로 끝난다.
3. 공용 색상 값이 Manim 코드 안에 복제되어 있었다. `core/visual_primitives/design_tokens.json`을 기준값으로 두고 Manim Palette와 Blender 재질이 이를 읽도록 했다. 기존 Manim 의미 색상은 그대로 유지하며 Blender에는 sRGB→linear 변환을 적용한다.
4. “교육용 개념 모델”만으로는 계산 범위가 충분히 드러나지 않았다. 요약 구간에 카드 없이 `교육용 운동 모델`, `접촉력 · 마찰 · 변형 미계산`, `하중 분포 해석 아님`을 표시한다.
5. 기존 부드러운 Area Light, 새틴 재질의 roughness/metallic, 카메라 방향, 30fps 프레임레이트는 유지했다. 새 장식이나 물리 시뮬레이션 주장은 추가하지 않았다.

## 비교 근거

| 버전 | 입력/장면 | 영상 SHA-256 | Blender 렌더 | Manim 렌더 |
|---|---|---|---:|---:|
| 97d0546 | `asset_scene.py`, 생성된 bearing asset 포함 | `cb11c345863bd262a935d58b8a2a4e3f8c6cb78f3f70fd49e9cd11d8deede732` | 754.60 s | 12.23 s |
| R5 / d67ac69 | R5 `bearing_scene.py`, 같은 저장된 Manifest/Timeline | `ea0d3ffeb40562e3443111e8e7d35cc75c8941237e49af149a953c7998fc325f` | 333.99 s | 12.12 s |
| R6 | 현재 `bearing_scene.py`, 같은 수업·84초 설정 | `c44219f83365482ef12e0223994b59c0022ff849a83e8c59655d9480109bd457` | 332.96 s | 12.03 s |

세 버전은 모두 960×540, 30fps, 2520프레임, 84초 H.264로 생성·검증했다. 97d0546은 별도 asset-backed 렌더러이고 R5/R6는 현재 procedural bearing renderer이므로 97과의 픽셀·성능 차이를 디자인 수정만의 효과로 해석하지 않는다. R5→R6 렌더 시간은 사실상 동일하다.

대표 시점 `12, 24, 31, 36, 40, 43, 46, 48, 53, 65, 77초`를 97/R5/R6에서 추출해 비교했다. R6 연락 시트에는 추가로 phase 경계 전후 프레임을 포함했다.

- R6 Preview: `pilots/v13_education/output/r6_visual_qa/r6-final/preview.mp4`
- 97d0546 Preview: `pilots/v13_education/output/r6_visual_qa/baseline-97/preview.mp4`
- 동일 소스 R5 Preview: `pilots/v13_education/output/r6_visual_qa/r6-baseline-r5/preview.mp4`
- 97/R5/R6 비교 시트: `pilots/v13_education/output/r6_visual_qa/before97_r5_r6_comparison.png`
- R5/R6 비교 시트: `pilots/v13_education/output/r6_visual_qa/r5_vs_r6_comparison.png`
- R6 대표 프레임: `pilots/v13_education/output/r6_visual_qa/r6-final/review_frames/`

위 영상과 이미지들은 `.gitignore` 대상 로컬 산출물이며 커밋에 넣지 않는다. 출력 폴더의 `production_report.json`, `visual_manifest.json`, `timeline.json`, `renderer_provenance.json`이 실행별 상세 근거다.

## 검증 결과

- Blender 5.2.1 LTS에서 실제 전체 R6 렌더; Manim Community 0.21.0 구간도 파이프라인에서 생성.
- Preview: PASS — 960×540, 30/1 fps, 2520 frames, 84.000 s, H.264, 무음.
- `validate_delivery.py` / 파이프라인 full decode: PASS; 자막 cue 20개.
- Plan/Manifest/Timeline: PASS; 8개 beat, `CONCEPT_ONLY`, 접촉력·마찰·응력·변형 계산 없음.
- Asset Registry: PASS — 39 assets; education catalog 검증 39 entries, generated assets 6개 확인.
- Scene style: PASS — 변경된 Blender 베어링 장면, Manim 베어링 장면, 공용 Manim kit.
- Unit tests: PASS — `python -m unittest discover -s tests -v`, 223 tests.
- Compile: PASS — 변경한 core, Blender scene, tests 대상으로 `compileall`.
- `git diff --check`: PASS.
- 실제 Blender 폰트: `C:\Windows\Fonts\malgun.ttf`를 `Malgun Gothic Regular`로 로드.
- 별도 black/freeze 후보 검사에서 8.0초와 59.0초 전후의 0.3초 dark 구간, 여러 freeze 후보가 검출됐다. 어두운 Manim 배경/장면 전환 및 의도된 정지·미세 운동 후보와 구분하기 위해 수동으로 결함이라고 단정하지 않았고, 자동 full-motion 판정은 수행하지 않았다.

### 정지 프레임 리뷰

실제 R6 MP4에서 지정 시점과 모든 주요 phase 경계 주변 프레임을 추출했다. 렌더 리뷰어 1회 검토 결과 blocker/high 결함은 없었다. 베어링 부품, 회전 표식, 하중 설명, 요약의 계산 범위 문구가 화면 안에 있고 자막과 겹치지 않았다. 이 리뷰는 정지 프레임과 contact sheet 평가이며 전체 1배속 모션·나레이션 청취·학습자 이해 검증은 아니다.

## 제한 및 남은 QA

- **P0/P1:** 정지 프레임 리뷰에서 확인된 항목 없음.
- **P2:** 전체 영상을 정상 속도로 사람 검수하지 않음. 따라서 모션 리듬, 분해/재조립의 연속성, 장면 전체의 시각 깜빡임 판정은 `PENDING`.
- **P2:** 1080p Final은 렌더하지 않음. 실제 텍스트 최소 크기 검증은 540p Preview 기준.
- **P2:** TTS·자막 음성 동기·마지막 음절 clipping은 검증하지 않음. Preview는 의도적으로 무음.
- **P2:** 계산 결과 기반 접촉 동역학이 아닌 교육용 운동/형상 모델. 마찰력·접촉력·응력·변형·하중 분포를 계산하지 않는다.
- **P3:** Blender 5.2.1이 `Material.use_nodes` API의 Blender 6.0 제거 예정 DeprecationWarning을 냈다. 이번 변경은 현재 API 호환을 유지했으며 Blender 6.x 검증은 하지 않았다.
- SoX는 Manim import 때 선택 의존성 경고가 있었으나 렌더·검증에는 영향을 주지 않았다. 설치 또는 의존성 변경은 하지 않았다.

## 시각 점수 (정지 프레임 근거)

10점은 결함이 확인되지 않고 요구가 충족된 경우에만 준다. 아래 점수는 정지 프레임에서 관찰한 R6 Preview의 상대 평가이며 10점 인증이 아니다.

| 항목 | 점수 | 근거 / 범위 |
|---|---:|---|
| 교육 목적 적합성 | 8.5/10 | 부품·운동 설명, 계산 범위 문구가 분리됨. 실제 학습자 이해도는 미측정. |
| 레이아웃 및 시선 유도 | 8.5/10 | 3D 모델과 우측 무카드 라벨, 회전 cue, 화면 여백 확인. |
| 타이포그래피 | 8/10 | 540p에서 한글 폰트와 문구 가독성 확인, 최소 크기 자동 검사 추가. |
| 색상·조명·재질 | 8.5/10 | 구조별 색상 식별, 하이라이트 억제, 기존 softbox와 satin look 유지. |
| 디자인 일관성 | 8.5/10 | 공용 token 연결, 기존 Manim palette 유지, Blender/R5 및 Manim 프레임 비교. |
| 모션 및 교육 전달력 | N/A | 정지 프레임만 리뷰; 정상 속도 모션을 확인하지 않음. |
| 실제 렌더링 완성도 | 8/10 | 전체 84초 30fps 렌더와 decode 통과. 정상 속도 전체 시청은 미검증. |

**판정:** 정지 프레임·기술 게이트 기준 R6 Preview는 검토 가능한 상태다. 최종 시각 승인이나 10/10 달성으로 표시하지 않는다. 다음 완료 조건은 사용자 또는 QA 담당자의 전체 1배속 시청과 1080p/TTS 생산이 필요한 경우 별도 검증이다.
