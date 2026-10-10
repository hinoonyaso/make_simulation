"""Trace-driven beat selection for the shared V9 manifest contract."""
from __future__ import annotations

from typing import Any


def validate_phase_contract(beats: list[dict[str, Any]], transitions: dict[str, Any]) -> list[str]:
    """Ensure each declared storyboard phase has exactly one renderer transition."""
    errors = []
    phase_ids = [beat.get("phase_id") for beat in beats]
    if any(not isinstance(value, str) or not value for value in phase_ids):
        errors.append("every storyboard beat requires a non-empty phase_id")
    if len(set(phase_ids)) != len(phase_ids):
        errors.append("storyboard phase_id values must be unique")
    declared = set(phase_ids)
    rendered = set(transitions)
    if declared - rendered:
        errors.append("renderer transitions missing for: " + ", ".join(sorted(declared - rendered)))
    if rendered - declared:
        errors.append("renderer phases absent from storyboard: " + ", ".join(sorted(rendered - declared)))
    if any(transitions.get(key) is None for key in declared & rendered):
        errors.append("every storyboard phase must have a concrete renderer transition")
    return errors


def _phases(topic: str, trace: dict[str, Any]) -> list[tuple[str, str, str, str, str]]:
    """Return trace-supported phases as (id, spoken, caption, object, focus)."""
    p = trace.get("payload", {})
    if topic == "quantization":
        phases = [("input", "입력 범위와 양자화 설정을 확인합니다.", "원래 값과 적용할 정밀도", "실수 입력", "Trace 입력 텐서와 비트 폭")]
        if any(op.get("id", "").startswith("quantize_") for op in trace.get("operations", [])):
            phases.append(("integer_mapping", "Scale과 zero point를 적용해 정수 코드로 바꿉니다.", "실수값 → 정수 코드", "양자화 과정", "실제 scale·zero point와 코드 매핑"))
        if any("dequantize" in op.get("id", "") for op in trace.get("operations", [])):
            phases.append(("dequantization", "정수 코드를 복원해 원래 값과 오차를 비교합니다.", "복원값과 절대 오차", "복원 결과", "동일 Trace의 값과 오차"))
        if p.get("activation_quantization") is not None:
            phases.append(("activation_quantization", "활성값도 별도 범위로 양자화해 가중치와 구분합니다.", "가중치와 활성값의 별도 변환", "두 입력 경로", "Trace의 두 tensor 결과"))
        return phases
    if topic == "nms":
        phases = [("candidates", "입력 상자와 confidence 점수에서 시작합니다.", "후보 상자와 점수", "검출 후보", "합성 후보와 실제 NMS 실행 경계")]
        if not p.get("ids"):
            phases = [("candidates", "입력 Trace에 검출 후보가 없습니다.", "입력 후보 0개", "빈 후보 집합", "빈 NMS 입력"),
                      ("final_result", "비교할 후보가 없어 최종 유지 상자도 없습니다.", "NMS 결과: 후보 없음", "빈 결과 집합", "0개 입력의 실제 결과")]
            return phases
        if p.get("confidence_pass_ids") != p.get("ids"):
            phases.append(("confidence_filter", "confidence 기준 아래인 후보를 먼저 제거합니다.", "confidence threshold 적용", "필터링 상태", "Trace의 통과·제거 ID"))
        else:
            phases.append(("confidence_filter", "모든 후보가 confidence 기준을 통과했는지 확인합니다.", "confidence threshold 통과", "필터링 상태", "Trace의 실제 confidence 점수"))
        if p.get("steps"):
            phases.append(("iou_comparison", "가장 높은 점수부터 IoU를 비교해 겹친 후보를 억제합니다.", "winner와 IoU 비교 순서", "greedy NMS 상태", "실제 비교값과 억제 결정"))
        phases.append(("final_result", "모든 비교 뒤 살아남은 상자를 확인합니다.", "최종 유지 후보", "결과 상자", "Trace의 kept IDs"))
        return phases
    if topic == "mcu_pid":
        return [("setpoint", "목표 속도와 encoder 측정값을 확인합니다.", "목표와 측정 피드백", "제어 입력", "Trace의 목표·encoder 표본"),
                ("motor_response", "모터 모델의 속도가 바뀌고 다음 측정으로 돌아옵니다.", "모터 응답과 encoder feedback", "닫힌 제어 루프", "같은 시각축의 상태와 측정값"),
                ("pid_terms", "오차에서 PID 항과 제한된 PWM이 계산됩니다.", "오차 → PID → PWM", "제어 출력", "실제 샘플 계산과 포화 범위")]
    if topic == "physics_oscillator":
        v = p["validation"]
        comparison = (f"SymPy 해석해와 SciPy 수치해의 최대 오차는 {v['max_abs_analytic_error_m']:.2g} m입니다."
                     if v.get("max_abs_analytic_error_m") is not None else
                     "외력이 작용하는 경우에는 닫힌 해를 단정하지 않고 수치 적분 결과를 봅니다.")
        return [("setup", "질량과 스프링, 댐퍼를 하나의 운동계로 둡니다.", "질량·스프링·댐퍼", "1자유도 물리 모델", "Trace에 기록된 m, c, k와 초기 상태"),
                ("equation", "힘의 합을 운동 방정식으로 적으면 m x 이계도함수 더하기 c x 일계도함수 더하기 k x는 F t입니다.", "m x'' + c x' + k x = F(t)", "힘에서 운동 방정식으로", "실행 설정에서 가져온 질량·감쇠·강성"),
                ("solution", "SymPy가 방정식을 표현하고 가능한 경우 초기 조건을 포함한 해석해를 구합니다.", "기호 해와 초기 조건", "해석해", "Trace의 실제 SymPy 해"),
                ("response", "SciPy가 같은 초기 조건에서 위치와 속도를 시간에 따라 적분합니다.", "수치 적분: 위치와 속도", "시간 응답", "solve_ivp DOP853 표본"),
                ("validation", comparison, "해석해 대 수치해 · 에너지", "수치 검증", "Trace 오차와 에너지 수지"),
                ("damping", "감쇠 계수가 작으면 진동이 오래가고, 임계감쇠는 진동 없이 빠르게, 과감쇠는 더 천천히 평형으로 돌아옵니다.", "감쇠 계수별 위치 응답", "감쇠 비교", "같은 질량·스프링·초기 조건에서 실행한 SciPy 감쇠 sweep")]
    if topic == "can_arbitration":
        p = trace.get("payload", {})
        winner = ", ".join(p.get("winners", [])) or "ACK 수신 노드 없음"
        return [("bus_setup", "ECU들이 같은 시각에 표준 CAN 프레임 송신을 요청합니다.", "노드 · 11비트 ID · 프레임", "CAN 버스", "Trace의 송신 요청과 식별자"),
                ("simultaneous_request", "모든 노드는 중재 구간에서 자신의 비트를 내보내고 버스의 상태를 읽습니다.", "동시 송신 요청", "중재 비트열", "동일한 시작 시각의 노드 요청"),
                ("arbitration", "dominant 0과 recessive 1이 만나면 1을 보낸 노드가 그 비트에서 송신을 멈춥니다.", "0이 1보다 우선", "비트 단위 중재", "Trace의 실제 ID 비트와 패배 위치"),
                ("frame_transmission", "승자는 남은 제어·데이터·CRC 비트를 전송하고 연속 비트에는 stuffing 규칙을 적용합니다.", "제어 · 데이터 · CRC · bit stuffing", "완성 프레임", "Trace의 실제 필드·CRC·stuff bit"),
                ("result", f"최종 승자는 {winner}입니다. 수신 노드가 있을 때만 ACK가 확인됩니다.", "승자와 ACK 결과", "전송 결과", "Trace의 receiver, ACK, 최종 비트열")]
    if topic == "motor_foc":
        return [("machine_setup", "데모 PMSM 파라미터와 FOC 제어기, 평균화된 인버터 모델을 설정합니다.", "PMSM · FOC · 평균 인버터", "모터와 제어 루프", "motulator 0.9 모델 파라미터와 한계"),
                ("three_phase_current", "모터 고정자에서 계산된 세 상 전류를 시간축으로 펼칩니다.", "실제 계산된 3상 전류", "3상 전류 파형", "motulator adaptive solver clock의 i_a, i_b, i_c"),
                ("dq_transform", "회전자 자속 기준으로 좌표를 돌려 d축과 q축 전류를 읽습니다.", "회전자 기준 d·q축 전류", "dq 변환 결과", "motulator machine state의 i_d, i_q"),
                ("current_control", "전류 벡터 제어기가 q축 전류 기준을 실제 피드백과 비교해 조절합니다.", "q축 전류 기준과 실제 피드백", "전류 제어 응답", "제어기 샘플 clock에 기록된 q축 기준·피드백"),
                ("speed_response", "속도 지령과 회전자 속도를 비교해 부하가 걸리기 전 응답을 봅니다.", "속도 지령과 실제 속도", "회전 속도 응답", "rad/s 기록과 동일 값의 rpm 환산"),
                ("load_disturbance", "지정한 시각에 부하 토크를 더하고 속도와 q축 전류의 변화를 확인합니다.", "부하 계단 입력과 회복", "부하 외란 응답", "Trace의 부하 토크, i_q, 속도")]
    if topic == "self_attention":
        phases = [("input_projection", "입력 토큰을 Q, K, V 벡터로 각각 투영합니다.", "입력 토큰 → Q·K·V", "투영된 토큰 벡터", "Trace의 실제 투영 행렬과 벡터"),
                  ("qk_scores", "Query와 각 Key의 내적으로 관련 점수를 계산합니다.", "QKᵀ 점수", "토큰 관계", "실제 행렬 곱 결과")]
        if p.get("causal_mask_enabled"):
            phases.append(("scaling_mask", "미래 위치를 가린 뒤 점수를 차원으로 나눕니다.", "Causal mask와 scaling", "가림이 적용된 점수", "Trace mask와 scale factor"))
        else:
            phases.append(("scaling_mask", "점수를 차원으로 나눕니다.", "Scaled dot product", "스케일된 점수", "Trace의 scale factor와 값"))
        phases.append(("softmax", "각 질문 행의 점수를 softmax 확률로 바꿉니다.", "Row softmax 가중치", "attention weight", "실제 weight와 행 합 1"))
        phases.append(("weighted_value", "가중치로 Value를 합쳐 각 토큰의 출력을 만듭니다.", "Attention weight × V", "문맥 출력", "Trace의 weighted sum"))
        return phases
    if topic == "robot_kinematics":
        return [("robot_setup", "MuJoCo 모델과 물리 실행 조건을 확인합니다.", "모델·실행 조건", "H1 관절 상태", "Trace 모델·solver provenance"),
                ("joint_state", "PD 토크 입력에 따른 실제 관절 상태를 재생합니다.", "관절 상태의 시간 변화", "MuJoCo 관절 궤적", "기록된 qpos/qvel 표본"),
                ("end_effector_motion", "같은 관절 상태에서 계산된 손 위치 궤적을 봅니다.", "끝단 위치와 관절 상태", "끝단 궤적", "동일 trace의 ee_pos")]
    if topic == "object_detection":
        return [("candidates", "실제 모델이 이미지에서 낸 전체 후보를 확인합니다.", "실제 모델 출력과 표시 후보", "원본 이미지와 후보 상자", "YOLO trace의 raw count와 이미지 좌표"),
                ("confidence_filter", "confidence 기준으로 통과할 후보와 제외할 후보를 가릅니다.", "confidence filtering", "신뢰도 필터 상태", "실제 점수와 기준값"),
                ("iou_comparison", "같은 클래스에서 겹친 상자를 IoU로 비교합니다.", "class-aware IoU NMS", "상자 억제 과정", "실제 NMS 비교 기록"),
                ("final_result", "런타임 결과와 대조한 최종 검출을 표시합니다.", "최종 검출 결과", "최종 상자", "trace 검증을 통과한 출력")]
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
        weights = [max(len(sentence), 1) for _, sentence, *_ in phases]
        total = sum(weights)
        durations = [measured_narration_seconds * weight / total for weight in weights]
        timing_basis = "measured_audio_total_proportional_allocation"
    else:
        durations = base
        timing_basis = "trace_complexity_estimate"
    beats = []
    for index, ((phase_id, spoken, caption, obj, focus), duration) in enumerate(zip(phases, durations), 1):
        beats.append({"id": f"B{index:02d}", "phase_id": phase_id, "text": spoken, "caption": caption,
                      "sec": round(duration, 3), "object": obj, "state_change": caption,
                      "focus": focus, "tool": "M",
                      "evidence": "model_execution" if topic == "robot_kinematics" else "toy_simulation",
                      "trace": trace_path})
    return {"language": "ko-KR", "format": "technical_preview" if render_mode == "preview" else "technical_render",
            "beats": beats, "storyboard_timing_basis": timing_basis,
            "estimated_duration_sec": round(sum(durations), 3),
            "narration_timing_status": "measured" if measured_narration_seconds is not None else "not_generated",
            "trace_id": trace.get("trace_id"), "visual_plan_kind": visual_plan.get("kind")}
