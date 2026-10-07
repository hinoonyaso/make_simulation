# R15 — R14 스킬 보완의 렌더 실험

## 최종 전달 — 2026-10-07

[최종 영상](output/planner_control_long_ko_v15.mp4): **359.23초 / 5분59초 / 1920×1080 / 30fps**, 한국어 SunHi 나레이션과 68문장 자막. [핵심 미리보기](output/critical_excerpt.mp4)는 67.33초 / 960×540이며 최종 설명 렌더를 사용한다. [R14/R15 동일 시점 비교](output/comparison/R14_R15.png), [프레임 리뷰](output/final_review_report.json).

| 검사 | 결과 / 근거 |
|---|---|
| V9 12개 / 재사용 물리 비교 | PASS / `output/physics_validation.json` |
| 724개 신규 Blender 프레임 / 바퀴 자세 | PASS / `output/case_render_validation.json` |
| 12 trace·22 음성·전체 WAV·자막 원본 일치 | PASS / `output/reuse_validation.json` |
| 변경 Manim 7개 1080p30 | PASS / `output/manim_render_validation.json` |
| manifest require-media / 두 scene style / 22 segments | PASS / `output/final_delivery_validation.log` |
| 최종 음성·30fps·68자막·전체 디코드 | PASS / 같은 로그 |
| 실제 최종 프레임 검토 | 79개 샘플 / 확인 범위 미해결 blocker0/high0 |
| 정의한 연출 목표 4개 | 모두 met / 프레임 리뷰와 비교 이미지 |

정상 속도 직접 시청·청취와 신규 초보자 이해도는 미확인이다. 전체 교육 리뷰는 `incomplete`로 유지하며, 두 채널 동급을 선언하지 않는다. 동일 대본/음성/물리 자료로 비교해 이번 변화는 화면 연출 효과다. 소재·조명은 기존 스튜디오 조건을 유지했다. 원래 에피소드와 공용 키트는 수정하지 않았다. 현재 작업은 업로드/푸시를 실행하지 않았다.

아래 중간 단계의 대기·발견 기록은 제작 이력이며, 현재 결과는 이 최종 전달 절을 따른다. 장편 manifest는 기존 R14에서 적용한 `long_form` 검증기를 사용했고 이번 작업에서 그 공용 파일을 변경하지 않았다.

## 범위와 완료 기준

R14의 359.23초 한국어 대본·음성·68문장 타이밍과 Bullet 실험 12개를 그대로 재사용한다. 새 물리 실행이나 새 음성 생성이 아니다. 교육용 계획/제어 및 물리 엔진이며 Nav2/DWB/실기 검증 아님. R06 회피 장면은 별도 실험 재사용으로 유지한다. 이전 revision, topics 및 공용 키트는 읽기 전용이다.

이번 네 목표: (1) 바퀴/접촉부 확대 컷의 빈 바닥을 줄여 작동 부품이 읽힘, (2) B05/B07/B09 질문·화살표 교차 제거, (3) B14 두 바퀴 이동 호·차축·몸의 각도→Δs=bθ→각속도 연결, (4) B12/B13/B15 수식 업데이트의 중간 글자 형태 유지. 기존 manifest focus와 리뷰에서 같은 목표를 검사한다.

대본을 고쳐 외부 TTS를 다시 보내는 대안 대신, 동일 음성에 시각적 근거를 맞추어 연출 효과를 분리한다. 새 도형은 미끄럼 없는 이상적 기하이며 Bullet 궤적을 이상적 호로 대체하지 않는다. 카메라만 변경하고 solver pose는 매 프레임 검증한다. 변경 Manim beat와 Blender 바퀴 실험은 새로 렌더하고, 나머지 R14 picture part를 읽기 전용 재사용해 전체 합본한다.

핵심 유음 미리보기→실제 프레임 리뷰/패치→1080p30 전체 합본→trace/manifest/style/audio/caption/full-decode 게이트를 실행한다. 정상속도 직접 시청·청취와 신규 초보자 이해는 도구 접근이 없으면 별도 미확인으로 기록한다. 동급/완벽을 보장하지 않는다. 업로드나 푸시는 이번 요청에 포함되지 않는다.

## 로컬 구현 / 키트 후보

이상적 차동구동의 이동 호·차축·각도 도식, 고정 항을 유지하는 수식 슬롯 교체, 실제 solver 바퀴에 맞춘 카메라와 명시적 component cutaway를 pilot-local로 구현한다. 실제 렌더 확인 후 재사용 가치가 확인되는 부분만 키트 후보로 기록한다. 공유 kit 파일 수정 없음.

## 실행과 발견한 문제

