# Pilot 02 — DWB velocity choice

사용자 지시에 따라 YouTube 채널 ID는 `남상기`로 선택했고, 현재 API 조회 시 같은 채널 ID의 표시 이름은 `hinoonyaso`였다. 최초 업로드는 비공개였으며 이후 사용자가 공개로 변경해 원격 상태를 확인했다. 이후 기본값은 공개, 아동용 아님, 현실적 합성 콘텐츠 미포함이다. `publish/package.json`은 최초 업로드 당시 설정을 보존하고, `publish/visibility_update.json`은 공개 전환 결과를 기록한다. 채널별 향후 기본값은 사용자 로컬 `~/.config/make_simulation/youtube/publishing_defaults.json`에 있다.

이 파일럿은 “DWB는 다음 0.2초 동안 어떤 속도로 움직일지 어떻게 고를까?”를 다룬다. 7개 비트로 구성한 60–90초 한국어 교육 영상이며, 밝은 콘크리트 스튜디오의 실물 TurtleBot3 Waffle Pi와 복도/드럼 샷을 `pilots/01_teb_reference`와 맞추고, 계산은 연속적인 Manim 장면으로 보여준다.

**영상의 DWB는 교육용 DWB형 모형의 기록 재생이며, Nav2 DWB 실행 결과가 아니다.** 최종 납품본은 한국어 나레이션과 문장 단위 한국어 자막 트랙을 포함한 1920×1080, 30fps 영상이다. 로컬 산출물 경로는 `output/dwb_reference_ko.mp4`다.

## 흐름

| 비트 | 화면 변화 | 근거 |
|---|---|---|
| B01 | Blender의 TB3 영웅 샷에서 기준 탑뷰로 크레인 | DWB 단일 계산 예시의 시작 포즈 |
| B02 | 같은 시작 포즈에서 속도 후보 경로가 펼쳐짐 | DWB 후보 119개 중 점수 상위 8개를 표시 |
| B03 | 선택 후보를 따라 2초 예측과 드럼 여유 거리 표시 | 후보 rollout과 clearance 값 |
| B04 | 경로·목표·장애물·속도·회전 가중 비용이 실제 합계로 정리됨 | 선택 후보의 원본 비용 항목 |
| B05 | 여유 거리 0.09m 미만 후보를 제외하고 최소 유효 점수를 강조 | 80/119 유효, 선택 값 및 속도 쌍 |
| B06 | 2초 예측 중 첫 0.2초만 밝히고 로봇 포즈 갱신 | 선택 명령을 source constant-twist 식으로 0.2초 적분 |
| B07 | TB3가 같은 복도에서 드럼을 돌아 주행하고 예측과 누적 궤적이 갱신됨 | 원 trace의 `dwb_obstacle` 기록만 재생 |

기준 단일 계산 예시에서 선택 명령은 `v=0.53 m/s`, `ω=0.375 rad/s`다. 원본은 119개 후보 중 80개를 유효로 두고, 선택 후보의 점수는 7.334952691이다. 유효 기준은 이 교육용 모형에서 정의한 최소 여유 0.09m이며, 이 예시의 선택 후보 여유는 0.092034629m다. 이 가중 비용·임계값은 Nav2 DWB 기본 설정이라는 주장이 아니다.

## 데이터 경계와 정확성

- 입력 원본: `topics/09_dwb_teb/output/trace.json`. `extract_trace.py`는 이를 읽기만 하며 `topics/` 아래 파일은 수정하지 않는다.
- 변환 대상은 원본의 `hero.dwb`와 `runs.dwb_obstacle`뿐이다. 같은 파일에 들어 있는 TEB 결과는 읽거나 복사하지 않는다.
- `data/candidate_trace.json`에는 단일 DWB 선택 예시의 모든 후보 속도, 유효 여부, 가중 비용 항목, 점수, 2초 예측 포즈 및 선택 인덱스를 담는다. 무효 후보는 원본에 점수가 없으므로 `valid=0`과 함께 점수 `0`으로 직렬화한다. 화면과 설명에서는 `valid`가 0인 후보를 비용 0으로 해석하지 않는다.
- `data/drive_trace.json`은 DWB 장애물 주행의 결정 시점과 30fps 시각화 프레임을 담는다. 중간 프레임 포즈는 각 원본 0.2초 명령을 차동구동 constant-twist 식으로 적분한다. 명령·결정·비용은 원본 DWB 행에서만 가져온다.
- 두 V9 trace 모두 `core/shared-data/validate_trace.py`로 검사한다. 원본 trace는 파이프라인 전체에서 읽기 전용이다.
- 이 모형은 Nav2 패키지를 실행하거나 DWB critic/generator 동작을 재현하지 않는다. 실제 Nav2 플러그인·센서·로컬라이제이션·모터 지연을 주장하지 않는다.

## 구현 결정과 근거

