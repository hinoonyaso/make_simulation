# Classical CAN arbitration

Run `uv run python scripts/produce_video.py --topic can_arbitration --config examples/v12/can_arbitration.json --preview`. Scope is Classical CAN 2.0A, standard 11-bit data/remote frames, DLC 0–8, one simultaneous request set, and integer wire-bit event ticks.

The deterministic engine constructs SOF, ID, RTR, IDE/r0, DLC, data, CRC-15/CAN (polynomial `0x4599`), stuffing through the CRC sequence, then unstuffed CRC delimiter, ACK slot/delimiter, EOF and intermission. Dominant 0 beats recessive 1. A receiver must be named for ACK; no receiver yields `no_ack_receiver`. Equal arbitration fields with diverging later bits produce a bit-error event rather than an arbitrary ID tie-break. Error recovery/retry is outside the model.

`python-can` VirtualBus proves API frame transport only. `assets/v12/engineering_demo.dbc` has example motor, motor-status and battery-status messages; cantools encodes and decodes a real DBC signal round trip. Neither proves physical CAN timing. SocketCAN vcan remains optional; no privileged kernel setup occurs in CI or the adapter.

## V12.1 evidence and timing validation

The adapter re-runs the deterministic protocol model and compares status, normalized requests/receivers, winner/loser/ACK state, physical bits and count, stuffing positions, stuffed CRC, CRC/polynomial, field metadata, supported event records, bitrate and both bit-time representations. Envelope inputs/outputs and the primary seconds clock are checked against that result as well. A trace whose content and envelope hash are both recomputed still fails domain validation when protocol evidence has been changed.

Event ticks are zero-based physical wire-bit slots. Arbitration-loss mapping counts stuffing before the raw arbitration bit being located; it does not include a stuff bit caused after that bit. ACK/ACK_MISSING point to the ACK slot (`wire length - 12` for this frame layout); a bit-error before the ACK field does not fabricate an ACK_MISSING event. A CRC-15/CAN reference check uses the catalogue check string `123456789` → `0x059E` with width 15, polynomial `0x4599`, zero init/xorout and no reflection ([CRC catalogue](https://reveng.sourceforge.io/crc-catalogue/1-15.htm)). The model remains Classical CAN 2.0A only; error recovery, retries, physical bus voltages and CAN FD are outside scope.
