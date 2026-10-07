# R12 — 기록된 바퀴 작동과 수식 항의 연결

렌더 전 목표 A1: 같은 Bullet 실행 source2.00–2.80초의 바퀴/몸 자세를 실제 기록에서 재생해 부품의 작동이 보인다. A2: 좌우 속도 목표와 바퀴 간격을 source token으로 유지하고 수식 항으로 복사해 operand→operator→result 순서를 보인다. A3: 동등 속도 가정에서 그림과 식의 값을 함께 갱신하며 원래 실행의 물리 응답으로 복귀한다.

기존 한국어 설명/78.80초/1080p30을 유지한다. R06 Bullet 실행은 읽기 전용 재사용이며 새 solver 실험이 아니다. 교육용 A*+lookahead 제어이며 Nav2/DWB/실기 실행이 아니다. 명령 목표와 기록된 응답을 구분한다. 부품 숨김과 작은 위상 점은 렌더 주석이며 모델 형상/충돌/접촉력을 바꾸거나 발명하지 않는다. topics/이전 revision/공유 키트는 수정하지 않는다.


## 완료 결과와 결정 근거

- 스킬 개선을 먼저 commit `eaf1ad3`으로 origin/main에 일반 push한 뒤 R12를 제작했다. Director5.9,Manim5.8,Blender5.9,Reviewer2.1에 기록된 부품 작동·값→항 전개와 실제 프레임 검증 기준을 넣었다.
- 최종: `output/planner_physics_ko_v12.mp4`,78.80초,1920×1080,30fps,한국어 나레이션,17문장 자막. 기존 R11 음성/실측 타이밍을 재사용해 새로운 TTS 전송은 없다.
- A1/A2/A3 프레임 기준 met. 실제 프레임 review1회와 발견 사항의 수정 확인에서 blocker/high0. 정상 속도 재생·청취 접근이 없어 전체 교육 검토는 incomplete. 첫 시청자 이해는 not_assessed. [비교 분석](COMPARISON.md)에 범위를 기록했다.

### 데이터 경계

R06 Bullet baseline planner_on source60..84(실험2.00–2.80초)의 root/wheel pose를 읽는다. render-only84프레임에 반복 매핑하며 새 물리 실행이나 성능 개선을 주장하지 않는다. 세계 좌표 wheel quaternion/position을 root상대 좌표로 변환한다. recorded motor/joint order는 right,left이며 모델 wheel 객체는 left,right여서 순서를 명시적으로 뒤집는다. 음수 motor axis 값을 후진으로 해석하지 않는다. 그림과 식은 sample60의 명령 목표를 사용하고 측정 응답의 순간 속도로 주장하지 않는다. 실제 명령은 응답 구간 동안 변한다.

전진 목표를 유지하고 회전 목표만0으로 바꾸는 조건은 속도 변환 가정이다. 다른 solver 실행·제어기 전체 재계산·실기/Nav2 검증이 아니다. 접촉력 시계열이 없어 힘 화살표는 만들지 않았다. 상판 숨김과3.5mm위상 점은 렌더 주석이다. 기존 physics 실행·V9 trace·모델·공유키트10개 파일의 hash동일 확인 PASS.

### 로컬 기능과 키트 후보

- `component_scene.py`: 기록된 joint world pose를 정확한 local pivot pose로 바꾸고 source/frame매핑 저장. 키트 후보: 기록된 관절 pose 어댑터와 swept framing. 시뮬레이션과 렌더 주석을 별도 유지할 필요가 있다.
- `reasoning_scene.py`: 식 항을 개별 mobject로 만들고 TransformFromCopy로 source값/간격을 연결. 키트 후보: 의미 역할/단위/조건 변경을 보존하는 항별 표현 helper.
- `prepare_component.py`:84native PNG와 pose 오차 검증 후 UTF-8 textfile 주석으로 인코딩. 키트 후보: source매핑 포함 관절 재생 미디어 검증.
- 공유 `studio_utils.py`, `manim_kit.py`는 직접 수정하지 않았다.

### 발견과 수정

1. 실제 solver joint position에는 고정 URDF pivot과 작은 차이가 있다. 정적 pivot을 강제하던 검증을 느슨하게 하지 않고 기록된 위치를 재생했다. 모든 wheel orientation<1e-4rad,position<1e-5m 검증 PASS.
2. Windows Blender는 Python assertion이 발생해도 exit0을 반환한 경우가 있었다. 종료 코드 외에 기대 프레임1..84와 매핑/이미지 검증을 필수로 확인했다.
3. TransformFromCopy 이후 color속성에서 색을 추론하면 조건 갱신값이 검게 됐다. 좌/우 의미 색상을 명시적으로 지정해 native프레임으로 수정 확인했다.
4. 복사 수치가 설명 문장을 지나갔다. 수식 전개 동안 해당 문장을 숨기고 이전 식을 흐리게 했다. 최종 합본의 이동 중간 프레임을 확인했다.
5. FFmpeg inline drawtext의 콜론으로 범례가 깨졌다. UTF-8 textfile을 사용해 수정하고 최종 범례의 한국어/색상 대응을 확인했다.

### 검증과 재현

`uv run python prepare_component.py`와 `uv run python assemble.py`는 프로젝트 루트에서 각 파일의 전체 상대 경로로 실행한다. Blender는 Windows5.2LTS이며 각 batch<=48프레임으로 native렌더. Manim preview540p30→final1080p30.

- validate_visual_manifest.py --require-media PASS
- check_scene_style.py reasoning_scene.py component_scene.py PASS
- stage_segments.py:7segments PASS
- validate_delivery.py --require-audio --fps30 --audio-manifest assets/audio/manifest.json --caption-timing output/caption_timing.json --full-decode PASS
- validate_evidence.py:기존6V9 trace/물리 반복·fine probe/제어 명령 증거 PASS
- prepare_component.py:84native프레임/기록된 joint 변환/순서 PASS
- 보호 input10개 hash PASS

명령과 실제 출력은 `output/delivery_validation.json`, `output/run_validation.txt`, 프레임 검토는 `output/render_review.json`에 남겼다. 미디어는 gitignore대상이며 R12결과는 로컬에 있다.
