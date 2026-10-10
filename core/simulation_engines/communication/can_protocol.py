"""Deterministic Classical CAN 2.0A data-frame arbitration and bit encoding.

This is a protocol-level event model, not an electrical CAN_H/CAN_L simulator.
Bit stuffing is applied through the CRC sequence; fixed CRC delimiter, ACK,
EOF and intermission fields are kept unstuffed per the Bosch CAN 2.0 spec.
"""
from __future__ import annotations

from dataclasses import dataclass

CRC15_POLY = 0x4599
SUPPORTED_PROTOCOL_EVENTS = {
    "TX_REQUEST", "ARBITRATION_LOST", "ARBITRATION_WON",
    "IDENTICAL_ARBITRATION_FIELDS", "BIT_ERROR_EQUAL_ARBITRATION",
    "IDENTICAL_FRAME_TRANSMITTERS", "ACK", "ACK_MISSING",
}


@dataclass(frozen=True)
class EncodedFrame:
    node: str
    arbitration_id: int
    remote: bool
    data: bytes
    dlc: int
    fields: tuple[tuple[str, int], ...]
    crc: int
    crc_input_bits: tuple[int, ...]
    stuffed_crc_bits: tuple[int, ...]
    wire_bits: tuple[int, ...]
    stuff_positions: tuple[int, ...]


def crc15_can(bits) -> int:
    crc = 0
    for bit in bits:
        feedback = ((crc >> 14) & 1) ^ int(bit)
        crc = (crc << 1) & 0x7FFF
        if feedback:
            crc ^= CRC15_POLY
    return crc


def bit_stuff(bits) -> tuple[tuple[int, ...], tuple[int, ...]]:
    out, positions = [], []
    last, run = None, 0
    for bit in bits:
        bit = int(bit)
        out.append(bit)
        run = run + 1 if bit == last else 1
        last = bit
        if run == 5:
            stuffed = 1 - last
            positions.append(len(out))
            out.append(stuffed)
            last, run = stuffed, 1
    return tuple(out), tuple(positions)


def _field(name: str, value: int, width: int) -> list[tuple[str, int]]:
    return [(name, (value >> bit) & 1) for bit in range(width - 1, -1, -1)]


def validate_frame_input(raw: dict) -> dict:
    node = raw.get("node")
    arbitration_id = raw.get("id")
    data_value = raw.get("data", "")
    remote = raw.get("remote", False)
    if not isinstance(node, str) or not node.strip():
        raise ValueError("CAN node must be a non-empty string")
    if type(arbitration_id) is not int or not 0 <= arbitration_id <= 0x7FF:
        raise ValueError("Classical CAN standard identifier must be an 11-bit integer")
    if type(remote) is not bool:
        raise ValueError("remote must be boolean")
    if not isinstance(data_value, str) or len(data_value) % 2:
        raise ValueError("CAN data must be an even-length hexadecimal string")
    try:
        data = bytes.fromhex(data_value)
    except ValueError as exc:
        raise ValueError("CAN data must be hexadecimal") from exc
    if remote and data:
        raise ValueError("Classical CAN remote frames cannot contain a data field")
    if len(data) > 8:
        raise ValueError("Classical CAN payload cannot exceed 8 bytes")
    dlc = raw.get("dlc", len(data))
    if type(dlc) is not int or not 0 <= dlc <= 8:
        raise ValueError("Classical CAN DLC must be an integer in [0, 8]")
    if remote:
        if data:
            raise ValueError("remote frame data must be empty")
    elif dlc != len(data):
        raise ValueError("data frame DLC must match payload byte length")
    return {"node": node, "id": arbitration_id, "data": data, "remote": remote, "dlc": dlc}


