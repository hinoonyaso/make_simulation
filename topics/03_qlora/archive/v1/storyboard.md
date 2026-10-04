# QLoRA 교육 영상 스토리보드

학습 목표: QLoRA가 4-bit로 저장한 동결 기본 모델을 통과해 BF16 LoRA 어댑터만 학습함으로써 메모리를 줄이는 원리를 이해한다.

형식: 16:9, 1920×1080, 30 fps, 약 2분 24초, 밝은 인포그래픽 스타일. 화면의 수치는 구조 이해용 예시이며 실제 학습 메모리는 모델·배치·길이·옵티마이저에 따라 달라진다.

1. 문제: 전체 파인튜닝은 모든 가중치와 gradient·optimizer state를 저장한다.
2. LoRA: ΔW=BA라는 저랭크 경로만 학습한다.
3. QLoRA: 동결 기본 가중치를 NF4 4-bit로 저장하고 계산할 때 BF16으로 dequantize한다.
4. 역전파: gradient는 기본 경로를 통과하지만 W4 자체는 갱신하지 않고 A와 B만 갱신한다.
5. 세 가지 장치: NF4, double quantization, paged optimizer.
6. 메모리: 7B weight-only 예시로 FP16 14 GB 대 4-bit 3.5 GB. 실제 메모리에는 activation·adapter·workspace가 추가된다.
7. 구현: bitsandbytes 4-bit 설정, `prepare_model_for_kbit_training`, `target_modules="all-linear"`.
8. 요약: dataset → frozen 4-bit base + trainable LoRA → adapter checkpoint → task model.

근거: QLoRA 논문(Dettmers et al., NeurIPS 2023), Hugging Face Transformers bitsandbytes 문서, PEFT LoRA/quantization 문서.
