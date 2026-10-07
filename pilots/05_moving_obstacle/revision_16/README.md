# R16 — 연결된 기구·수식 발생·같은 실행의 피드백

## 범위와 결정
승인된 음성과 기존12개 Bullet trace를 사용한다. 사용자 피드백 “수식 도출이 빠름”에 따라 B14에 두 번의 4초 읽기 여백을 추가하고, B22의 중복 질문·답변 두 문장은 제거해 마지막 완전한 요약 문장만 남겼다. 총 길이는356.13초(5분56초), 문장 자막66개다. 나머지20개 WAV는 R14와 동일하다. 새 TTS 전송·새 물리 실행은 없다. 화면 변수를 비교하기 위해 R16을 별도 제작한다. 공용 키트·topics·기존 리비전은 읽기 전용이다. 스킬 커밋134a3a3을 먼저 origin/main에 푸시했고, 실제 도출 속도 피드백을 반영한 후속 커밋fa9a6b7도 푸시했다.

| 목표 | 소유 | 완료 조건 | 구간 |
|---|---|---|---|
| 연결된 바퀴 기구 | Blender | 기록 바퀴/참고 차축/차축 중심·방향/ground history가 cutaway에서도 함께 읽힘 | B06/08/10/18 |
| 기하로 식 도출 | Manim | 중심 중간값→평균, 공통각/반지름차→bθ 중간 단계를 그림에서 따라감 | B12/14 |
| 같은 실행 피드백 | Manim | R06 pose/target/명령→기록 응답→다음 비교가 동일 좌표와 source time으로 이어짐 | B16/19 |
| 조건 변화 그림 | Manim | 좌우 이동/시간 고정, 간격2배의 실제 이상적 각도절반을 비교 | B15 |
| 표면 분리 | Blender | 동일 pose/camera baseline/material/light 후보 비교에서 상판층·고무·접촉 분리 개선 | 모든 새 cases |
| 과제별 구성 | Director/finishing | 예측/실험 반복 대신 비교는 궤적, 도출은 중심 기하, 피드백은 world scene로 설명 | B08/11–19 |

## 데이터 경계
교육용 계획·제어 및 Bullet 모형이며 Nav2 DWB 실행/실기/센서 검증이 아니다. 기존 R14 별도 바퀴 실험과 R06 회피 실행을 구분한다. 평균/호/간격 비교는 이상적 미끄럼 없는 기하이며 solver 응답으로 표현하지 않는다. 차축선·차축 중심/방향·phase mark는 render annotation이며 실제 샤프트/힘 측정이 아니다. source time과 presentation time을 보존한다.

## 검증
필수 기술게이트 모두 PASS. 최종 합성본116개 프레임의 render-reviewer 검토에서 blocker/high0개. 정상속도 전체 시청/청취와 초보자 이해는 별도 미확인 상태다.

## 로컬 키트 후보
공통각/반지름차 도출, midpoint 평균, 동일 source world feedback, recorded cutaway anchor/history, fixed-pose material comparison. 실제 검증된 부분만 이관 후보로 남기며 키트는 직접 수정하지 않는다.

## 후보 선택과 발견한 문제
같은 left 실험 frame1/91에서 baseline/material/material+light 후보를 actual native PNG로 비교했다. 첫 metallic .65/밝은 base 후보는 바닥과 비슷하게 밝아져 배제했다. 선택은 상판의 .13/.16/.20 base, metallic .15, roughness .46, 다른 몸체 부품 roughness .52의 material-only 처리다. 추가 broad light 후보는 층의 대비 이득이 작아 선택하지 않았다. faithful mesh는 동일하며 EEVEE samples를64로 올렸다. 샘플 프레임에서만 표면 분리 효과를 판단했고 움직이는 반사/노이즈 감각은 미확인이다.