def encode_standard_frame(raw: dict) -> EncodedFrame:
    frame = validate_frame_input(raw)
    fields: list[tuple[str, int]] = [("SOF", 0)]
    fields += _field("identifier", frame["id"], 11)
    fields.append(("RTR", int(frame["remote"])))
    fields.extend((("IDE", 0), ("r0", 0)))
    fields += _field("DLC", frame["dlc"], 4)
    if not frame["remote"]:
        for byte_index, byte in enumerate(frame["data"]):
            fields += [(f"data[{byte_index}]", bit)
                       for _, bit in _field("data", byte, 8)]
    raw_bits = tuple(bit for _, bit in fields)
    crc = crc15_can(raw_bits)
    crc_bits = tuple((crc >> bit) & 1 for bit in range(14, -1, -1))
    stuffed, positions = bit_stuff((*raw_bits, *crc_bits))
    wire = (*stuffed, 1, 1, 1, *(1 for _ in range(7)), *(1 for _ in range(3)))
    return EncodedFrame(frame["node"], frame["id"], frame["remote"], frame["data"], frame["dlc"],
                        tuple(fields), crc, raw_bits, stuffed, tuple(wire), positions)


def _arbitration_key(frame: EncodedFrame) -> tuple[int, ...]:
    return (*(bit for _, bit in _field("identifier", frame.arbitration_id, 11)), int(frame.remote))


def _wire_tick_for_raw_bit(frame: EncodedFrame, raw_bit_index: int) -> int:
    """Return the zero-based wire slot of a raw bit (stuffing before, not after it)."""
    if type(raw_bit_index) is not int or not 0 <= raw_bit_index < len(frame.crc_input_bits):
        raise ValueError("raw bit index is outside the encoded frame")
    stuffed_prefix, _ = bit_stuff(frame.crc_input_bits[:raw_bit_index])
    return len(stuffed_prefix)


def arbitration_wire_extent(events: list[dict], physical_bit_count: int) -> tuple[int, int]:
    """Return the exclusive arbitration boundary and display slots incl. margin.

    Event timestamps are zero-based physical wire slots. The arbitration winner
    timestamp is the boundary after SOF, 11 identifier bits and RTR, including
    any stuff bits inserted before that boundary.
    """
    if type(physical_bit_count) is not int or physical_bit_count < 1:
        raise ValueError("physical bit count must be a positive integer")
    boundaries = [event for event in events if isinstance(event, dict)
                  and event.get("event") in {"ARBITRATION_WON", "IDENTICAL_ARBITRATION_FIELDS"}]
    if len(boundaries) != 1:
        raise ValueError("CAN events require exactly one arbitration boundary")
    end_tick = boundaries[0].get("timestamp")
    if type(end_tick) is not int or not 1 <= end_tick <= physical_bit_count:
        raise ValueError("arbitration boundary is outside physical wire bits")
    for event in events:
        if isinstance(event, dict) and event.get("event") == "ARBITRATION_LOST":
            tick = event.get("timestamp")
            if type(tick) is not int or not 0 <= tick < end_tick:
                raise ValueError("arbitration loss marker must precede the winner boundary")
    return end_tick, end_tick + 1


