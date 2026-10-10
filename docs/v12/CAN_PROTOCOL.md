# Classical CAN arbitration

Run `uv run python scripts/produce_video.py --topic can_arbitration --config examples/v12/can_arbitration.json --preview`. Scope is Classical CAN 2.0A, standard 11-bit data/remote frames, DLC 0–8, one simultaneous request set, and integer wire-bit event ticks.

The deterministic engine constructs SOF, ID, RTR, IDE/r0, DLC, data, CRC-15/CAN (polynomial `0x4599`), stuffing through the CRC sequence, then unstuffed CRC delimiter, ACK slot/delimiter, EOF and intermission. Dominant 0 beats recessive 1. A receiver must be named for ACK; no receiver yields `no_ack_receiver`. Equal arbitration fields with diverging later bits produce a bit-error event rather than an arbitrary ID tie-break. Error recovery/retry is outside the model.

`python-can` VirtualBus proves API frame transport only. `assets/v12/engineering_demo.dbc` has example motor, motor-status and battery-status messages; cantools encodes and decodes a real DBC signal round trip. Neither proves physical CAN timing. SocketCAN vcan remains optional; no privileged kernel setup occurs in CI or the adapter.
