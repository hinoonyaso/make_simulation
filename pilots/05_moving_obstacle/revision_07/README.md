# revision 07 — 제어 원인과 물리 반응을 더 잘 보여주기

## 의도와 결정

강화한 Director/Manim/Blender/Reviewer/편집 스킬을 현재 회피 영상에 적용하는 비교 렌더다. 사용자가 승인한 설명 흐름과 B01–B05 나레이션을 유지했다. B04는 기존 추상 피드백 도식 앞에 **기록된 방향 차이 → 회전 명령 → 실제 회전**을 보여준다. B01 접촉, B05 회피·목표 접근은 가까운 고정 시점으로 관찰한다. B06의 반복 결과 설명을 줄여 측정 길이는 13.733초→8.300초, 총 72.200초→66.767초다. 고정 길이·컷 수가 아닌 실제 관찰 과제에 따라 시점을 선택했다. 자막 외곽선도 줄여 화면을 덜 가린다.

새 물리 실험의 성능 향상을 주장하지 않는다. 기존 revision_06의 검증된 Bullet 실행을 **읽기 전용 데이터 참조**로 사용해 물리 결과를 같게 유지하고 연출 변화만 비교한다. 원본 solver 실행은 모터 입력에 의해 계산되었으며, 이번 Blender 렌더 키프레임은 그 결과의 재생이다. **교육용 A* + heading/lookahead 제어 모형이며 실제 Nav2/DWB·실기·센서 시뮬레이션이 아니다.** 정적 드럼은 처음부터 존재하고 2초에 이상화한 지도 정보만 추가된다.

## 증거와 데이터 경계

Manifest의 trace와 comparison_trace는 `../revision_06/data/baseline_planner_on.json` 및 OFF를 가리킨다. 기본/동일 반복/substeps 16의 6개 기록을 기존 검증기로 재확인했다(`output/run_validation.txt`). 물리 설정·근사·초기 목표 overshoot 수정·검증 기준은 `../revision_06/README.md`, runner `../revision_06/physics_closed_loop.py`, `planner.py`에 있다. 전체 동역학·불확실성의 근거를 새로 복제하지 않는다.

B04의 기록 t=2.000s 명령은 직전 solver t=1.967s pose에서 계산되므로, 방향 화살표와 오차는 ROWS[59], lookahead/명령은 ROWS[60]에서 가져온다. 방향 차이는 약 30.50°(화면 반올림 31°), 회전 명령 +1.0rad/s다. 이는 `clip(2.2*heading_error, −1,1)`의 명령이며 달성된 각속도를 뜻하지 않는다. 이후 표시되는 위치와 yaw는 실제 solver 출력이다. 명령을 입력했으니 즉시 해당 속도/방향으로 움직였다고 주장하지 않는다. 비교는 계획과 추종 제어를 함께 바꾼 조건이며 둘 중 하나의 독립 효과를 분리한 실험이 아니다.

## 시점과 시간

- B01: 전체 공간에서 출발을 확인한 후 표시 6.1초에 접촉 부근으로 컷. 물리 OFF 0→8초의 기존 재생을 유지한다.
- B02/B03: 기존 지도 정보 갱신·금지 영역·새 참고 경로 설명을 유지한다.
- B04: t2 입력 상태를 설명 동안 잠시 유지한 후 실제 t2→3.5 회전을 먼저 보여주고 t12까지 진행한다. solver 시간은 바꾸지 않고 설명용 재생 시간을 변경했다.
- B05: 같은 ON 실행의 t2→30 재생. 표시 0→3초 전체 경로, 3→9.1초 회전/드럼 여유, 9.1초 이후 목표 접근/정지의 고정 시점. 같은 장소·진행 방향을 유지하는 컷이며 가짜 기하학적 전환은 아니다.
- B06: 같은 전체 카메라에서 OFF/ON의 실제 t30 끝 상태를 짧게 비교하고 모델 범위를 명시한다. 전체 실제 과거 궤적을 표시한다.

매 Blender 프레임의 solver index/source time/view는 `output/blender/source_mapping.json`. 초록은 참고 경로, 파랑은 실제 과거 궤적이다. 휠 quaternion도 같은 solver 기록을 사용한다. 표시 프레임마다 실제 샘플을 선택하며 새 운동학 궤적을 만들지 않았다. 카메라 조명은 기존 bright studio/EEVEE/AgX, 실제 TurtleBot3 mesh를 유지한다.

## 제작·키트와 스킬 관찰

`visual_manifest.json`이 유일한 비트 계약이다. 기존 B01–B05 TTS/정렬 캐시를 재사용하고 짧아진 B06만 기존 승인 범위의 Edge TTS로 생성했다. 제한된 네트워크 실행은 대기 상태여서 해당 TTS 프로세스만 종료 후 허용된 네트워크로 재실행했다. 자막 생성은 TTS manifest 완료 후 실행해야 한다. 처음 일찍 실행한 captions는 manifest 부재로 실패했고, 음성 완료 후 재실행했다.