def arbitrate(raw_frames: list[dict], *, bitrate: int = 1_000_000,
              receivers: list[str] | None = None) -> dict:
    if not isinstance(raw_frames, list) or not raw_frames:
        raise ValueError("CAN arbitration requires at least one frame request")
    if type(bitrate) is not int or not 10_000 <= bitrate <= 1_000_000:
        raise ValueError("Classical CAN bitrate must be an integer in [10 kbit/s, 1 Mbit/s]")
    frames = [encode_standard_frame(item) for item in raw_frames]
    nodes = [item.node for item in frames]
    if len(set(nodes)) != len(nodes):
        raise ValueError("CAN frame node names must be unique per simultaneous request")
    receivers = [] if receivers is None else receivers
    if not isinstance(receivers, list) or any(not isinstance(v, str) or not v for v in receivers):
        raise ValueError("receivers must be a list of non-empty node names")
    if len(set(receivers)) != len(receivers) or set(receivers) & set(nodes):
        raise ValueError("receiver names must be unique and distinct from transmitters")
    active = list(frames)
    events = [{"timestamp": 0, "node": frame.node, "event": "TX_REQUEST"} for frame in frames]
    arbitration_bits = [_arbitration_key(frame) for frame in frames]
    loser_bits = {}
    for bit_index in range(12):
        if len(active) <= 1:
            break
        bus_bit = min(_arbitration_key(frame)[bit_index] for frame in active)
        remaining = []
        for frame in active:
            sent = _arbitration_key(frame)[bit_index]
            if sent == 1 and bus_bit == 0:
                loser_bits[frame.node] = bit_index
                events.append({"timestamp": _wire_tick_for_raw_bit(frame, bit_index + 1), "node": frame.node,
                               "event": "ARBITRATION_LOST", "bit_index": bit_index,
                               "field": "identifier" if bit_index < 11 else "RTR",
                               "sent_bit": sent, "bus_bit": bus_bit})
            else:
                remaining.append(frame)
        active = remaining
    if not active:
        raise RuntimeError("CAN arbitration unexpectedly removed all transmitters")
    # Equal arbitration fields stay on the bus. Diverging control/data bits are
    # a bit error, not a winner selected by sorting equal identifiers.
    winners = active
    representative = winners[0]
    conflict_bit = None
    for field_index, (expected_name, expected_bit) in enumerate(representative.fields[12:], 12):
        different = [frame for frame in winners if frame.fields[field_index][1] != expected_bit]
        if different:
            conflict_bit = field_index
            break
    arbitration_tick = len(bit_stuff(representative.crc_input_bits[:13])[0])
    events.append({"timestamp": arbitration_tick, "node": ",".join(frame.node for frame in winners),
                   "event": "ARBITRATION_WON" if len(winners) == 1 else "IDENTICAL_ARBITRATION_FIELDS"})
    if conflict_bit is not None:
        prefix_wire, _ = bit_stuff(representative.crc_input_bits[:conflict_bit])
        wire_conflict_index = len(prefix_wire)
        events.append({"timestamp": wire_conflict_index, "node": ",".join(f.node for f in winners),
                       "event": "BIT_ERROR_EQUAL_ARBITRATION", "bit_index": conflict_bit})
        wire = (*representative.wire_bits[:wire_conflict_index], *(0 for _ in range(6)), *(1 for _ in range(8)))
        acked = False
        winner_nodes = []
        status = "bit_error_equal_arbitration"
    else:
        shared_identical = len(winners) > 1
        wire = representative.wire_bits
        acked = bool(receivers)
        winner_nodes = [frame.node for frame in winners] if acked else []
        status = "success" if acked else "no_ack_receiver"
        if shared_identical:
            events.append({"timestamp": len(wire) - 3, "node": ",".join(f.node for f in winners),
                           "event": "IDENTICAL_FRAME_TRANSMITTERS"})
    if acked:
        # ACK slot is before ACK delimiter + EOF + intermission.
        ack_index = len(wire) - 12
        wire = (*wire[:ack_index], 0, *wire[ack_index + 1:])
        events.extend({"timestamp": ack_index, "node": receiver, "event": "ACK"}
                      for receiver in receivers[:1])
    elif status != "bit_error_equal_arbitration":
        # ACK_MISSING is meaningful only after a complete frame reached its ACK slot.
        events.append({"timestamp": len(wire) - 12, "node": "BUS", "event": "ACK_MISSING"})
    events.sort(key=lambda event: event["timestamp"])
    bits = list(wire)
    return {"status": status, "bitrate_hz": bitrate,
            "bit_time_seconds": 1.0 / bitrate, "bit_time_ns": [1_000_000_000, bitrate],
            "requests": [{"node": f.node, "id": f.arbitration_id, "remote": f.remote,
                          "data_hex": f.data.hex(), "dlc": f.dlc} for f in frames],
            "winners": winner_nodes, "losers": [{"node": node, "bit_index": index}
                                                   for node, index in loser_bits.items()],
            "receivers": receivers, "acknowledged": acked,
            "physical_bits": bits, "bit_count": len(bits),
            "stuffed_bit_positions_before_ack": list(representative.stuff_positions),
            "stuffed_crc": list(representative.stuffed_crc_bits),
            "crc15": representative.crc, "crc_polynomial": "0x4599",
            "field_bits": [{"field": name, "bit": bit} for name, bit in representative.fields],
            "events": events,
            "model_limitations": ["Classical CAN standard 11-bit data/remote frames only; no error recovery retransmission.",
                                  "Protocol bit/event model; no CAN_H/CAN_L voltage, propagation delay, sample point or transceiver model.",
                                  "A real receiver is required for ACK; missing ACK is reported as unsuccessful."]}
