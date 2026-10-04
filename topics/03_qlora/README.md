# QLoRA Manim 교육 영상

개선판 v2: **4분 58초, 1920×1080, 30 fps**, 한국어 내레이션과 교정 자막을 포함합니다. LoRA 행렬 분해 → 병렬 순전파 → 어댑터 업데이트 → NF4 → Double Quantization → Paged Optimizer → 메모리 비교 → 적용과 요약 순서입니다.

## 결과물

빠른 세로 버전은 `shorts/output/qlora_shorts_ko.mp4`입니다. 58초, 1080×1920, 30 fps, 본편 음성 대비 1.3배 템포이며 화면은 세로에 맞춰 다시 구성했습니다. 소스와 실행법은 `shorts/README.md`에 있습니다.

- `output/qlora_education_ko_v2.mp4`: 음성 + 화면에 포함된 한국어 자막
- `output/qlora_clean_ko_v2.mp4`: 같은 음성, 화면 자막 없음. YouTube에서 SRT를 별도로 올려 자막을 켜고 끌 수 있습니다.
- `output/subtitles.ko.srt`, `output/subtitles.ko.vtt`: Whisper 구간 분석 + 대본 기준 교정 자막 32개
- `output/narration.wav`, `output/narration.ko.txt`: 음성과 대본
- `output/youtube_description.txt`: 제목, 설명, 9개 챕터, 출처
- `output/thumbnail_v2.png`: YouTube용 벡터 썸네일
- `output/review_v2.png`: 장면별 검수용 모음
- `output/validation_v2.json`, `output/toy_training.json`: 미디어 검증 결과와 실제 계산 데이터

## 재생성

공통 uv 환경은 두 단계 위 프로젝트 루트의 `pyproject.toml`, `uv.lock`, `.venv`를 사용합니다. Manim CE, manim-voiceover, edge-tts, openai-whisper가 설치되어 있습니다. 시스템 패키지는 FFmpeg, LaTeX/dvisvgm, Cairo/Pango, NanumGothic이 필요합니다.

기존 음성과 자막을 사용한 최종 렌더:

```bash
cd /home/sang/make_simulation/topics/03_qlora
uv run --offline python -m py_compile qlora_video_v2.py render.py finish_video.py
uv run --offline python render.py
```

빠른 미리보기 및 한 장면만 확인:

```bash
uv run --offline python render.py --preview
LESSON_CHAPTER=parallel uv run --offline manim -ql --fps 30 --media_dir media_v2 qlora_video_v2.py QLoRAEnhanced
```

대본 변경 후 음성부터 다시 생성:

```bash
uv run --offline python render.py --prepare-audio
```

`--offline`은 uv 의존성 해석에 적용됩니다. Edge TTS 음성 합성에는 네트워크가 필요하며, Whisper base 모델은 로컬 캐시에서 CPU로 실행합니다. TTS는 대본·목소리·속도, Whisper 결과는 음성 해시를 기준으로 재사용합니다. 이미 분석한 발화의 음성 인식 결과를 재사용하고, 나머지는 확정된 대본을 Whisper의 단어 정렬 기능으로 음성에 맞춥니다. 발화별 결과를 저장해 중단 후에도 이어서 처리할 수 있습니다.

썸네일과 검수 이미지:

```bash
uv run --offline manim -s -qh --media_dir media_v2 qlora_video_v2.py QLoRAThumbnail
cp media_v2/images/qlora_video_v2/QLoRAThumbnail_ManimCE_v0.21.0.png output/thumbnail_v2.png
uv run --offline python review_frames.py output/qlora_education_ko_v2.mp4
```

## 코드 구조와 수정 지점

`qlora_video_v2.py` 하나에 장면, 수식, 행렬/도식 생성기, NumPy 학습 시뮬레이션을 모았습니다. `QLoRAEnhanced`는 `VoiceoverScene`을 사용하고, `beat()`가 프레임에 맞춘 발화 길이만큼 장면을 유지합니다. 음성은 `prepare_audio.py`, 자막 합성과 챕터는 `finish_video.py`, 검사와 프레임 추출은 별도 스크립트가 담당합니다.

- `storyboard.json`: 학습 목표, 9개 장면, 32개 발화, 짧은 자막, 목소리와 속도
- `qlora_video_v2.py`의 색상 상수·`text()`·`card()`: 폰트, 크기, 색상
- `chapter_*()` 메서드: 화면 배치와 움직임
- `toy_training()`: 재현 가능한 작은 선형 회귀 학습. seed 17, rank 2, SGD 60회, A 무작위·B 0 초기화
- `finish_video.py`의 ASS 스타일: 자막 글꼴과 위치

## 정확성과 범위

기본 가중치의 양자화 코드와 스케일은 고정합니다. 실제 계산은 `dequant(W₄)x + (α/r)B(Ax)`의 두 경로를 더합니다. 동결은 입력이나 앞쪽 층에 필요한 기울기까지 끊는다는 뜻이 아닙니다.

NF4 점은 실제 코드북 값이며, 분포 곡선과 가중치 표본은 설명용입니다. 학습 그래프는 4×4 선형 회귀를 실제로 계산한 결과로, LLM 벤치마크가 아닙니다. Paged Optimizer 장면은 상태 페이지의 이동을 단순화한 개념도이며 CPU/GPU 메모리를 직접 측정한 결과가 아닙니다. 7B의 14 GB / 3.5 GB는 가중치 표현만의 십진 용량이며 전체 학습 VRAM과 다릅니다.

`validate_video.py`는 전체 디코딩, 영상/음성 길이, 해상도와 코덱, 챕터 9개, 자막 겹침, 발화/장면 누적 오차, 예제 손실 감소를 확인합니다. 오디오는 -16 LUFS 목표로 정규화합니다.

이전 무음 v1과 소스는 `archive/v1/`에 보존했습니다. 주제별 폴더는 `topics/03_qlora/`를 유지합니다.

참고 자료:

- QLoRA 논문: https://arxiv.org/abs/2305.14314
- Hugging Face bitsandbytes: https://huggingface.co/docs/transformers/quantization/bitsandbytes
- Hugging Face PEFT LoRA: https://huggingface.co/docs/peft/package_reference/lora
- Hugging Face PEFT quantization: https://huggingface.co/docs/peft/developer_guides/quantization
