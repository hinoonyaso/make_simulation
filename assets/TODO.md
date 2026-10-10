# Pending asset imports

Not available in a clean clone. Some STEP files below exist only in the current local worktree
and are ignored by Git. Their presence does not mean they are included in the public repository
or that their current rights permit redistribution. See `docs/assets/EXISTING_ASSET_AUDIT.md`.
Raspberry Pi 5's folder has a local MIT license file, but the STEP file's coverage by that license
has not been independently confirmed.

## Confirmed workflow for these four
No anonymous direct-download URL exists for any of these — each needs a human to log in / fill a
form once. The plan: **log in manually, download the file once, hand it to Claude** — it then
gets the same treatment as everything else here (own folder, README.md with source/license,
`registry.json` entry), exactly like `jetrover/` and the rest were done. Don't spend more time
trying to script around the gate; it isn't going to open.

- [ ] **Jetson Orin Nano Developer Kit** — STEP file, gated behind NVIDIA Developer account
  login (`developer.nvidia.com`, forum-attached or a `.../secure/...` path).
- [ ] **Jetson Orin Nano module (SoM)** — same NVIDIA account gate as the Dev Kit, separate file
  (module only, not the full carrier board).
- [ ] **STM32 Nucleo-F446RE** — CAD design file gated behind ST's "Get CAD design file" form
  (name/email, or an ST account).
- [ ] **Hailo-8 M.2 NPU** — STEP model (2242/2280, and other M.2 form factors as of 2026-09)
  gated behind Hailo Developer Zone / Community login.

## Not a download at all
- [ ] **BlenderKit: Warehouse/Pallet Rack** — no plain file exists; BlenderKit assets come
  through their own Blender addon + account, not a URL. Add from inside Blender (BlenderKit
  addon → search → download), not from this repo.
- [ ] **BlenderKit: Industrial Assets** (conveyor, trolley, utility box) — same, addon-only.

## Local-only assets, not clone-reproducible
The current worktree has files under `livox_mid360/`, `ouster_os1/`, `ouster_os0/`,
`ouster_osdome/`, `zed2i/`, and `raspberry_pi5/`. All listed CAD model files are ignored by Git.
Their hashes, sizes, Git state, and local license notes are recorded in the audit report.