- `uv run python pilots/05_moving_obstacle/revision_15/validate_cases.py`: 재사용된 V9 trace와 기존 반복/간격 비교 재검증. 새로운 실험 실행으로 주장하지 않는다.
- `uv run python pilots/05_moving_obstacle/revision_15/render_cases.py`: 설치된 Windows Blender를 사용해 네 조건의 181프레임씩 재렌더. WSL 연동 소켓은 샌드박스 밖 실행이 필요하며 기존 데이터/키트는 읽기 전용.
- `uv run python pilots/05_moving_obstacle/revision_15/deliver.py`: 변경된 7개 Manim beat 렌더→재사용 검증→합본→게이트. 이미 렌더한 경우 `--skip-render`. 외부 TTS 호출 없음.
- 실제 미리보기에서 Text 그룹의 `get_color()`가 의도한 글리프 색상을 반환하지 않아 교체 숫자가 검게 보였다. 좌우 역할의 팔레트를 명시하고 재렌더 확인했다. 다중 글리프 그룹 전체를 문장으로 Transform하던 숫자/제목 전환은 주소 가능한 항 교체와 짧은 제목 교체로 변경했다.
- 평균의 반대방향/동일속도 사례는 기존 문장 정렬의 8.29/14.73초에 맞춰 값과 식이 갱신되도록 배치했다. 고정평균 비교는 차이 증가 문장 전에 갱신한다. 제목 교체 중간도 검사한다.
- 카메라는 실제 몸의 위치를 따라가며 세계 방향은 유지한다. 바퀴가 작동하는 구간에서만 더 가까워지고, 몸체 표시의 시작/끝은 넓힌다. 실제 바퀴 pose는 매 프레임 검증하며 컷어웨이 동안 타이어 위치에 맞춰 시선을 낮춰 자막 여백을 남긴다.
- 960×540 미리보기에 최종 배달 기본값(1080p)을 적용하면 예상대로 FAIL한다. 미리보기 검사는 `--min-width 960 --min-height 540`로 명시하고, 최종 검사에서는 기본 1080p 기준을 유지한다.

실제 native frame146에서 몸체 복원 순간의 상판 crop을 발견했다. 확대를 body-hidden 40–145프레임 안으로 제한하고 146 전에 넓은 구도로 복귀하도록 수정했다. 이미 렌더한 equal/left는 경계 26–55 및130–160프레임만 재렌더해 전체 mapping에 병합한다(`repair_camera.py`). spin/stop은 수정 소스로 처음부터 렌더한다. 정상 재현은 수정된 `render_cases.py` 전체 실행이며, repair는 이번 증분 작업의 경로다.

기하 도형의 좌우 반경 비도 같은 명령 예(.05/.25m/s)에서 계산한다. 화면 차축 span을 기준으로 rL=span×vL/(vR−vL), rR=rL+span을 사용하여 앞뒤 수식과 같은 입력을 유지한다. 값은 이상적 구성의 입력이고 실제 물리 궤적은 아니다.

## WSL 연결 복구

WSL 연결이 끊겨도 이미 시작한 Windows Blender는 계속 실행될 수 있다. 복구 때 완성 이미지 수가 증가하는 것을 확인했고 Blender 프로세스의 PID/시작 시각/대상 경로로 원래 작업을 식별했다. 중복 시작한 복구 프로세스만 종료하고 원래 Windows 렌더를 유지했다. Linux orchestration 세션은 소실되어 마지막 조건은 완성 mapping/이미지를 확인한 뒤 ffmpeg 인코딩과 게이트를 로컬에서 이어간다. 일부 Manim 마지막 실행은 미완료이므로 B14/B15만 재렌더했다.

재발 방지 후보: WSL/Windows 분리 프로세스의 작업 ID·PID와 완료 artifact를 확인하는 pilot-local 복구 실행기. 출력 파일 존재만으로 완료라 판단하지 않고 mapping 수·181프레임·미디어 디코드를 검사한다. 이번 작업에서 공용 스킬/키트를 다시 변경하지 않는다.

최종 합본의 B13 중간 프레임에서 좌우 라벨을 순서대로 교체하는 동안 한쪽만 바뀐 상태가 보여 평균 유지 조건과 잠깐 어긋났다. 좌우 라벨과 수식 피연산자/결과를 같은 애니메이션 단계에서 함께 교체하도록 수정했다. 원래 수식 관계는 유지하고 교체 글자는 짧게 사라진 뒤 나타나게 해 글리프 혼합을 피한다. raw 수정본 6.9/7.3/7.8초에서 이전 상태→함께 교체→새 상태를 확인했으며 최종 합본 재검증을 이어간다.

최종 수식 handoff에서 `always_redraw` 도형과 별도 FadeIn으로 추가된 항이 그룹 FadeOut만으로 즉시 정리되지 않아 이전 θ/거리 식이 잠깐 남았다. 실제 Scene 목록에서 지속 객체를 제외한 종료 객체를 수집하고, recursive updater를 종료한 뒤 FadeOut/remove한다. 현재 데이터와 의미가 유지되는 로봇·제목·값·화살표는 보존한다. B14/B15만 다시 렌더해 경계를 검증한다. 공용 kit 후보는 상태 전환 시 실제 Scene family와 updater를 함께 관리하는 국소적 retire helper이며, 단순 그룹 opacity만으로 의미 종료를 처리하지 않는다.
