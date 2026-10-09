"""Trace-driven beat selection for the shared V9 manifest contract."""
from __future__ import annotations

from typing import Any


def _phases(topic: str, trace: dict[str, Any]) -> list[tuple[str, str, str, str]]:
    """Return only phases supported by this trace; each tuple is spoken/caption/object/focus."""
    p = trace.get("payload", {})
    if topic == "quantization":
        phases = [("입력 범위와 양자화 설정을 확인합니다.", "원래 값과 적용할 정밀도", "실수 입력", "Trace 입력 텐서와 비트 폭")]
        if any(op.get("id", "").startswith("quantize_") for op in trace.get("operations", [])):
            phases.append(("Scale과 zero point를 적용해 정수 코드로 바꿉니다.", "실수값 → 정수 코드", "양자화 과정", "실제 scale·zero point와 코드 매핑"))
        if any("dequantize" in op.get("id", "") for op in trace.get("operations", [])):
            phases.append(("정수 코드를 복원해 원래 값과 오차를 비교합니다.", "복원값과 절대 오차", "복원 결과", "동일 Trace의 값과 오차"))
        if p.get("activation_quantization") is not None:
            phases.append(("활성값도 별도 범위로 양자화해 가중치와 구분합니다.", "가중치와 활성값의 별도 변환", "두 입력 경로", "Trace의 두 tensor 결과"))
        return phases
    if topic == "nms":
        phases = [("입력 상자와 confidence 점수에서 시작합니다.", "후보 상자와 점수", "검출 후보", "합성 후보와 실제 NMS 실행 경계")]
        if not p.get("ids"):
            phases = [("입력 Trace에 검출 후보가 없습니다.", "입력 후보 0개", "빈 후보 집합", "빈 NMS 입력"),
                      ("비교할 후보가 없어 최종 유지 상자도 없습니다.", "NMS 결과: 후보 없음", "빈 결과 집합", "0개 입력의 실제 결과")]
            return phases
        if p.get("confidence_pass_ids") != p.get("ids"):
            phases.append(("confidence 기준 아래인 후보를 먼저 제거합니다.", "confidence threshold 적용", "필터링 상태", "Trace의 통과·제거 ID"))
        else:
            phases.append(("모든 후보가 confidence 기준을 통과했는지 확인합니다.", "confidence threshold 통과", "필터링 상태", "Trace의 실제 confidence 점수"))
        if p.get("steps"):
            phases.append(("가장 높은 점수부터 IoU를 비교해 겹친 후보를 억제합니다.", "winner와 IoU 비교 순서", "greedy NMS 상태", "실제 비교값과 억제 결정"))
        phases.append(("모든 비교 뒤 살아남은 상자를 확인합니다.", "최종 유지 후보", "결과 상자", "Trace의 kept IDs"))
        return phases
    if topic == "mcu_pid":
        return [("목표 속도와 encoder 측정값을 확인합니다.", "목표와 측정 피드백", "제어 입력", "Trace의 목표·encoder 표본"),
                ("오차에서 PID 항과 제한된 PWM이 계산됩니다.", "오차 → PID → PWM", "제어 출력", "실제 샘플 계산과 포화 범위"),
                ("모터 모델의 속도가 바뀌고 다음 측정으로 돌아옵니다.", "모터 응답과 encoder feedback", "닫힌 제어 루프", "같은 시각축의 상태와 측정값")]
    if topic == "self_attention":
        phases = [("입력 토큰을 Q, K, V 벡터로 각각 투영합니다.", "입력 토큰 → Q·K·V", "투영된 토큰 벡터", "Trace의 실제 투영 행렬과 벡터"),
                  ("Query와 각 Key의 내적으로 관련 점수를 계산합니다.", "QKᵀ 점수", "토큰 관계", "실제 행렬 곱 결과")]
        if p.get("causal_mask_enabled"):
            phases.append(("미래 위치를 가린 뒤 점수를 차원으로 나눕니다.", "Causal mask와 scaling", "가림이 적용된 점수", "Trace mask와 scale factor"))
        else:
            phases.append(("점수를 차원으로 나눕니다.", "Scaled dot product", "스케일된 점수", "Trace의 scale factor와 값"))
        phases.append(("각 질문 행의 점수를 softmax 확률로 바꿉니다.", "Row softmax 가중치", "attention weight", "실제 weight와 행 합 1"))
        phases.append(("가중치로 Value를 합쳐 각 토큰의 출력을 만듭니다.", "Attention weight × V", "문맥 출력", "Trace의 weighted sum"))
        return phases
    if topic == "robot_kinematics":
        return [("MuJoCo 모델과 물리 실행 조건을 확인합니다.", "모델·실행 조건", "H1 관절 상태", "Trace 모델·solver provenance"),
                ("PD 토크 입력에 따른 실제 관절 상태를 재생합니다.", "관절 상태의 시간 변화", "MuJoCo 관절 궤적", "기록된 qpos/qvel 표본"),
                ("같은 관절 상태에서 계산된 손 위치 궤적을 봅니다.", "끝단 위치와 관절 상태", "끝단 궤적", "동일 trace의 ee_pos")]
    # RAG uses its existing V10 manifest and renderer.
    raise ValueError(f"no trace-driven storyboard for {topic}")


def build_storyboard(topic: str, trace: dict[str, Any], visual_plan: dict[str, Any],
                     trace_path: str, *, render_mode: str,
                     measured_narration_seconds: float | None = None) -> dict[str, Any]:
    phases = _phases(topic, trace)
    payload = trace.get("payload", {})
    operations = trace.get("operations", [])
    complexity = max(1.0, len(operations) ** .5)
    if topic == "nms":
        complexity += min(3.0, sum(len(step.get("comparisons", [])) for step in payload.get("steps", [])) / 4)
    elif topic == "mcu_pid":
        complexity += min(3.0, len(payload.get("samples", [])) / 500)
    elif topic == "self_attention":
        complexity += min(2.0, len(payload.get("tokens", [])) / 4)
    elif topic == "quantization":
        complexity += min(2.0, len(payload.get("original", [])) / 8)
    base = [max(3.0, min(9.0, 3.2 + complexity * .7)) for _ in phases]
    if measured_narration_seconds is not None:
        if measured_narration_seconds <= 0:
            raise ValueError("measured narration duration must be positive")
        weights = [max(len(sentence), 1) for sentence, *_ in phases]
        total = sum(weights)
        durations = [measured_narration_seconds * weight / total for weight in weights]
        timing_basis = "measured_audio_total_proportional_allocation"
    else:
        durations = base
        timing_basis = "trace_complexity_estimate"
    beats = []
    for index, ((spoken, caption, obj, focus), duration) in enumerate(zip(phases, durations), 1):
        beats.append({"id": f"B{index:02d}", "text": spoken, "caption": caption,
                      "sec": round(duration, 3), "object": obj, "state_change": caption,
                      "focus": focus, "tool": "M",
                      "evidence": "model_execution" if topic == "robot_kinematics" else "toy_simulation",
                      "trace": trace_path})
    return {"language": "ko-KR", "format": "technical_preview" if render_mode == "preview" else "technical_render",
            "beats": beats, "storyboard_timing_basis": timing_basis,
            "estimated_duration_sec": round(sum(durations), 3),
            "narration_timing_status": "measured" if measured_narration_seconds is not None else "not_generated",
            "trace_id": trace.get("trace_id"), "visual_plan_kind": visual_plan.get("kind")}