- **Manim에서 계산을 설명하고 Blender에서 물리적 로봇/복도를 보여준다.** DWB의 후보 점수 비교는 숫자 변화가 핵심이라 원 reference의 연속 계산 장면 규칙을 따랐다. TB3 메시와 스튜디오 복도는 물리적 규모가 의미 있어 기존 `studio_utils.py`의 Waffle Pi 로더, 조명, 드럼, 복도, 밴드, 카메라, 궤적 함수를 사용했다.
- **한 장면 안에서 상태를 이어간다.** B02–B06은 동일한 로봇, 드럼, rollout 경로를 보존하고 강조 대상만 바꾼다. 이는 `ROUTING.md` 및 Director 스킬의 비트당 상태 전이 계약에 따른 선택이다.
- **주행 증거로 같은 원본의 DWB 장애물 run을 쓴다.** 새로운 DWB 결과를 만들지 않으면서 매 0.2초마다 실제 저장된 명령·포즈를 재생할 수 있다. 이 자료는 성능 비교가 아니다.
- **결과 주장은 교육용 모형으로 제한한다.** 주제 09 README는 DWB형 사용자 정의 가중 비용, 이상적 지도, 0.2초 제어 간격 등 실험 가정을 명시하며 실제 Nav2 DWB 실행이 아니라고 구분한다. 따라서 영상 내레이션과 이 README에도 동일 경계를 둔다.

## 번들/스킬 관찰과 승격 후보

- Director 스킬은 compact manifest와 상태 전이 원칙을 제공하지만, 이 주제에서 trace의 DWB 전용 필드를 manifest 비트/시각화 helper로 매핑하는 규약은 제공하지 않는다. 파일럿의 `extract_trace.py`가 그 변환을 담당한다.
- 키트에는 DWB 후보 점수·여유 기준·선택 명령을 시각화하는 Manim helper가 없다. 이 파일럿은 `manim_shot.py` 안에 `trajectory()`, `point_on()`, `cost_panel()`을 로컬 구현했다. 반복 사용을 확인한 후 후보 rollout fan/선택 결과 helper를 `manim_kit.py`로 옮길지 검토할 수 있다. 키트는 수정하지 않았다.
- Blender 경로 표시는 기존 `build_band()`, `key_band()`, `reveal_trajectory()`를 재사용했다. 별도 studio helper를 만들지 않았다.
- 첫 render-reviewer pass는 27–52초에서 비용 패널/속도 후보/선택값 겹침 high 결함을 보고했다. `manim_shot.py`에서 비트 전환 시 속도 목록을 치우고, 합계 패널 및 선택 행을 재배치해 preview targeted review PASS를 받았다. 최종본 검토에서 B06 60초의 자막이 “실행 구간 0.2s” 라벨을 가리는 high 결함이 추가로 발견돼 라벨 y 위치를 -3.25에서 -2.55로 올렸다. Manim을 다시 렌더·합성한 후 60, 62, 64, 66초 자막 오버레이 프레임과 B01–B07 시작 프레임을 재검토했고 blocker/high 없이 PASS했다.
- 현 환경에는 SoX 실행 파일이 없어 Manim이 경고했지만, 이 장면은 Manim voiceover/SoX를 사용하지 않는다. `edge-tts 7.2.8` 로컬 상수에 명시된 음성 연결 대상은 `wss://speech.platform.bing.com/consumer/speech/synthesize/readaloud/edge/v1`이다. 첫 전송 요청은 auto-review에서 거부됐고, 사용자가 별도로 승인한 뒤에만 TTS를 생성했다.
- 사용자가 나레이션 전송을 승인한 뒤 TTS는 83.33초를 생성했고, 첫 비트가 계획보다 1.97초 길어져 manifest의 실제 길이가 갱신됐다. 그 다음 최종 Blender 재렌더를 시작할 때 WSL interop의 `UtilBindVsockAnyPort` 오류가 발생했고 `cmd.exe` 진단도 실패했다. 이전 최종 샷을 확인해 B01의 크레인 종료 프레임과 B07의 마지막 주행 프레임을 남은 오디오 길이만큼 고정 연장했다. 이 로컬 산출물 단계는 Blender scene/kit을 변경하지 않으며, 최종 합성물을 별도로 프레임 검토한다.

## 렌더/검증 재현

프로젝트 루트 `/home/sang/make_simulation`에서:

```bash
uv run python pilots/02_dwb_reference/extract_trace.py
uv run python core/robotics-ai-visual-director-skill/templates/validate_visual_manifest.py pilots/02_dwb_reference/visual_manifest.json
uv run manim -ql --fps 15 --media_dir pilots/02_dwb_reference/output/manim pilots/02_dwb_reference/manim_shot.py DWBDissection
pilots/02_dwb_reference/render.sh S1 PREVIEW anim
pilots/02_dwb_reference/render.sh S3 PREVIEW anim
uv run python pilots/02_dwb_reference/assemble.py --preview
uv run python core/render-reviewer-skill/scripts/extract_review_frames.py pilots/02_dwb_reference/output/preview_picture.mp4 --out pilots/02_dwb_reference/output/review_frames
uv run python scripts/check_scene_style.py pilots/02_dwb_reference
```

최종 전달본 재생성 경로:

```bash
uv run python core/narration/prepare_audio.py tts pilots/02_dwb_reference/visual_manifest.json
uv run python core/narration/prepare_audio.py captions pilots/02_dwb_reference/visual_manifest.json
pilots/02_dwb_reference/render.sh S1 FINAL anim
pilots/02_dwb_reference/render.sh S3 FINAL anim
uv run manim -qh --fps 30 --disable_caching --media_dir pilots/02_dwb_reference/output/manim pilots/02_dwb_reference/manim_shot.py DWBDissection
uv run python pilots/02_dwb_reference/assemble.py
```

최종 생성 시 `assemble.py`가 `--require-media`, `--require-audio --fps 30 --audio-manifest ... --caption-timing ... --full-decode` 검증을 실행했다. 결과는 1920×1080, H.264, 오디오 1개, 30fps, 83.33초, 자막 cue 13개, 전체 디코드 PASS다.
