# iRonCub 3 — 논문에서 제어 계산, 3D 비교 실험까지

주제별 폴더: `topics/04_ironcub3/`. 한국어 음성, Whisper 기반 자막, Manim 수식/데이터 흐름, Blender 자체 제작 로봇으로 구성한 약 5분 39초 영상입니다.

공개 영상: https://www.youtube.com/watch?v=uYOModSLyAQ

YouTube API에서 영상 처리 완료(`succeeded`), 공개(`public`), 자막 제공(`serving`), 썸네일 첨부를 확인했습니다. 최초 확인 중 자막 조회가 일시적으로 404를 반환했지만, 같은 영상/자막 ID로 재확인해 정상 제공 상태를 확인했습니다. 중복 업로드는 하지 않았습니다.

- 최종 영상: `output/ironcub3_education_ko.mp4`
- 논문 조사·주장별 근거·제작 범위: [research/brief.md](research/brief.md)
- 대본: [storyboard.json](storyboard.json)
- 모델: [simulation.py](simulation.py), 수치 데이터 `output/simulation.json`
- 화면: [lesson.py](lesson.py), [blender_scene.py](blender_scene.py)
- 재생 가능한 Blender 프로젝트: `output/blender/nominal.blend`, `mismatch.blend`
- 검증: `output/model_validation.json`, `output/blender/validation.json`, `output/validation.json`
- YouTube 패키지 및 결과: `publish/package.json`, `publish/receipt.json`

## 모델의 범위

공중에 떠 있는 평면 강체의 MPC 비교입니다. 질량 50 kg, 관성 8 kg·m², 유효 모멘트 암 0.32 m는 교육용 설정입니다. 상태를 정확히 아는 피드백을 사용하며, 다관절·UKF·접촉·열유동은 구현하지 않았습니다. 4개 제트는 좌우 두 쌍으로 묶이며 각 제트 힘은 0–250 N로 제한합니다. 화염 모양은 추력의 정성적 표시입니다.

제어기: 10 Hz, 3초 예측, 정확 이산화한 선형 예측 모델, 입력 제약이 있는 이차 비용 최적화. 식의 u는 평형 추력을 뺀 질량 정규화 입력입니다. 실제 계산 플랜트는 sin/cos를 포함한 평면 강체 방정식과 1차 추력 지연을 0.01초 RK4로 적분합니다. 모델 일치 τ=0.35초와 불일치 τ=0.77초를 동일 목표/제어기로 비교합니다. 무작위 과정이 없어 seed는 없습니다.

12초 전체 구간의 위치 RMSE는 각각 약 1.50/2.19 cm, 최대 절대 기울기는 0.85/10.58도입니다. **논문의 실험 수치나 iRonCub 제어기 재현이 아닙니다.** 논문은 비선형 2차 제트 모델과 다관절 시스템을 다룹니다. 이 영상은 그중 모델 불일치의 효과를 분리한 예시입니다.

3D 비교는 설명 시작에 첫 상태를 유지한 뒤 12초를 1배속으로 재생하고, 결과 해설 동안 마지막 상태를 유지합니다. `output/composition_timeline.json`에 시간 매핑을 저장합니다. Blender의 30 fps 프레임은 100 Hz 계산 표본 중 가장 가까운 값을 사용합니다.

## 재생성

프로젝트 루트의 uv 환경을 사용합니다. 이 주제 폴더에서:

```bash
uv run --offline python simulation.py
uv run --offline python prepare_audio.py tts
uv run --offline python prepare_audio.py captions
uv run --offline manim -qh --fps 30 --media_dir media lesson.py FlyingHumanoid
blender --background --factory-startup --python blender_scene.py -- --render
uv run --offline python finish_video.py
uv run --offline python validate_video.py
```

TTS는 네트워크가 필요합니다. `uv --offline`은 패키지 해석에만 적용됩니다. Blender 렌더는 기존 번호 프레임을 재사용하므로 장면을 수정했다면 해당 렌더 디렉터리를 새 버전으로 분리하거나 기존 생성 프레임을 명시적으로 재생성해야 합니다. 모델 데이터는 `simulation.py`가 다시 계산합니다. 로그인 정보는 프로젝트 밖 사용자 설정 폴더에만 저장합니다.

원문: https://arxiv.org/abs/2506.01125v1

공식 데모: https://github.com/ami-iit/paper_gorbani_mohamed_2025_ironcub3
