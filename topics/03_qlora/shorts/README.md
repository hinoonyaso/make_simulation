# QLoRA 빠른 쇼츠 버전

58초, 1080×1920 세로 9:16, 30 fps. 본편의 핵심 8개 발화를 추려 1.3배 템포로 편집하고, 화면은 세로에 맞춰 Manim으로 새로 구성했습니다. `atempo=1.3`으로 목소리 높이를 유지했고 본편의 Whisper 자막 시간을 같은 비율로 변환했습니다.

- `output/qlora_shorts_ko.mp4`: 한국어 음성·화면 자막 포함 완성본
- `output/subtitles.ko.srt`: 별도 자막
- `output/youtube_description.txt`: 제목과 설명
- `output/validation.json`: 해상도·길이·자막·동기화·전체 디코딩 검사
- `storyboard.json`: 선택한 본편 발화, 새 자막과 장면 순서
- `short_video.py`: 세로 화면용 Manim 소스 전체
- `finish_short.py`: 자막 합성과 검증

```bash
cd /home/sang/make_simulation/topics/03_qlora/shorts
uv run --offline manim -qh -r 1080,1920 --fps 30 --media_dir media short_video.py QLoRAShort
uv run --offline python finish_short.py
```

저장된 음성 클립으로 오프라인 재생성이 가능합니다. `scene_0`~`scene_7`에서 배치와 움직임을, `finish_short.py`의 ASS 스타일에서 자막 크기와 위치를 수정합니다. 본편 원본은 상위 폴더에 유지합니다.
