# R18 — 재질과 조명만 바꾸는 비교 렌더

## 목표와 범위
R17의 대본·음성22개·문장 자막70개·설명 속도·카메라/물리 상태를 유지하고, 부품 표면과 빛의 관계를 다듬는다. 목표는 상판 하이라이트와 측면 층/틈, 타이어와 바닥 경계를 더 잘 읽는 것이다. 출력 목표는 R17과 같은382.4초/1080p30이다. 교육용 계획·제어 및 기존 Bullet 결과의 렌더이며 실제 로봇이나 Nav2 DWB 실행이 아니다.

`topics/`, 이전 리비전, `studio_utils.py`, `manim_kit.py`는 읽기 전용. TTS 재생성이나 외부 대본 전송은 없다. 새 물리 실행도 없다. 데이터12JSON과 음성/자막 시간은 R17에서 그대로 복사하고 해시로 검증한다.

## 후보와 결정 근거
- 같은 left 실험 pose0/pose180, wheel-ground pose109에서 baseline / material-only / light-only / combined를 비교했다. exposure와 카메라는 고정했다. 유효 재질·광원 위치/크기/출력/world/exposure는 각 `output/cases/left/settings_*.json`에 남긴다.
- 앞쪽 키라이트의 light/combined는 틈과 바퀴를 드러냈지만 상판 하이라이트를 지워 평평한 표면으로 만들었다. combined_v2는 뒤쪽 측면 키로 하이라이트를 되찾았으나 일부 방향에서 센서 뚜껑과 상판의 하이라이트가 너무 강했다.
- selected는 뒤쪽 측면 키를 높이고 넓혀 하이라이트를 완화한다. key(-1.5,2.5,3.6)m/850W/2.2m, fill240W/4m, rim300W/2.5m, world0.26. 상판 roughness0.42, 센서0.48, 타이어0.82. 이 수치는 이 스튜디오 후보의 결정이며 다른 장면의 보편적 정답이 아니다.
- selected pose0/180에서 부드러운 상판 하이라이트와 더 어두운 측면 층의 분리, wheel-ground에서 어두운 타이어의 면/트레드/바닥 경계를 확인했다. 회피의 overview/goal 카메라에서도 후보를 확인했다. 최종 90개 표본 프레임과 사용자 동작 비교 피드백은 아래에 기록했다.
- 기존 카메라·정확한 solver pose와 faithful STL 치수는 유지했다. 표면이 바뀌었다고 coarse STL 실루엣이 개선됐다고 주장하지 않는다. 고정 이미지로 움직이는 하이라이트의 자연스러움을 판정하지 않는다.

## 동일 상태와 재사용
- 네 실험의 root 및 wheel 세계 자세/축 순서는 R14 기록을 그대로 따른다. phase/차축/방향/누적 궤적은 설명용 표시이고 하드웨어/접촉력 표현이 아니다.
- 회피는 R06의 같은 source sample을 R10의 기존 view/time 매핑으로 렌더한다. B01은 원본 frame1–278, B20은317–722를 표시한다. R18에서 실제 wheel 위치와 orientation까지 검증한다. 동일 beat/sample/view의 정지 프레임은 렌더를 한 번 하고 픽셀을 복사한다. source time이나 native30fps를 줄이는 방식이 아니다.
- B19 끝은 pose119와 command120, B20 첫1.5초는 같은 물리 그림이며 다음은 pose120이다. 표면만 바뀌는 새 그림에 맞춰 B19만 Manim 재렌더한다. 나머지 설명 장면은 R17 원본 영상 조각을 읽기 전용 재사용한다.

## 로컬 기능과 스킬 문제
- `surface_treatment.py`: 검증 가능한 광원/재질 설정을 한 곳에서 물리 실험·회피·handoff에 적용한다. 실제 메시의 재질 슬롯과 셰이더를 기록한다. 키트 후보는 표면 후보 적용과 유효 설정 저장이며, 아직 공용 키트로 이동하지 않는다.
- Blender의 `--python` 백그라운드 실행은 이 환경에서 스크립트 폴더를 Python import 경로로 자동 추가하지 않았다. 로컬 helper를 읽도록 `sys.path`에 pilot 폴더를 명시한다. 오류가 있어도 Blender process exit0일 수 있어 실제 산출물/매핑을 확인한다.
- 렌더 스킬의 기존 ‘하이라이트를 보존하라’만으로 모든 로봇 방향을 보장하지 않는다. 후보 pose0뿐 아니라180과 회피 detail을 비교해 강한 센서 반사를 발견하고 선정 전에 완화했다.