공용 `studio_utils.py`, `manim_kit.py`, topics, revision_06의 렌더/장면 소스를 수정하지 않는다. 이번에 로컬로 만든 후보는 (1) 기록된 이전 입력 pose/명령과 현재 반응을 연결하는 제어 설명, (2) event 기반 고정 카메라 선택과 시간 매핑, (3) solver 휠/과거 궤적/최종 정지 상태 재생이다. 키트로 옮기기 전에 여러 사례에서 필요성과 좌표 일관성을 확인해야 한다.

Blender의 curve 데이터 애니메이션은 object 애니메이션 제거와 별개이므로 최종 비교 전에 둘 다 제거하고 reveal=1을 명시한다. revision_06에서 발견한 궤적 잘림 방지를 유지했다. Resolve MCP가 제공되지 않아 FFmpeg로 조립하고 기존 sequence staging/delivery gate를 사용한다. 내부 자막 스트림 없이 굽는 문장 자막과 외부 SRT를 제공한다.

## 검토 상태

실제 핵심 미리보기 프레임을 확인했고 오디오·문장 타이밍·30fps·전체 decode gate가 PASS했다. 확대 컷의 표기가 로봇과 겹쳐 B05의 안내/색 설명은 처음 3초의 전체 시점에서만 표시하도록 정리했다. 최종 렌더와 기술 게이트·프레임 검토를 완료했다. 결과는 아래에 기록한다. 정상 속도 재생·직접 청취는 도구에서 지원되지 않으므로, 사용자 피드백이 없는 범위는 교육적 acceptance `incomplete`로 구분한다. 스킬 강화만으로 다른 채널과 동급 품질을 주장하지 않는다.

도입 전체 시점의 변경 없는 frame 1–182는 revision_06의 1080p30 프레임을 그대로 복사했다. `--resume-production`은 frame 183–698을 같은 렌더 조건(48 samples)에서 새로 렌더한다. 전체 재생을 재현하려면 옵션 없이 실행하면 된다. 핵심 미리보기는 `--critical`로 B05를 540p30/16 samples 렌더하고, Manim 핵심 구간과 합친다. 최종 전체 프레임은 1080p로 다시 확인한다.

사용자는 새 26.1초 유성 핵심 미리보기의 정상 속도 설명·컷 연결을 “자연스러움”으로 확인했다. 전체 영상 청취·최종 결과 승인을 대신하는 것으로 확대 해석하지 않는다.

## 최종 전달과 게이트

최종 영상 `output/planner_physics_ko_v7.mp4`: **1920×1080, 30fps, H.264/AAC, 66.77초, 한국어 문장 자막 14개**. 외부 자막 `output/final.ko.srt`. 실제 검증 결과 `output/delivery_validation.txt`, 파일 식별 `output/delivery_identity.json`.

- 재사용 기본/동일 반복/세밀 계산 6개 trace와 물리 acceptance: PASS (`output/run_validation.txt`). 새 물리 실행을 했다는 의미는 아니다.
- `validate_visual_manifest.py --require-media`: PASS. B01의 primary trace는 실제 OFF, 비교 참조는 ON으로 정리했다. renderer도 같은 OFF 경로를 primary에서 읽도록 맞췄으며 렌더 결과의 입력 값은 그대로다.
- `scripts/check_scene_style.py revision_07`: Manim/Blender 모두 PASS.
- `stage_segments.py`: PASS, 6개 구간.
- `validate_delivery.py --require-audio --fps 30 --audio-manifest assets/audio/manifest.json --caption-timing output/caption_timing.json --full-decode`: PASS.
- 모든 698개 Blender PNG를 header 검사하여 1920×1080 확인. 낮은 해상도 미리보기 프레임이 최종 렌더에 남지 않았다.
- render-reviewer 기본 1회와 표기 수정 확인: 실제 핵심/합본 프레임 8/9.15/35.6/38.8/47.7/53.5/56.7/61/65초의 접촉·제어 전/후·회피/목표·결말을 검사. **검토 범위에서 남은 blocker/high 0개**. 기록은 `output/final_review.json`.
- 사용자 정상 속도 확인은 26.1초 핵심 발췌본의 설명/컷 연결에 한정. 전체 합본의 직접 정상 속도 재생·청취는 여전히 `incomplete`로 기록한다. 프레임/기술 PASS를 완전한 교육적 승인으로 부풀리지 않는다.

재실행은 `prepare_audio.py tts|captions visual_manifest.json` → `reasoning_scene.py ClosedLoopReasoning`을 Manim 1920×1080/30fps로 렌더 → 설치된 Windows Blender에서 `blender_scene.py` 렌더 → `uv run python pilots/05_moving_obstacle/revision_07/assemble.py`. Manim media_dir은 이 폴더의 `output/final_render`를 지정한다. 필요한 원본 데이터와 물리 provenance는 revision_06을 함께 보존해야 한다.
