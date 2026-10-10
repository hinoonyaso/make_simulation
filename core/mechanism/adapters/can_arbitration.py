"""Classical CAN bit-level simulation plus independent python-can/DBC checks."""
from __future__ import annotations

import importlib.metadata
import math
from pathlib import Path

import can
import cantools

from core.mechanism.engineering_trace import validate_discrete_events
from core.mechanism.protocol import MechanismRequest
from core.mechanism.trace_contract import make_envelope, validate_envelope
from core.simulation_engines.communication.can_protocol import arbitrate

ROOT = Path(__file__).resolve().parents[3]
DBC_PATH = ROOT / "assets/v12/engineering_demo.dbc"


class CANArbitrationAdapter:
    def __init__(self, capability=None):
        self.capability = capability or {}

    def describe_capability(self):
        return self.capability

    def prepare(self, request: MechanismRequest):
        return {"topic": request.topic, **request.options}

    def execute(self, config):
        bitrate = config.get("bitrate", 1_000_000)
        frames = config.get("frames", [
            {"node": "ECU_A", "id": 0x100, "data": "10203040"},
            {"node": "ECU_B", "id": 0x200, "data": "A0B0C0D0"},
        ])
        receivers = config.get("receivers", ["ECU_C"])
        result = arbitrate(frames, bitrate=bitrate, receivers=receivers)
        result["kind"] = "discrete_events"
        result["time_unit"] = "bit_time"
        result["events"] = [{**event, "timestamp": int(event["timestamp"])}
                            for event in result["events"]]
        dbc_result = self._dbc_round_trip()
        virtual_bus = self._virtual_bus_smoke()
        payload = {**result, "dbc_round_trip": dbc_result,
                   "python_can_virtual_bus": virtual_bus,
                   "protocol_model": "Classical CAN 2.0A standard data/remote frame bit model"}
        return make_envelope(domain="communication_protocol", topic="can_arbitration",
            execution_type="numerical_simulation", inputs=[
                {"id": "frames", "value": result["requests"]},
                {"id": "bitrate_hz", "value": result["bitrate_hz"]},
                {"id": "receivers", "value": result["receivers"]}],
            operations=[{"id": "bit_level_encode_arbitrate", "engine": "deterministic Python CAN model"},
                        {"id": "dbc_encode_decode", "engine": "cantools"},
                        {"id": "virtual_bus_smoke", "engine": "python-can VirtualBus"}],
            outputs=[{"id": "winners", "value": result["winners"]},
                     {"id": "physical_bits", "value": result["physical_bits"]}],
            payload=payload, timestamps=[i / bitrate for i in range(result["bit_count"])],
            provenance={"engine": "local Classical CAN protocol model",
                        "python_can_version": importlib.metadata.version("python-can"),
                        "cantools_version": importlib.metadata.version("cantools"),
                        "dbc_sha256": __import__("hashlib").sha256(DBC_PATH.read_bytes()).hexdigest()},
            limitations=result["model_limitations"] + [
                "python-can VirtualBus validates API message transport only; it does not model CAN bit arbitration."])

    @staticmethod
    def _dbc_round_trip():
        db = cantools.database.load_file(DBC_PATH)
        message = db.get_message_by_name("MotorSpeedCommand")
        values = {"target_rpm": 1500.0, "enable": 1}
        encoded = message.encode(values)
        decoded = message.decode(encoded)
        if decoded != values:
            raise RuntimeError(f"DBC round-trip mismatch: {decoded!r}")
        return {"message": message.name, "arbitration_id": message.frame_id,
                "signals": decoded, "data_hex": encoded.hex(), "status": "PASS"}

    @staticmethod
    def _virtual_bus_smoke():
        bus = can.Bus(interface="virtual", channel="v12-can-smoke", receive_own_messages=True)
        try:
            sent = can.Message(arbitration_id=0x321, data=bytes.fromhex("123456"), is_extended_id=False)
            bus.send(sent)
            received = bus.recv(timeout=1.0)
            if received is None or received.arbitration_id != sent.arbitration_id or received.data != sent.data:
                raise RuntimeError("python-can VirtualBus did not return the transmitted frame")
            return {"status": "PASS", "arbitration_id": received.arbitration_id,
                    "data_hex": received.data.hex(), "channel": "isolated in-process virtual bus"}
        finally:
            bus.shutdown()

    def validate(self, trace):
        errors = validate_envelope(trace)
        p = trace.get("payload", {})
        if trace.get("topic") != "can_arbitration" or trace.get("domain") != "communication_protocol":
            errors.append("CAN trace domain/topic mismatch")
        errors.extend(validate_discrete_events(p))
        try:
            from core.simulation_engines.communication.can_protocol import SUPPORTED_PROTOCOL_EVENTS
            unknown = sorted({event.get("event") for event in p.get("events", [])
                              if isinstance(event, dict) and event.get("event") not in SUPPORTED_PROTOCOL_EVENTS})
            if unknown:
                errors.append(f"unsupported CAN protocol event(s): {unknown}")
            canonical_requests = [{"node": row["node"], "id": row["id"],
                "data": row["data_hex"], "remote": row["remote"], "dlc": row["dlc"]}
                for row in p["requests"]]
            recomputed = arbitrate(canonical_requests, bitrate=p["bitrate_hz"], receivers=p["receivers"])
            for key in ("status", "requests", "receivers", "winners", "losers", "acknowledged",
                        "physical_bits", "bit_count", "stuffed_bit_positions_before_ack", "stuffed_crc",
                        "crc15", "crc_polynomial", "field_bits", "events", "bitrate_hz", "bit_time_ns"):
                if recomputed[key] != p[key]:
                    errors.append(f"CAN protocol result mismatch in {key}")
            if (not isinstance(p.get("bit_time_seconds"), (int, float))
                    or not math.isfinite(p["bit_time_seconds"])
                    or not math.isclose(p["bit_time_seconds"], recomputed["bit_time_seconds"],
                                        rel_tol=0.0, abs_tol=1e-18)):
                errors.append("CAN protocol result mismatch in bit_time_seconds")
            if p.get("bit_count") != len(p.get("physical_bits", [])):
                errors.append("CAN bit_count does not match physical_bits length")
            # New V12 traces bind bus settings to envelope inputs. Older valid
            # traces without these optional input records remain replayable.
            input_values = {row.get("id"): row.get("value") for row in trace.get("inputs", [])
                            if isinstance(row, dict)}
            for input_id, payload_key in (("frames", "requests"), ("bitrate_hz", "bitrate_hz"),
                                          ("receivers", "receivers")):
                if input_id in input_values and input_values[input_id] != p[payload_key]:
                    errors.append(f"CAN payload {payload_key} differs from envelope input")
            expected_times = [index / recomputed["bitrate_hz"] for index in range(recomputed["bit_count"])]
            actual_times = trace.get("timestamps", [])
            if (len(actual_times) != len(expected_times)
                    or any(not math.isclose(float(a), b, rel_tol=0.0, abs_tol=1e-18)
                           for a, b in zip(actual_times, expected_times))):
                errors.append("CAN envelope timestamps do not match bitrate and physical bit count")
            output_values = {row.get("id"): row.get("value") for row in trace.get("outputs", [])
                             if isinstance(row, dict)}
            for output_id, expected in (("winners", recomputed["winners"]),
                                        ("physical_bits", recomputed["physical_bits"])):
                if output_values.get(output_id) != expected:
                    errors.append(f"CAN envelope output mismatch in {output_id}")
            if p["dbc_round_trip"].get("status") != "PASS" or p["python_can_virtual_bus"].get("status") != "PASS":
                errors.append("CAN integration smoke status is not PASS")
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"CAN trace payload invalid: {exc}")
        return errors

    def build_visual_plan(self, trace):
        p = trace["payload"]
        return {"kind": "engineering", "domain": trace["domain"], "topic": trace["topic"],
                "title": "Classical CAN: 비트 중재와 프레임 전송", "trace_id": trace["trace_id"],
                "timestamps": trace["timestamps"], "events": p["events"],
                "bits": p["physical_bits"], "fields": p["field_bits"], "requests": p["requests"],
                "winners": p["winners"], "losers": p["losers"], "acknowledged": p["acknowledged"],
                "bitrate_hz": p["bitrate_hz"], "bit_count": p["bit_count"],
                "visualization": "digital_timing_diagram",
                "source_time_unit": "bit_time"}

    def render(self, plan, manifest, output: Path):
        from core.mechanism.renderer import render_plan
        return render_plan(plan, Path(manifest["_path"]), output, manifest.get("render_mode", "preview"))
