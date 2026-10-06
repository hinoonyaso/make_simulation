# revision 08 — 회전 이유와 스튜디오 화면 개선 비교

## 의도와 결정

강화한 Director/Manim/Blender/Reviewer 스킬을 같은 회피 영상에 적용했다. 처음 보는 사람에게 목표 방향과 현재 방향의 관계를 먼저 설명하고, 재질·조명·구도를 실제 동일 상태 프레임으로 비교한다. 설명 외의 B01–B03/B05–B06 대본과 기존 물리 실행은 유지한다. 전제 지식은 로봇의 앞 방향과 경로의 뜻이며 제어 수식·부호·단위를 알 필요는 없다.

B04는 **새 경로에서 조금 앞의 목표점 선택 → 현재 방향보다 왼쪽 → 왼쪽 보정 명령 → 이미 정렬된 방향이라는 가정에서 명령 0 → 실제 물리 응답** 순서다. 수치 표기보다 이유를 먼저 드러낸다. 비교에서 현재 방향만 가정으로 정렬하고, 실제 재생 전에 기록된 자세로 돌아온다. 가정은 방향 화살표와 로봇의 설명용 회전에 표시되며 새 물리 실행을 뜻하지 않는다. t2 명령은 직전 t1.967 자세로 계산되어 그 입력을 사용한다. `output/controller_evidence.json`은 실제 제어 코드의 목표 선택/명령 일치와 정렬 시 w=0을 확인한다. 명령과 달성된 회전은 구분한다.

처음 생성한 B04 21.5초는 manifest의 비트 길이 검사에 실패했다. 내용을 나누어 장면 전환을 늘리는 대신 중복 표현을 줄여 19.267초로 녹음했다. 기존 12.1초보다 7.167초 늘었고 전체는 73.933초다. 문장 자막 17개와 측정 타이밍을 사용한다.

## 데이터 경계

`../revision_06/data/`의 기존 Bullet 실행 6개를 읽기 전용으로 사용한다. 새 solver 실행/성능 향상이 아니다. Blender 키프레임은 모터 구동으로 계산된 기존 물리 결과를 재생하며 Manim도 같은 pose/목표점/명령을 사용한다. **교육용 A* + lookahead/heading 제어 모형이고 실제 Nav2/DWB, 실기 또는 센서 시뮬레이션이 아니다.** 드럼은 정적으로 계속 존재하며 2초에는 이상화된 지도 정보만 추가된다. 모델 근사와 solver 검증은 revision_06 README를 참조한다.

`validate_evidence.py`는 기존 검증의 읽기 경로를 revision_06으로 두고 보고서만 이번 output에 저장한다. 기본/반복/세밀 6개 trace와 물리 probe를 재검증한다. 실제 solver 시간/프레임/카메라는 `output/blender/source_mapping.json`에 기록한다. 방향 정렬 가정은 solver trace에 넣지 않는다.

## 스튜디오 후보 선택

`output/style_comparison.html`에서 접촉(frame278), 회피(frame428), 목표(frame628)의 같은 solver 상태를 비교한다. baseline은 기존 화면, materials는 기존 카메라에서 재질·조명만 변경, camera는 기존 재질·조명에서 구도만 변경, selected는 선택 조합이다. 물리 형상/질량/마찰/결과와 경로 색 의미는 변경하지 않는다.

첫 후보는 키 라이트를 앞쪽으로 옮겨 차체를 평평하게 만들었다. 실제 프레임을 보고 배제하고 기존 키 라이트 방향을 유지했다. 검은 차체의 밝기를 낮추고 센서·타이어의 재질 반응을 구분하며 환경광/보조광을 제한했다. 목표 장면에서 센서의 검은 표면, 차체 층과 바퀴 실루엣이 기존보다 구분된다. 회피 카메라 초안은 드럼 뒤의 로봇 하부를 가렸다. 핵심 합본에서 발견해 시점을 높여 가림을 제거했다. 최종 회피 카메라는 로봇/드럼 여유를 가림 없이, 목표 카메라는 차체와 목표 링을 함께 보여준다. 얕은 심도/장식적 카메라 이동을 추가하지 않았다. 이 비교는 화면 공예의 근거이며 초심자 이해도나 보편적 선호를 입증하지 않는다. 가져온 STL의 각진 상세와 일부 밝은 경로 재질은 남은 취향/완성도 관찰이다.

## 키트·스킬 관찰

공용 `studio_utils.py`, `manim_kit.py`, topics 및 기존 revision 소스는 수정하지 않았다. 로컬 후보는 (1) 실제 lookahead 선택 강조와 제어 가정 비교, (2) 동일 solver 상태의 재질/조명/카메라 분리 비교, (3) 측정된 문장 시작 시간의 reveal anchor다. 여러 사례에서 확인한 뒤 키트로 옮길 후보이며 아직 공용화하지 않는다.

재질 비교 중 프레임 변경 콜백이 수동 카메라 변경을 덮어써 구도까지 바뀌는 문제가 있었다. camera_for_frame 자체에서 materials-only를 기존 구도로 고정하고 다시 렌더하여 비교 조건을 복구했다. 초안의 목표점 라벨과 참고 경로 겹침도 위치를 옮겨 수정했다. 긴 단일 추론이 manifest 20초 상한에 걸릴 수 있음은 스킬/검증 정책 검토 후보다. 이번에는 문장 중복을 줄여 기준에 맞췄다.