첫 Manim preview에서 B15 하단 글자 겹침, B14 시간 나눗셈 전환의 남은 식, B11 원래 로봇과 궤적 중첩을 발견해 수정했다. 공용 키트의 결함으로 단정하지 않는다. addressable token으로 변환한 그룹은 원래 source 객체가 아니라 live 그룹을 퇴장시켜야 잔상이 사라진다. 컷 기준점은 world/robot-relative 변환의 handedness를 확인해야 왼쪽이 화면 왼쪽으로 대응한다.

스킬 검증기는 PyYAML을 필요로 하지만 프로젝트 runtime 의존성에는 없었다. 임시 `uv run --with pyyaml` 환경으로 스킬5개를 검증했고 프로젝트 pyproject/lock은 바꾸지 않았다. 기존 long_form validator 미커밋 변경은 R14에서 물려받은 작업이며 이번 스킬 push에서 제외했다.

## 도출 속도 사용자 검토
첫 미리보기에 “수식 도출이 빠름” 피드백이 있었다. B14를26.47초로 늘려 이동 거리 식→반지름 차이→각도 식의 읽기 시간을 확보했고, 수정된75.33초 B12–B15 미리보기에 사용자가 “이제 따라가기 좋음”으로 답했다. 이는 해당 도출 속도에 대한 informed 사용자 피드백이며, 전체 영상 청취나 초보자 이해 검증으로 확장하지 않는다. 승인 음성의 편집 경계에는6ms/12ms 짧은 램프를 적용했다.

## 최종 결과와 실행 근거
- 최종 영상: `output/planner_control_long_ko_v16.mp4` — 1920×1080,30fps,H.264/AAC,356.13초,문장 자막66개.
- `uv run python deliver.py --skip-render`를 프로젝트 기준 경로로 실행했다. `output/delivery.log`에 require-media/style/stage22segments/require-audio/fps30/caption/full-decode PASS가 남아 있다.
- `validate_cases.py`: 기존12개 V9 trace·물리 실험 검증 PASS. `validate_relations.py`: 이상적 기하와 동일 R06 제어 명령 관계 PASS. `validate_render.py`:724개 recorded pose/렌더 및20개 미변경 WAV SHA 대응 PASS; B14/B22 음성 편집은 `output/pacing_edit.json`에 선언했다.
- `output/final_review_report.json`:116개 최종 프레임 검토,blocker/high0개. 개별 프레임과 범위는 `output/final_review/index.json`.
- 실제 처음 만든 미리보기의 빠른 도출 문제는 사용자 피드백→타이밍 수정→새 미리보기 사용자 확인까지 마쳤다.

## R15 및 채널 비교의 결론
`output/comparison/R15_R16.png`에 전후 프레임을 남겼다. R15의 분리된 바퀴는 차축 중심·방향·지면 기록으로 연결됐고, 바로 제시하던 bθ 식에는 반지름/공통각의 중간 대응이 생겼다. 글자로 끝나던 간격2배 조건은 동일 이동량에서 실제 이상적 두 몸체의 다른 회전각으로 바뀌었다. 정지 도식에 머물던 피드백은 같은 R06 실행의2→4초 상태·명령·다음 비교로 이어진다.
기존8개 원본 발췌 조사(`research/channel_craft_2026_10/STUDY.md`)에서 잡은 bRd의 기구 연결과3Blue1Brown의 그림→식 대응 목표를 이번 화면에서 보완했다. 이것은 해당 관계와 샘플 프레임의 개선 근거다. 표면 개선은 작으며, 움직이는 반사 안정성·전체 정상속도 청취·초보자 전이 이해를 확인하지 않았으므로 두 채널 전체와 동급이라고 결론내리지 않는다.

재현: 승인 음성 편집은 `retime_approved_audio.py`, Manim 재렌더/합성/게이트는 `deliver.py`; Blender는 Windows Blender5.2의 `render_cases.py`(WSL interop 권한 필요). 공용 키트 변경 없음. 기존 long_form validator 변경은 이번 작업 이전 미커밋 상태이며 그대로 사용했다.
