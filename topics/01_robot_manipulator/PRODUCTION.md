# 로봇 매니퓰레이터 교육 영상

평면 2관절 로봇팔의 각도와 위치를 FK·IK 수식으로 연결하고 시간 궤적까지 시각화합니다. 길이 1.0 m, 0.8 m의 교육용 예시이며, 동역학이나 물리 엔진을 사용하는 시뮬레이션은 아닙니다.

- 최종 길이: 346.90초, 약 5분 47초
- 화면: 1920×1080, 16:9, 30 fps
- 영상·음성: H.264 / AAC, 한국어 합성 내레이션
- 자막: Whisper base의 단어 타임스탬프 + 발화별 시간 구간 + 대본 기준 교정 문구
- 스타일: `manim-robotics-education-skill` 및 해당 shared style guide 적용

## 결과물

`output/robot_manipulator_education_ko.mp4`는 한국어 자막이 화면에 포함된 완성본입니다.

`output/robot_manipulator_clean_ko.mp4`는 동일한 한국어 음성을 포함하고 화면 자막만 제외한 버전입니다. 유튜브에서 자막을 켜고 끄게 하려면 이 파일을 업로드하고 `output/subtitles.ko.srt`를 자막으로 추가하세요.

`output/youtube_description.txt`에는 제목, 영상 설명, 챕터 타임스탬프가 있습니다. 업로드 자체는 수행하지 않습니다.

## 코드 구성

- `storyboard.json`: 학습 목표, 장면별 시각 구성, 한국어 대본 48문장, 짧은 자막, 목소리와 속도
- `manipulator_video.py`: 단일 파일로 실행되는 Manim `VoiceoverScene`. 공통 좌표계·로봇·수식·텍스트 도우미와 12개 `chapter_*` 메서드. `fk`, `ik`, `jacobian`이 실제 계산을 담당합니다.
- `prepare_audio.py`: Edge TTS 발화 생성, 30 fps에 맞춘 WAV 길이 정렬, 전체 내레이션 결합, 로컬 Whisper 분석, SRT/VTT 출력
- `finish_video.py`: 자막 ASS 생성, 음량 정규화, 최종 MP4 및 자막 없는 MP4, 유튜브 챕터 설명 생성
- `validate_lesson.py`: FK/IK 수치 검증, 야코비안 유한차분 검증, 장면·자막 타이밍, 최종 영상 규격 확인

## 실행 환경과 재생성

Python 3.12, `uv`, FFmpeg, LaTeX, dvisvgm, Cairo/Pango 및 NanumGothic 폰트가 필요합니다. Python 패키지는 `.venv`와 `uv.lock`으로 관리합니다. 현재 환경에서는 CPU용 PyTorch를 사용합니다.

```bash
cd /home/sang/make_simulation/topics/01_robot_manipulator
uv sync --locked

# 음성 합성에 인터넷 연결 필요. 변경되지 않은 발화는 해시로 캐시합니다.
uv run python prepare_audio.py tts

# base 모델이 캐시에 있으면 Whisper는 로컬에서 실행됩니다.
uv run python prepare_audio.py captions --model base

# 문법 및 기구학 검증
uv run python -m py_compile manipulator_video.py prepare_audio.py finish_video.py
uv run python validate_lesson.py

# 특정 장면만 빠르게 확인
LESSON_CHAPTER=ik uv run manim -ql --fps 30 manipulator_video.py ManipulatorLesson

# 전체 저해상도 미리보기
uv run manim -ql --fps 30 manipulator_video.py ManipulatorLesson

# 최종 1080p, 30 fps
uv run manim -qh --fps 30 manipulator_video.py ManipulatorLesson
uv run python finish_video.py
uv run python validate_lesson.py
```

`uv run --offline ...`은 의존성이 설치된 뒤 네트워크 없이 Python 환경을 실행할 때 사용할 수 있습니다. Edge TTS 호출 자체에는 여전히 네트워크가 필요합니다. 로컬 WAV가 준비되면 Manim 렌더와 Whisper 분석은 네트워크 없이 가능합니다.

## 수정 지점

대본·자막·음성 속도는 `storyboard.json`에서 바꿉니다. 대본이나 음성이 달라지면 `output/whisper_raw.json`을 삭제하고 음성 생성부터 다시 실행해 타임스탬프를 재계산하세요. 화면 배치·색상·글자 크기는 `manipulator_video.py`의 상단 상수와 `header`, `rig`, `item`에서 조정합니다.

링크 길이·예시 각도를 바꾸려면 수식의 숫자, 대본, 작업 공간, 목표 좌표도 함께 수정해야 합니다. 현재 수치와 설명은 1.0 m / 0.8 m 예시에 맞춰 작성됐습니다. `LESSON_CHAPTER`의 값은 storyboard의 `id`와 같습니다.

## 내용과 제작 참고 자료

- [Robotic Systems — Kinematics, Kris Hauser](https://motion.cs.illinois.edu/RoboticSystems/Kinematics.html): 링크 변환과 정기구학
- [Modern Robotics — Singularities](https://modernrobotics.northwestern.edu/nu-gm-book-resource/5-3-singularities/): 야코비안의 계수와 특이점
- [Manim 공식 uv 설치 안내](https://docs.manim.community/en/stable/installation/uv.html)
- [OpenAI Whisper 전사 구현](https://github.com/openai/whisper/blob/main/whisper/transcribe.py): 단어 타임스탬프
- [Edge TTS](https://github.com/rany2/edge-tts): 한국어 내레이션 합성

발화와 자막은 별도 자료로 제공되며, Whisper의 원시 인식 결과는 `output/whisper_raw.json`, 최종 교정 자막의 타이밍은 `output/caption_timing.json`에 보관합니다. SRT는 내레이션을 축약한 교육용 자막입니다.
