# EP01 — 3-DOF 로봇 팔의 순기구학

## Locked episode brief

- **Central question:** 세 관절각 `θ1, θ2, θ3`만 알 때 로봇 손끝의 3차원 위치 `(x, y, z)`를 어떻게 구하는가?
- **Missing intuition:** 평면에서는 링크 변위 벡터를 더할 수 있지만, 3차원에서는 각 관절의 회전과 이동이 뒤의 모든 링크와 좌표계에 누적된다. 동차변환은 이 회전과 이동을 한 체인으로 일반화한다.
- **Audience promise:** 평면의 한 링크에서 시작해 두 링크의 누적각을 이해하고, 같은 논리를 3차원 변환행렬로 확장해 손끝 좌표를 얻는다.
- **Runtime / delivery:** `168 s` target (acceptable final range `150–180 s`), `1920×1080`, `30 fps`, Korean narration.
- **Scene/tool lock:** exactly 6 scenes. Blender is used only for Scenes 1 and 4; Scenes 2, 3, 5, 6 are Manim.
- **Persistent objects:** one two-link arm, the amber end-effector point `P`, and the coordinate-frame chain `{0}→{1}→{2}→{3}`. Preserve pose and screen direction across tool handoffs.
- **Evidence label:** conceptual illustration plus analytic derivation. Do not present motion as measured hardware data or physics simulation.

## Locked beat sheet

| Beat / scene / time | Narration intent (Korean) | Persistent object | Dominant visual change / attention target | Tool | Evidence mode |
|---|---|---|---|---|---|
| `b01` / **S1** / `00:00–00:11` | “베이스, 어깨, 팔꿈치. 세 각도로 손끝의 `x,y,z`를 찾을 수 있을까요?” | 3D arm, amber `P` | Neutral pose → three joint arcs; question beside viewport. | **B** | Illustration |
| `b02` / **S1** / `00:11–00:22` | “평면에서 원리를 만든 뒤, 같은 생각을 3차원으로 확장해 보겠습니다.” | Same arm and `P` | Joints activate one at a time; settle on continuity pose. | **B** | Illustration |
| `b03` / **S2** / `00:22–00:35` | “길이 `L`인 링크를 위로 `α`만큼 들면 손끝은 반지름 `L`인 원 위에 있습니다.” | One planar link, `P` | Blender arm match-cuts to one 2D link and radius arc. | **M** | Analytic derivation |
| `b04` / **S2** / `00:35–00:49` | “가로 투영은 `L cos α`, 세로 투영은 `L sin α`입니다.” | Link and projections | Build `x=L cos α`, then `y=L sin α`, one projection at a time. | **M** | Analytic derivation |
| `b05` / **S3** / `00:49–01:04` | “두 번째 링크의 `β`는 상대각이라 실제 방향은 `α+β`입니다.” | Two planar links | Attach link 2; transform its label from `β` to `α+β`. | **M** | Analytic derivation |
| `b06` / **S3** / `01:04–01:21` | “어깨가 돌면 두 링크가, 팔꿈치가 돌면 두 번째 링크만 움직입니다. 두 변위 벡터를 더해 `x=L1 cos α+L2 cos(α+β)`, `y=L1 sin α+L2 sin(α+β)`를 얻습니다.” | Full planar chain | Demonstrate downstream motion, then add component arrows into the two equations. | **M** | Analytic derivation |
| `b07` / **S4** / `01:21–01:39` | “평면을 세우고 수직축 회전 `θ1`을 더하면 3차원 팔이 됩니다.” | 3D arm, `{0},{1}` | Planar silhouette becomes Blender arm; yaw and `{0}→{1}` appear. | **B** | Kinematic illustration |
| `b08` / **S4** / `01:39–01:58` | “어깨 `θ2`와 팔꿈치 `θ3`의 양의 피치는 링크를 위로 듭니다. 어깨는 뒤의 두 링크를, 팔꿈치는 마지막 링크와 프레임 `{3}`을 움직입니다.” | Frames `{0}…{3}`, amber `P` | Ghost poses isolate shoulder versus elbow dependency; finish with `{3}` exactly at `P`. | **B** | Kinematic illustration |
| `b09` / **S5** / `01:58–02:16` | “각 관절의 회전과 이동을 동차변환으로 묶고 부모에서 자식 순서로 곱합니다: `T03=T01 T12 T23`.” | Frame-chain schematic | Match 3D frames to three transform blocks; compose left to right. | **M** | Analytic derivation |
| `b10` / **S5** / `02:16–02:34` | “프레임 3의 원점을 옮기면 `[pEE;1]=T03[0,0,0,1]^T`. 반지름을 요가 `x,y`로 나누고, `z`에는 어깨 높이 `h`가 더해집니다.” | Chain, amber `P` | Apply origin vector; reveal `r`, then Cartesian `pEE=(x,y,z)` and the `h` offset. | **M** | Analytic derivation |
| `b11` / **S6** / `02:34–02:42` | “관절각을 정하고, 변환을 연결하고, 마지막 원점을 옮깁니다.” | Mini arm and chain | Compress angle arcs → transform blocks → `T03`. | **M** | Recap |
| `b12` / **S6** / `02:42–02:48` | “각도, 체인, 순기구학, 그리고 `x,y,z`. 이것이 3자유도 팔의 순기구학입니다.” | Amber `P` | Finish on `θ → chain → FK → (x,y,z)` with no new notation. | **M** | Recap |

