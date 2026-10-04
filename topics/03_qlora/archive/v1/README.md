# QLoRA Manim 교육 영상

QLoRA를 전체 파인튜닝 → LoRA → 4-bit frozen base → gradient flow → NF4·double quantization·paged optimizer → 구현 설정 순으로 설명합니다.

```bash
cd /home/sang/make_simulation/topics/03_qlora
uv run --offline python -m py_compile qlora_video.py render.py
uv run --offline python render.py
```

결과는 `output/qlora_education_ko.mp4`입니다. 화면 구성은 `qlora_video.py`, 장면 순서와 설명은 `storyboard.md`에서 수정합니다.

현재 파일은 한국어 화면 설명을 포함하고 음성 트랙은 무음으로 둡니다. 온라인 음성 합성 접근이 가능해지면 한국어 내레이션을 추가할 수 있습니다.

참고 자료:

- QLoRA 논문: https://arxiv.org/abs/2305.14314
- Hugging Face bitsandbytes: https://huggingface.co/docs/transformers/quantization/bitsandbytes
- Hugging Face PEFT LoRA: https://huggingface.co/docs/peft/package_reference/lora
- Hugging Face PEFT quantization: https://huggingface.co/docs/peft/developer_guides/quantization