Windows Blender는 WSL sandbox의 interop 소켓이 막혀 허용된 실행 범위에서 실행했다. Edge TTS는 이전 승인 범위의 새 교육 나레이션 전송만 사용했다. Resolve 연결 도구가 없어 기존 파일럿 FFmpeg 조립과 sequence staging을 사용한다.

## 이해도와 검토 범위

실제 초심자의 첫 답변은 아직 없다. learner_check는 `not_assessed`이며 제작자/에이전트의 해석을 초심자 증거로 주장하지 않는다. 확인 질문은 “왜 이 로봇이 여기서 돌았나요?”와 “이미 선택한 목표점 방향을 향했다면 어떤 회전 명령이 나올까요?”다. 먼저 영상만 보여주고 초기 답변/혼동 시점을 기록한 뒤 필요한 관계만 수정한다.

새 대본/화면의 정상 속도 재생·직접 청취는 도구에서 지원되지 않는다. 이전 버전의 사용자 피드백은 이번 변경된 B04 음성·타이밍에 자동 적용하지 않는다. 픽셀/시간/기술 검증과 실제 사용자 playback 증거를 구분한다. 최종 게이트와 프레임 리뷰 결과는 제작 완료 후 아래에 추가한다.

최종 렌더는 구도 수정 전에 완료된 동일 B01 frame1–47을 유지하고 `--start-frame 48`로 나머지를 재개했다. 이 47프레임은 기존 버전 재사용이 아니라 이번 재질·조명으로 생성한 native1080p 프레임이다. 옵션 없이 실행하면 전체를 다시 렌더한다.

긴 Windows 렌더가 frame142 저장 중 exit143으로 종료됐다. 디스크/메모리 부족 근거는 없고 종료 원인은 미확인이다. PNG 크기 header만으로 완료를 판단할 수 없어 IEND까지 확인하고 frame142부터 60프레임 이하의 구간으로 나눠 재개했다. `--start-frame N --end-frame M --batch`는 구간 렌더이며 마지막 구간만 최종 비교 이미지를 생성한다. 최종 검사는 모든 PNG의 native 크기/끝 표식과 합본 전체 decode를 함께 사용한다.

최종 native 프레임 검토에서 B01 확대 직후(frame183) 로봇이 왼쪽에 잘리는 기존 구도를 발견했다. 접촉 구도의 범위를 넓혀 frame183–278만 다시 렌더했다. 같은 solver 상태/재질/조명이며 접촉 면과 접근 로봇을 함께 유지한다.

최종 편집 라벨이 복도 벽의 어두운 트림과 겹치는 관찰을 수정했다. B01/B05 안내를 밝은 빈 바닥 영역으로 내려 라벨 대비를 확보했다. 자막과 로봇은 가리지 않으며 새 Blender 렌더 없이 편집 구간만 다시 조립했다.

## 최종 결과와 검증

- 최종 영상: `output/planner_physics_ko_v8.mp4` — **73.93초, 1920×1080, 30fps, H.264/AAC, 한국어 문장 자막 17개**. 외부 자막은 `output/final.ko.srt`.
- 비교: `output/style_comparison.html` — 동일 상태 스튜디오 비교와 R07/R08 회전 이유 구간 재생 버튼. 핵심 발췌본 `output/critical_excerpt.mp4`는 최종 수정 구도로 갱신했다.
- 기존 물리 trace 6개/schema/반복·세밀 probe 및 실제 제어 입력/정렬 가정 명령 검증 PASS: `output/run_validation.txt`, `output/controller_evidence.json`.
- `validate_visual_manifest.py --require-media`, Manim/Blender `check_scene_style.py`, 6구간 sequence staging: PASS.
- `validate_delivery.py --require-audio --fps 30 --audio-manifest assets/audio/manifest.json --caption-timing output/caption_timing.json --full-decode`: PASS. 측정 근거는 `output/delivery_validation.txt`, 파일 해시/속성은 `output/delivery_identity.json`.
- 모든 Blender PNG 698개의 native1080p 크기와 IEND 확인, 합본 전체 decode PASS. 미리보기 프레임을 최종에 섞지 않았다.
- render-reviewer 스킬의 실제 핵심 프레임 검토 1회와 발견 결함의 제한된 수정 검증, 최종 합본 15개 시점 검토: **검토 범위의 남은 blocker/high 0개**. 상세 `output/final_review.json`. 도입 잘림, 회피 가림, 라벨 대비는 실제 새 프레임으로 확인했다.
- 실제 초심자의 이해도는 `not_assessed`. 새 음성/변경된 컷의 직접 정상 속도 재생·청취도 아직 `incomplete`. 제작물과 기술 게이트 완료를 완전한 교육적 승인/동급 채널 품질로 확대하지 않는다.

재현: `prepare_audio.py tts|captions visual_manifest.json` → `uv run manim --disable_caching -r 1920,1080 --fps 30 --media_dir pilots/05_moving_obstacle/revision_08/output/final_render pilots/05_moving_obstacle/revision_08/reasoning_scene.py ClosedLoopReasoning` → 설치된 Windows Blender에서 `blender_scene.py` → `uv run python pilots/05_moving_obstacle/revision_08/assemble.py`. 물리 provenance와 입력 데이터는 revision_06을 함께 보존한다. 영상·이미지·오디오 출력은 기존 gitignore 정책을 유지한다.