Total locked duration: **168 s**. Scene boundaries may shift by up to ±2 s during narration fitting, while order, total range, equations, and tool assignments remain locked.

## Visual and model contract

### Geometry, frames, and signs

- Units are metres and radians internally. On-screen teaching angles may be shown in degrees; formulas remain symbolic.
- Link lengths and shoulder height are fixed: `L1=2.0 m`, `L2=1.5 m`, `h=0.6 m`.
- Right-handed world/base frame `{0}` has its origin on the floor directly below the shoulder: `+x` forward at zero yaw, `+y` left, `+z` up.
- Frame `{1}` is at the shoulder, height `h`, after base yaw `θ1` about `+z`. Frame `{2}` is at the elbow. **Frame `{3}` is at the end effector `P`**, not at a decorative wrist offset.
- `θ1` is positive counter-clockwise when viewed from `+z`. `θ2` and `θ3` are relative pitch angles; positive pitch lifts the downstream link upward. With the stated axes and standard right-handed matrices, implement this as `Ry(-θ)`.
- The two pitch axes are parallel to local `+y`. `θ3` is relative to link 1, so link 2’s elevation is `θ2+θ3`.
- The planar teaching symbols are exclusively `α, β`; the 3D on-screen symbols are exclusively `θ1, θ2, θ3`. Code may use `q1, q2, q3` internally. In Scenes 2–3, planar `+x` is outward and planar `+y` is upward. At the Scene 3→4 handoff, explicitly map planar height `y` to 3D `z-h`.
- A useful continuity pose is `θ1=35°`, `θ2=25°`, `θ3=-40°`; use it for held frames and cross-tool match cuts unless motion requires interpolation from neutral.

### Transform and position lock

Use column vectors and pre-multiplication:

```text
T01 = Trans_z(h) · Rz(θ1)
T12 = Ry(-θ2) · Trans_x(L1)
T23 = Ry(-θ3) · Trans_x(L2)

T03 = T01 · T12 · T23
[pEE; 1] = T03 · [0, 0, 0, 1]^T
```

The final position must agree with:

```text
r = L1 cos(θ2) + L2 cos(θ2+θ3)
x = r cos(θ1)
y = r sin(θ1)
z = h + L1 sin(θ2) + L2 sin(θ2+θ3)
pEE = (x, y, z)^T
```

Do not add an unmodeled tool length or shoulder offset. Any mesh thickness is visual only; joint origins and `P` govern the math.

### Cross-tool visual lock

- Background: bright `#F7F9FC`; primary text: dark `#243247`; inactive context: gray `#8B95A1`.
- Coordinate axes always use `X=#E74C3C`, `Y=#2ECC71`, `Z=#3498DB`.
- Link 1 is purple `#7867C5`; link 2 is neutral gray `#AAB2BD`; end effector/result `P` is amber `#F5B942`, avoiding ambiguity with the green Y axis. Active angles use the matching link color or dark text emphasis.
- Link colors remain identical across Blender and Manim.
- Blender camera continuity: three-quarter view with `+z` visibly vertical and the base yaw readable. Scene 4 begins from a framing compatible with Scene 1’s final hero pose. At 1920×1080, use viewport `x=60, y=190, w=1080, h=720`; reserve `x=1190…1840` for equations/joint controls and `y≥945` for captions.
- Manim continuity: keep the arm’s base/shoulder left of centre and reserve the right half for equations. Transform existing labels and arrows instead of clearing to new slides.
- Typography: Korean sans serif with full Hangul coverage (prefer Noto Sans CJK KR); math in a consistent TeX face. Minimum body size should remain legible at 1080p, with titles/equations inside a 5% title-safe margin.
- Motion grammar: joint rotations drive all downstream geometry as a parented chain. Never animate a child link independently in a way that breaks the fixed joint connection. Hold each completed equation or final coordinate result for at least 2 s.

## Handoff acceptance checks

- Exactly six scenes and exactly two Blender shots (Scenes 1 and 4).
- Korean narration fits `150–180 s`; target `168 s`.
- Planar derivation uses `α, β`; the 3D screen uses `θ1, θ2, θ3` (`q1,q2,q3` allowed internally).
- Shoulder height `h=0.6 m` appears in `T01` and final `z`.
- Positive pitch visibly raises the link and is implemented with `Ry(-θ)`.
- Shoulder motion affects both downstream links; elbow motion affects link 2 and frame `{3}` only.
- Frame `{3}` origin and the amber end-effector point `P` coincide.
- `T03=T01T12T23` and `[pEE;1]=T03[0,0,0,1]^T` appear exactly once in the derivation scene and once, compactly, only if needed in the recap.
