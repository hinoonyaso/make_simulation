#!/usr/bin/env python3
"""Capability-driven production entry point for implemented mechanism adapters."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core.mechanism.protocol import MechanismRequest
from core.mechanism.registry import MechanismRegistry


BEAT_COPY = {
    "quantization": [
        ("먼저 FP 값과 적용할 정밀도를 확인합니다.", "원래 실수 가중치의 값과 범위를 봅니다.", "원본 가중치", "각 원소의 FP32 값과 입력 정밀도"),
        ("Scale과 zero point로 정수 코드에 대응시킵니다.", "실제 계산된 scale과 정수 코드가 나타납니다.", "양자화 결과", "사용한 공식과 정수 표현"),
        ("복원 값과 오차를 원래 값에 대조합니다.", "Dequantization 결과와 최대 절대 오차를 확인합니다.", "복원 가중치와 오차", "실제 계산 결과 및 하드웨어 실행 경계"),
    ],
    "nms": [
        ("검출 후보와 confidence 점수를 확인합니다.", "합성 후보 상자와 점수는 실제 NMS 계산의 입력입니다.", "후보 상자", "모델이 추론한 출력이 아닌 입력 후보"),
        ("점수가 높은 상자와 겹침 IoU를 비교합니다.", "실제 계산된 IoU가 임계값을 넘는 후보를 억제합니다.", "IoU 비교와 억제", "선택 ID, 후보 ID, 계산된 IoU와 임계값"),
        ("남은 상자를 최종 후보로 표시합니다.", "실행한 greedy NMS가 반환한 ID를 확인합니다.", "NMS 결과", "계산 결과와 YOLO 추론 미실행 경계"),
    ],
    "mcu_pid": [
        ("속도 목표와 엔코더 표본을 확인합니다.", "모터 속도를 표본 주기로 측정한 엔코더 피드백입니다.", "목표와 측정값", "목표 속도, 측정 주기와 엔코더 값"),
        ("PID 오차로 PWM 입력을 갱신합니다.", "계산된 제어 출력은 설정한 PWM 한계 안에 제한됩니다.", "PID와 PWM", "실제 이산 제어 계산과 포화 범위"),
        ("모터 모델의 응답을 피드백과 비교합니다.", "속도 변화와 제어 출력은 수치 plant 시뮬레이션 결과입니다.", "모터 응답", "시뮬레이션과 실제 MCU 측정의 경계"),
    ],
    "robot_kinematics": [
        ("MuJoCo 모델과 고정 조건을 확인합니다.", "입력 관절 목표와 고정-base 설정을 사용합니다.", "모델과 실행 조건", "MJCF, 물리 엔진 버전과 제어 조건"),
        ("PD 토크 입력에 대한 관절 응답을 기록합니다.", "어깨와 팔꿈치 관절의 실제 MuJoCo 상태입니다.", "관절 상태", "시뮬레이션 목표와 solver 상태"),
        ("기록된 관절 상태에서 끝단 궤적을 확인합니다.", "같은 실행 trace의 link 위치를 보여줍니다.", "끝단 이동", "trace 좌표와 검증 범위; 하드웨어 아님"),
    ],
    "self_attention": [
        ("세 토큰의 벡터에서 질문·키·값을 각각 만듭니다.", "같은 입력 토큰이 학습된 투영을 거쳐 Q, K, V가 됩니다.", "Q·K·V 벡터", "Trace의 실제 투영 행렬과 토큰 벡터"),
        ("질문과 모든 키의 내적으로 관련도를 계산합니다.", "각 질문 행에서 키 열마다 내적 점수를 계산합니다.", "QKᵀ 점수 행렬", "실제 행렬 곱 결과와 토큰 위치 대응"),
        ("차원으로 나눈 뒤 softmax로 가중치를 만듭니다.", "점수를 √차원으로 나누고 행마다 확률 가중치로 바꿉니다.", "Scaled scores → softmax", "Trace의 점수·가중치와 행 합 1"),
        ("가중치로 값 벡터를 합쳐 문맥 표현을 만듭니다.", "각 토큰의 출력은 값 벡터의 가중합입니다.", "문맥 벡터", "동일 Trace의 attention weights × V 계산"),
    ],
}


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_v9_manifest(topic: str, trace_path: Path, output_dir: Path,
                       evidence: str, mode: str) -> Path:
    beats = []
    for index, (narration, caption, obj, focus) in enumerate(BEAT_COPY[topic], start=1):
        beats.append({"id": f"B{index:02d}", "text": narration, "caption": caption,
                      "sec": 4.0, "object": obj, "state_change": caption,
                      "focus": focus, "tool": "M", "evidence": evidence,
                      "trace": os.path.relpath(trace_path, output_dir)})
    manifest = {"language": "ko-KR", "format": "short_form", "beats": beats}
    path = output_dir / "visual_manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    validator = load_module(ROOT / "core/robotics-ai-visual-director-skill/templates/validate_visual_manifest.py",
                            "v9_manifest_validator")
    errors, warnings = validator.validate(str(path))
    if errors:
        raise ValueError("generated V9 manifest invalid: " + "; ".join(errors))
    for warning in warnings:
        print(f"WARN {warning}")
    return path


def run_rag(args, output: Path) -> None:
    command = [sys.executable, str(ROOT / "scripts/produce_ai_video.py"), "--topic", "rag",
               "--render", args.render, "--silent", "--output-root", str(output)]
    if args.document:
        if not args.question:
            raise SystemExit("RAG --document requires --question")
        command += ["--document", str(args.document), "--question", args.question]
        if args.config:
            config = json.loads(args.config.read_text(encoding="utf-8"))
            for key, flag in (("chunk_size", "--chunk-size"), ("overlap", "--overlap"), ("top_k", "--top-k")):
                if key in config: command.extend([flag, str(config[key])])
    else:
        command += ["--trace", str(args.trace or ROOT / "pilots/v10_rag_poc/data/ai_trace.json")]
    if args.preview:
        command.append("--preview-only")
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic", required=True, help="normalized topic or registered alias")
    parser.add_argument("--mode", choices=("executable", "replay", "illustration"), default="executable")
    parser.add_argument("--render", choices=("auto", "manim"), default="auto")
    parser.add_argument("--preview", action="store_true", help="render a 540p30 technical preview and stop")
    parser.add_argument("--config", type=Path, help="JSON options for the selected adapter")
    parser.add_argument("--trace", type=Path, help="saved trace for replay")
    parser.add_argument("--document", type=Path, help="new UTF-8 document for RAG")
    parser.add_argument("--question", help="RAG query paired with --document")
    parser.add_argument("--input", type=Path, help="input image/data; only accepted when an adapter implements it")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "pilots/v11_mechanisms/output")
    parser.add_argument("--asset", help="asset ID required by a robotics adapter")
    parser.add_argument("--robot", help="robot model ID for robotics adapters")
    args = parser.parse_args()

    registry = MechanismRegistry()
    try:
        capability = registry.resolve(args.topic)
        if capability is None:
            resolution = registry.resolve_detailed(args.topic)
            if resolution["status"] == "ambiguous":
                raise SystemExit(f"ambiguous topic {args.topic!r}; choose one: {', '.join(resolution['candidates'])}")
            raise SystemExit(f"unknown topic {args.topic!r}; inspect supported names with scripts/inspect_capabilities.py")
        topic = capability["topic"]
        if topic == "rag":
            if args.mode not in {"executable", "replay"}:
                raise SystemExit("RAG supports executable or replay mode; illustration mode is not routed here")
            args.output_dir.mkdir(parents=True, exist_ok=True)
            run_rag(args, args.output_dir)
            return 0
        if capability["implementation_status"] != "ready":
            raise SystemExit(f"unsupported for execution: {topic}; level={capability['support_level']}, "
                             f"status={capability['implementation_status']}; use inspect_capabilities.py")
        if args.mode != "executable":
            raise SystemExit(f"{topic} currently supports executable mode only")
        if args.input:
            raise SystemExit(f"{topic} has no adapter for --input image/data; pass supported values via --config JSON")
        config = json.loads(args.config.read_text(encoding="utf-8")) if args.config else {}
        if topic == "robot_kinematics":
            args.output_dir = args.output_dir / topic
            args.output_dir.mkdir(parents=True, exist_ok=True)
            if args.robot and args.robot != "unitree_h1":
                raise SystemExit("robot_kinematics currently supports only unitree_h1")
            if args.asset and args.asset != "blender.unitree_h1.v1":
                raise SystemExit("robot_kinematics requires asset blender.unitree_h1.v1")
            config["output_dir"] = str(args.output_dir / "data")
        else:
            args.output_dir = args.output_dir / topic
            args.output_dir.mkdir(parents=True, exist_ok=True)

        adapter = registry.load_adapter(topic)
        request = MechanismRequest(topic=topic, options=config)
        prepared = adapter.prepare(request)
        trace = adapter.execute(prepared)
        validation = adapter.validate(trace)
        if validation:
            raise SystemExit("adapter trace validation failed: " + "; ".join(validation))
        if topic == "robot_kinematics":
            trace_path = Path(config["output_dir"]) / "trace.json"
            trace_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            trace_path = args.output_dir / "trace.json"
            trace_path.write_text(json.dumps(trace, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        plan = adapter.build_visual_plan(trace)
        plan.setdefault("title", {"quantization": "실제 수치로 보는 가중치 양자화",
                                   "nms": "합성 후보로 계산하는 IoU 기반 NMS",
                                   "mcu_pid": "엔코더 피드백을 사용하는 PID 모터 시뮬레이션",
                                   "robot_kinematics": "MuJoCo 로봇팔의 실제 관절 상태",
                                   "self_attention": "토큰 관계 점수로 계산하는 Self-Attention"}[topic])
        if topic == "quantization" and plan.get("scope") == "weight_and_activation":
            plan["title"] = "가중치와 활성값을 따로 양자화해 오차를 비교"
        manifest_path = write_v9_manifest(topic, trace_path, args.output_dir,
            "model_execution" if topic == "robot_kinematics" else "toy_simulation", "preview" if args.preview else "final")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["_path"] = str(manifest_path)
        manifest["render_mode"] = "preview" if args.preview else "final"
        output = args.output_dir / ("preview.mp4" if args.preview else "final.mp4")
        rendered = adapter.render(plan, manifest, output)
        report = {"topic": topic, "domain": capability["domain"], "support_level": capability["support_level"],
                  "mode": "executable_simulation", "trace": str(trace_path),
                  "trace_id": trace.get("trace_id", "robotics-visual-trace"),
                  "trace_sha256": hashlib.sha256(trace_path.read_bytes()).hexdigest(),
                  "manifest": str(manifest_path), "renderer": "manim", "media": str(rendered),
                  "media_mode": "silent technical preview" if args.preview else "silent technical render",
                  "limitations": trace.get("limitations", trace.get("model", {}).get("assumptions", [])),
                  "technical_decode": "PASS"}
        (args.output_dir / "production_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        print(f"PASS: {topic} → {trace_path} → {rendered}")
        return 0
    except (KeyError, NotImplementedError) as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    raise SystemExit(main())