## 검증 상태
완성본: `output/planner_control_long_ko_v18.mp4` — 382.40초, 1920×1080, H.264, 30fps, 한국어 음성 + 문장 자막70개.

- `validate_cases.py` / `validate_relations.py`: PASS (`output/physics_validation.log`, `relation_validation.log`).
- `audit_geometry.py`: PASS. 재질 적용 전후 faithful mesh 정점·topology·변환·parent 동일 (`geometry_audit.json`).
- `validate_render.py`: PASS. 12JSON, 22WAV, 음성 manifest, 합성 PCM, 자막 타이밍이 R17과 byte-identical. 실험724개 / 회피684개 바퀴 자세 검사와 source/view/sample 순서, pose119→120 연결 통과 (`render_validation.json`).
- `validate_visual_manifest.py --require-media`: PASS.
- `scripts/check_scene_style.py`: cases/avoidance/handoff/reasoning 전체 PASS.
- `scripts/validate_delivery.py --require-audio --fps 30 --audio-manifest assets/audio/manifest.json --caption-timing output/caption_timing.json --full-decode`: PASS. 22segments, 70captions, 전체 디코드 통과 (`delivery.log`).
- render-reviewer 1회: 완성본90프레임을 8mosaic로 실제 확인하고 B08/B19/B20의 대표1080p 프레임도 확인. 관측된 blocker/high 각각0. 상판 하이라이트 완화, 측면 층/타이어/바닥 경계, 경로색, body 복원, source119→120 연결의 표본 검사 통과 (`render_review.json`, `final_review/index.json`).
- 재질·조명 목표는 확인한 범위에서 met. 전체 정상 속도 시청·청취를 도구로 직접 수행하지 못해 종합 교육 리뷰는 incomplete. 초보자 이해는 not_assessed. 이 상태를 기술 PASS나 비교 영상 사용자 피드백으로 대체하지 않는다.
- 남은 비차단 관측: 원래 STL의 각진 실루엣/EEVEE 그림자 입자; B19의 밝은 화면으로 전환하는 순간 흰 제목 대비가 낮음(색 화살표·외곽선 자막은 읽힘). 이번 표면 개선을 형상 개선이나 두 채널과 동급이라는 판단으로 확대하지 않는다.

## 재현
프로젝트 루트에서 실행한다. Windows Blender 호출에는 이 WSL 환경의 실행 권한이 필요하다.

```bash
uv run python pilots/05_moving_obstacle/revision_18/render_all.py
uv run manim -qh --media_dir pilots/05_moving_obstacle/revision_18/output/final_render pilots/05_moving_obstacle/revision_18/reasoning_scene.py PatchB19
'/mnt/c/Program Files/Blender Foundation/Blender 5.2/blender.exe' --background --python '\\wsl.localhost\Ubuntu-24.04\home\sang\make_simulation\pilots\05_moving_obstacle\revision_18\audit_geometry.py'
uv run python pilots/05_moving_obstacle/revision_18/deliver.py
uv run python pilots/05_moving_obstacle/revision_18/review_samples.py
```

실행 기록에서 Blender 크기2.2가 2.200000047로 저장되어 정밀 비교가 실패했다. 원본 설정·출력은 유지하고 크기 비교에1e-6 허용 오차를 적용한 뒤 PASS. 첫 도입 PNG 인코딩은 미사용279프레임 탐색 경고를 출력했으나 지정된278프레임이 모두 인코딩된 것을 ffprobe/전체 디코드로 확인했다.

## 사용자 비교 영상 피드백
R17 왼쪽 / R18 오른쪽의 같은 B08 동작·카메라·음성 17.5초 비교(`output/material_motion_comparison.mp4`)에 대해 사용자는 “R18이 더 자연스럽고 선명함”이라고 응답했다. 움직이는 표면·조명에 대한 이 비교 범위의 평가이며, 전체 영상 시청·청취나 초보자 이해 검증으로 확대하지 않는다.
