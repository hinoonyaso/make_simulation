# R13 — 4명 시청자 평가 기반 읽기·원인 연결 실험

목표 C1: 지도 목표 방향→회전 명령→좌우 바퀴 차이를 같은 예와 방향으로 연결. C2: 속도 목표=바퀴에 요구한 값, 기록된 응답=물리 결과를 일상어로 정의. C3: 평균/차이식을 순서대로 활성화하며 이동 토큰이 읽히는 식을 가로지르지 않고 최종 자막과 읽기 시간 확보. 이미 긍정적인 기록된 부품 응답 컷은 유지.

새 물리 실험이 아니라 R06 Bullet 데이터와 R12 검증된 렌더의 읽기 전용 재사용. 교육용 A*+lookahead/heading 제어이며 실제 Nav2/DWB/하드웨어가 아니다. topics/기존 revision/공유 키트를 수정하지 않는다. 기존 voice/rate 유지, 바뀐 문장만 기존 승인된 Edge TTS로 생성. 총60–90초를 목표로 반복 결론/도입을 줄여 핵심 읽기 시간을 배분한다.

검토 근거: R12/forms/EVALUATION_RESULTS.md,4응답(초보1/조금앎2/경험1). 일반 학습 효과·동급 판정은 미확인. 이번 확인은 렌더의 표현과 시간 배분이며 실제 이해 효과는 후속 사람 평가가 필요하다.


## 제작 결과와 로컬 결정

최종 파일 `output/planner_physics_ko_v13.mp4`,86.27초/1080p30/문장 자막18개. 중앙 설명은 별도 목적의13개 전체 비트 중8개로 구성하며 기존 manifest가 단일 계약이다. [R12 비교](COMPARISON.md), [비교 플레이어](output/comparison.html).

R13 대본의 Edge TTS 전송을 사용자가 명시적으로 승인한 후 생성했다. 실측94.63초여서 반복 설명 두 문장을 재작성해 전송하려 했으나 자동 승인 검토가 수정 payload는 별도 승인 대상이라고 거절했다. 그 전송은 실행하지 않았다. 추가 전송을 하지 않고 기존 승인 음성의 문장 경계에서 B03뒤 반복 문장/B04E뒤 반복 문장을 제거했다. `trim_approved_audio.py`는 원본 음성을 로컬 보존하고 Whisper 단어 경계와 다음 문장 시작 사이에서 자른 뒤 이름 있는 읽기 과제용 tail을 확보한다. 전체86.27초로 맞추고 음성 manifest/자막을 다시 계산했다. 이는 음성 신호/정렬 확인이며 직접 청취를 대신하지 않는다. 이후 전체 tts재생성을 하면 로컬 trim을 다시 적용해야 하므로 해당 helper가 재현 경로다.

목표 방향은 source59실제 yaw와 source60lookahead/명령에서 얻는다. 회전 양수/왼쪽과 바퀴 목표 변환을 같은 config로 검증한다. 같은 속도 조건은 전진 목표 유지·회전 목표0의 수식 가정이고 새 solver 결과가 아니다. 물리 영상은R12/R10기존 실행을 읽으며 입력/응답 provenance와84관절 프레임 검증을 재사용한다. Blender 장면은 새로 변경/렌더하지 않았다. 원래 부품 주석/느린 재생 표시는 유지한다.

공유 키트 후보: 단일 활성 수식과 source값 이동/결과 dwell을 명시하는 helper, 실제 yaw기준 방향차이 도식. 파일럿 `reasoning_scene.py`에서만 구현했고 공유 키트는 수정하지 않았다. FFmpeg tpad duration은0.2형태로 써야 하며 .2가 인식되지 않은 오류를 로컬 수정했다. “이 숫자”처럼 지시어를 쓰는 문장은 그 대상을 실제 자막 구간 동안 유지해야 한다는 결함을 미리보기에서 수정했다.

## 검증 상태

기술/프레임과 정상 속도 재생·청취/초보자 이해는 구분한다. 새 음성은 직접 청취하지 못했고, R13초보자 응답은 아직 없다. 사용자에게46.3초 변경 핵심 미리보기를 보내 후속 피드백을 요청했다. 영상 업로드나 git push는 이번 요청 범위에 포함되지 않는다.

최종 검증: manifest --require-media PASS, Manim+재사용 Blender style PASS, staging13segments PASS, delivery --require-audio --fps30 --audio-manifest --caption-timing --full-decode PASS(86.27초/1080p30/18cues). 보호 입력10개 hash동일, 기존6V9 trace/물리 probe/제어기검증 PASS, 재사용84관절 프레임 검증 PASS. 프레임 리뷰와2개 수정 확인에서 잔여 blocker/high0. 출력 근거는 output/delivery_validation.json,output/render_review.json,output/run_review.json에 저장했다. 정상 속도 재생·청취와 신규 사람 이해 검토는 incomplete/not_assessed로 분리한다.
