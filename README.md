# Engineering Visual Lab

**Engineering Education Through Visualization**

공학·과학 개념을 재현 가능한 계산과 시각 자료로 설명하는 교육 영상 제작 프로젝트입니다. Manim으로 수식·그래프·2D 도식을 만들고, 필요한 장면은 Blender로 3D 구조와 동작을 보여줍니다. 일부 주제는 검증된 trace나 수치 모델을 렌더링에 연결하지만, CAD·FEM·CFD·전자기 Solver 자체를 제공하지는 않습니다.

> V12.1 정확도 개선과 V13 Education-First 기능은 각각 Merge Commit `d0e868c`, `0a2979b`로 `main`에 통합됐습니다.

## Quick Start

Ubuntu 24.04 / WSL2에서 Python 3.12와 `uv`를 준비한 뒤 프로젝트 환경을 설치합니다.

```bash
git clone https://github.com/hinoonyaso/make_simulation.git
cd make_simulation
sudo apt update
sudo apt install -y build-essential python3-dev pkg-config libcairo2-dev libpango1.0-dev ffmpeg fonts-nanum
uv sync --locked --group sim-render
```

가벼운 제작 계획 검증:

```bash
uv run python scripts/produce_lesson.py \
  --spec examples/education/education_smoke.json --plan-only
```

짧은 무음 미리보기 렌더:

```bash
uv run python scripts/produce_lesson.py \
  --spec examples/education/education_smoke.json --preview --manim-only
```

기본 출력 위치는 `pilots/v13_education/output/lessons/<run-id>/`입니다. Preview는 960×540, 30 fps이며, 영상과 문장 자막 파일을 생성합니다. 생성물은 Git에서 추적하지 않습니다.

## Overview

프로젝트는 학습 주제에 맞춰 설명 계획, 시각 장면, 계산 또는 trace, 영상 출력을 연결합니다. 교육용 asset library에는 절차적으로 만든 재사용 가능한 Blender 모델이 포함됩니다. 영상의 사실성은 사용한 모델·trace·수치 엔진의 범위에 따라 달라지며, 보기 좋은 렌더가 물리적 검증을 대신하지 않습니다.

## Key Features

| 기능 | 상태 | 범위 |
|---|---|---|
| 교육 lesson 제작 | Experimental | spec 기반 계획, Manim Preview, 선택적 TTS·자막 |
| 2D 수식·그래프 | Implemented | Manim 장면 및 기존 robotics/AI/engineering renderer |
| 3D 장면 | Optional | Blender 렌더·trace 재생. Blender 실행 환경 별도 필요 |
| 공학 계산 trace | Implemented by topic | oscillator, CAN arbitration, PMSM FOC 등 구현된 어댑터만 |
| Robotics / AI trace | Experimental | registry의 지원 수준과 입력 조건을 확인해야 함 |
| Asset registry | Implemented | 목록, 검색, 경로·메타데이터 검증 |
| TTS 및 자막 | Optional | `--with-tts`에서 Edge TTS와 음성 정렬 사용 |
| 전문 CAD·FEM·CFD 해석 | Not integrated | 별도 Solver 설치만으로 제작 파이프라인에 연결되지 않음 |

## Demo & Examples

저장소에는 일부 교육 asset의 PNG 미리보기는 있지만, 완성 MP4는 Git에 포함하지 않습니다. 아래 이미지는 모델 형상을 보여주는 asset preview이며, 시뮬레이션 결과나 완성 영상을 뜻하지 않습니다.

| 주제 | 자료 | 표현 |
|---|---|---|
| 베어링 6204 | [PNG](assets/education/generated/bearing_6204.png) · [spec](examples/education/bearing.json) | Blender asset 및 lesson |
| BLDC 모터 개념 모델 | [PNG](assets/education/generated/bldc_motor_concept.png) | 교육용 3D 자산 미리보기 |
| 적층 PCB | [PNG](assets/education/generated/pcb_layered.png) | 교육용 3D 자산 미리보기 |
| RAG | [trace](pilots/v10_rag_poc/data/ai_trace.json) | trace 기반 예시, 제한은 [pilot 문서](pilots/v10_rag_poc/README.md) 참조 |

위 파일이 현재 체크아웃에서 존재하는지 먼저 확인하세요. Preview 영상은 로컬 실행으로 생성하며, 무음 Preview는 나레이션 완성본이 아닙니다.

## Supported Environments

| 구성요소 | 확인된 버전·환경 | 필요 여부 | 참고 |
|---|---|---:|---|
| Linux | Ubuntu 24.04 / WSL2 | 권장 | 로컬 Python·Manim 경로 확인 |
| Python | `>=3.12`, 로컬 확인 3.12.3 | 필수 | `pyproject.toml` 기준 |
| uv | 로컬 확인 0.12.3 | 필수 | lockfile 환경 설치 |
| Manim Community | 0.21.0 | 렌더에 필요 | `sim-render` group |
| FFmpeg | 로컬 확인 6.1.1 | 미디어 출력에 필요 | 인코딩·검증 경로 |
| Blender | 로컬 확인 5.2.1 LTS (Windows) | 3D 장면에 선택 | WSL2에서 Windows 실행 연동은 환경별 설정 필요 |
| GPU | 요구하지 않음 | 선택 | 문서화된 CPU 계산·미리보기 경로 사용 가능 |

Ubuntu/WSL2 외 OS는 이 저장소에서 동일한 제작 절차가 검증됐다고 보장하지 않습니다. Windows Blender 실행은 설치 위치와 WSL interop에 따라 달라집니다. Blender 공식 설치 안내는 [blender.org](https://www.blender.org/download/)를 참고하세요.

## Requirements

기본 프로젝트 환경은 `uv.lock`에 고정된 Python dependency를 사용합니다. Manim의 Linux native dependency는 Cairo, Pango, compiler 도구와 FFmpeg를 포함합니다. 설치 세부 사항은 [Manim Linux 설치 문서](https://docs.manim.community/en/stable/installation/linux.html)를 참고하세요.

Blender는 Blender 장면이나 Blender asset을 생성·검증할 때만 필요합니다. STEP 자산을 다루는 일부 변환 경로에는 FreeCAD 같은 별도 변환기가 필요할 수 있습니다. TTS는 외부 Edge TTS 서비스에 텍스트를 보내므로 명시적으로 켤 때만 실행합니다.

## Installation & Setup

### 1. Clone 및 브랜치

```bash
git clone https://github.com/hinoonyaso/make_simulation.git
cd make_simulation
```

V12.1과 V13은 `main`에 통합됐습니다. 새 clone은 기본 `main` 브랜치를 사용하면 됩니다.

### 2. 시스템 패키지

```bash
sudo apt update
sudo apt install -y build-essential python3-dev pkg-config libcairo2-dev libpango1.0-dev ffmpeg fonts-nanum
```

`fonts-nanum`은 한국어 글꼴 렌더를 위해 CI와 로컬 경로에서 사용합니다.

### 3. Python 환경

```bash
uv sync --locked --group sim-render
```

저장소는 Python `>=3.12`를 요구합니다. `sim-render`는 Manim 렌더 의존성을 추가합니다. 기본 dependency에는 PyTorch 등 용량이 큰 패키지도 있으므로 첫 설치에 시간이 걸릴 수 있습니다. 설치하지 않은 선택 group의 주제를 실행할 때는 해당 group을 추가합니다.

```bash
uv sync --locked --group sim-math --group sim-can --group sim-motor --group sim-render
```

설치된 공학 엔진의 준비 상태를 확인합니다.

```bash
uv run python scripts/inspect_engineering_env.py
```

`uv` 설치는 [공식 안내](https://docs.astral.sh/uv/getting-started/installation/)를 따르세요.

### 4. Blender (선택)

Blender 기반 3D 제작에는 Blender 실행 파일이 필요합니다. 실행 경로는 제작 코드에서 `BLENDER_BIN` 환경 변수 또는 자동 탐색으로 정합니다. WSL2에서 Windows Blender를 쓸 경우 Linux 경로에서 실행 가능한지 먼저 점검하세요. 시스템 설치 및 interop 설정은 환경별로 다르며, WSL에서 Windows `.exe` 실행이 막힌 경우 Blender 장면은 해당 환경에서 렌더할 수 없습니다.

## Video Production

### Education lesson

```bash
# 입력과 장면 계획만 확인
uv run python scripts/produce_lesson.py --spec examples/education/bearing.json --plan-only

# 960x540, 30 fps 미리보기
uv run python scripts/produce_lesson.py --spec examples/education/bearing.json --preview

# Manim만 사용해 무음 preview
uv run python scripts/produce_lesson.py \
  --spec examples/education/education_smoke.json --preview --manim-only
```

`--preview`는 저해상도 검토 경로입니다. 기본 출력 root는 `pilots/v13_education/output/lessons`; `--output-root`로 변경할 수 있습니다. `--run-id`를 지정하면 해당 ID로 run 디렉터리를 만듭니다. 같은 경로를 재사용할 때는 기존 파일 덮어쓰기 여부를 먼저 확인하세요.

### Narration

기본 렌더는 무음입니다. 나레이션을 만들 때만 `--with-tts`를 추가합니다.

```bash
uv run python scripts/produce_lesson.py \
  --spec examples/education/bearing.json --preview --with-tts
```

이 경로는 대본을 Microsoft Edge TTS 서비스로 보내 음성을 만들고 Whisper 기반 정렬로 자막 타이밍을 산출합니다. 외부 서비스 연결과 모델 dependency가 필요합니다. 문장 자막은 lesson의 영상 산출물에 포함되며 세부 파일은 run 폴더에 생성됩니다.

### Existing topic renderer

기존 공학 주제는 registry를 확인한 뒤 topic CLI를 사용합니다.

```bash
uv run python scripts/inspect_capabilities.py
uv run python scripts/produce_video.py --topic physics_oscillator \
  --config examples/v12/oscillator.json --preview
uv run python scripts/produce_video.py --topic can_arbitration \
  --config examples/v12/can_arbitration.json --preview
uv run python scripts/produce_video.py --topic motor_foc \
  --config examples/v12/pmsm_foc.json --preview
```

이 경로는 technical preview이며, lesson 제작 CLI의 출력 형식·나레이션·완성도와 같다고 가정하지 마세요. Topic, dependency group, renderer 옵션은 [routing 안내](ROUTING.md)와 각 문서를 확인하세요.

## Engineering Simulation Engines

| 주제 | 구현된 계산·실행 | 중요한 범위 |
|---|---|---|
| Physics oscillator | SymPy / SciPy 기반 수치 모델 | 설정된 질량·감쇠·강성 조건에 한정 |
| CAN arbitration | 결정론적 Classical CAN 모델, `python-can` VirtualBus, `cantools` | 전기적 버스 파형이나 CAN FD가 아님 |
| PMSM FOC | `motulator` PMSM/vector-control 예제 | 데모 파라미터와 averaged converter 가정 |
| MuJoCo H1 arm | MuJoCo 3.7 trace 실행 | 모델·고정 베이스·제어 가정을 문서에서 확인 |
| YOLO object detection | 옵션 Ultralytics YOLO11n CPU 추론 | 필요한 weight와 Ultralytics 버전 별도 필요 |
| RAG | 로컬 lexical TF-IDF 또는 저장 trace | semantic embedding이나 LLM 생성 아님 |
| Quantization / NMS / PID / Self-Attention | 교육용 수치·합성 입력 모델 | 해당 모델이 실제 제품 runtime을 실행하지 않음 |

`scripts/inspect_capabilities.py`는 주제별 지원 수준을 출력합니다. DWB, MPPI, TEB, A* 등 일부 항목은 trace replay 또는 pilot 수준이며, 모두 실행 가능한 planner라고 보면 안 됩니다. PyBaMM, Renode, FEMM, Elmer, CalculiX, OpenFOAM 등의 전문 solver는 현재 통합 기능으로 문서화되어 있지 않습니다.

## 3D Assets & Sources

### Education asset library

교육용 procedural asset은 [catalog](assets/education/catalog.json)에 등록되어 있고 해당 폴더의 [README](assets/education/README.md)에 범위와 라이선스를 기록합니다. 현재 catalog에는 베어링, 기어, BLDC 개념 모델, PCB 층 구조, shaft/coupling assembly, 열·구조 부품 등 6개 생성 모델이 있습니다. 교육용 단순 형상이며 제품 CAD 치수, 전자기·접촉·열 해석 결과가 아닙니다.

`assets/education/LICENSE`는 프로젝트에서 직접 만든 교육용 asset에 CC0 1.0을 적용합니다. 이 라이선스는 외부 robotics asset이나 저장소 전체에 적용되지 않습니다.

### Robotics and device assets

모델의 출처와 사용 조건은 [asset index](assets/README.md), 개별 모델 README, [source/license matrix](docs/assets/SOURCE_LICENSE_MATRIX.md)에 기록합니다. 저장소에 포함된 로봇·센서 메시지는 원본 출처의 라이선스와 고지를 따릅니다. 각 폴더의 라이선스를 확인한 뒤 재사용하세요.

일부 원본 vendor CAD/STEP 파일은 크기·배포 조건 때문에 로컬 전용이며 Git clone에 포함되지 않습니다. 따라서 asset registry의 항목 수가 곧 clone에 실제 파일이 있다는 뜻은 아닙니다. 누락 및 변환 제한은 [missing asset report](docs/assets/MISSING_ASSETS.md), 현황은 [library status](docs/assets/LIBRARY_STATUS.md)를 참고하세요.

## Asset Management

```bash
# 등록 자산 목록 및 검색
uv run python scripts/manage_assets.py list
uv run python scripts/manage_assets.py search --category environment

# 현재 clone의 asset 파일 검증
uv run python core/visual-assets/asset_registry.py validate
uv run python scripts/acquire_education_assets.py --validate
```

`acquire_education_assets.py --plan`은 다운로드 계획을 검토합니다. 실제 다운로드는 명시적 허용 옵션과 출처·라이선스·크기·hash 검증 정보를 요구합니다. 사용 가능한 후보가 검증되지 않은 경우 다운로드가 거부됩니다. 변환 기능은 설정된 converter와 입력 형식에 제한되므로 자동으로 임의 STEP 파일을 변환한다고 가정하지 마세요.

## Project Structure

```text
core/                    공통 trace, renderer, asset registry
scripts/                 제작·검증·환경 확인 CLI
examples/education/      lesson spec 예제
examples/v12/            engineering trace 설정 예제
assets/education/        교육용 생성 asset 및 catalog
assets/<model>/          출처·라이선스별 robotics/device asset
pilots/                  주제별 PoC 및 실험
topics/                  기존 주제별 episode 자료
docs/                    아키텍처, 검증, asset 출처 문서
.github/workflows/       CI workflow 정의
```

## Validation & Testing

프로젝트의 전체 단위 검증:

```bash
uv run --offline python -m unittest discover -s tests -v
uv run --offline python -m compileall -q core scripts tests assets/education
uv run python core/visual-assets/asset_registry.py validate
uv run python scripts/acquire_education_assets.py --validate
uv run python scripts/inspect_engineering_env.py --check all
git diff --check
```

Manim smoke preview는 Quick Start 명령으로 실제 미디어를 생성하고 FFmpeg로 검사합니다. Blender 검증은 Blender 설치 및 실행 가능한 환경에서 수행합니다. CI 정의는 [workflow](.github/workflows/v13-education.yml)를 참고하세요.

**CI 상태 (2026-10-11, main `0a2979b`):** [AI trace run #35](https://github.com/hinoonyaso/make_simulation/actions/runs/38065253356), [V13 Education run #3](https://github.com/hinoonyaso/make_simulation/actions/runs/38065253393), [V12 Engineering run #10](https://github.com/hinoonyaso/make_simulation/actions/runs/38065253366)이 모두 성공했습니다. run #35에서 전체 155개 unittest를 통과했고, Education run은 실제 Manim smoke 미디어를 렌더·검증했습니다. V12 Engineering run은 physics, CAN, motor FOC, timeline 테스트와 세 편의 렌더·전체 디코드를 통과했습니다. V12.1 PR의 [run #7](https://github.com/hinoonyaso/make_simulation/actions/runs/38033443003)도 7개 check 모두 성공해 Merge Commit `d0e868c`로 main에 반영됐습니다. run #28의 Vendor CAD 오류는 9a43b20에서 수정되어, CAD가 없는 clone에서도 catalog·license·재배포 정책·Git 미추적 검사는 유지되고 로컬 파일 검사는 파일이 있을 때만 실행됩니다.

V13 전용 workflow는 교육 테스트만 실행하며, Python/Manim 패키지는 `uv.lock`의 `sim-render` group으로 설치합니다. education asset 검증, 계획 검증, Manim-only smoke, 960×540·30 fps·H.264 metadata, VTT와 production report, FFmpeg 전체 디코드를 검사하고 로그·미디어·리포트를 Artifact로 보관합니다. 교육 관련 경로를 바꾼 PR, `main`/`v13-education-first`의 관련 파일 push, 수동 dispatch에서 실행됩니다. 전체 회귀는 `ai-trace.yml`이 계속 담당합니다. main 통합 후 세 workflow의 성공은 위 run #35, #3, #10에서 확인했습니다.

| 검증 | 상태 | 범위 |
|---|---|---|
| AI trace 전체 unittest | PASS, 155/155 | main run #35 |
| V13 education unittest | PASS, 16/16 | main V13 run #3; `sim-render` locked environment |
| Asset registry / education asset validation | PASS | Registry 39 entries, 6 generated models |
| Education plan | PASS | `education_smoke.json`, concept-only |
| Manim smoke preview | PASS | [GitHub Actions main V13 run #3](https://github.com/hinoonyaso/make_simulation/actions/runs/38065253393), 960×540, 30 fps, silent, VTT/report present, full decode |
| Blender render | PASS (기록된 R6 로컬 검증) | Windows Blender 5.2.1 from WSL; Ubuntu CI에서는 실행하지 않음 |
| Narration/TTS | NOT TESTED | Smoke는 무음이며 외부 TTS를 호출하지 않음 |
| 최종 1080p 영상 검증 | NOT TESTED | CI preview는 960×540 무음 smoke |

## Current Capabilities & Limitations

- V13 lesson pipeline은 실험적이며, 주제별 출력과 renderer 지원이 다릅니다.
- 로컬에서 검증한 무음 smoke preview는 960×540, 30 fps입니다. 이는 1080p 완성 영상 검증이 아닙니다.
- TTS는 별도 선택이며, Edge TTS 서버로 대본 텍스트가 전송됩니다.
- Blender 렌더는 Blender 실행 파일과 환경 연동이 필요합니다. 현재 개발 환경에서 Windows Blender 5.2.1을 확인했지만 모든 WSL 설정에서 실행된다는 뜻은 아닙니다.
- Registry에는 clone에 없는 로컬 vendor 파일이 있을 수 있습니다. 자산별 README와 validation 결과를 확인하세요.
- 전문 해석기 미통합 상태를 플러그인 설치만으로 해결할 수 없습니다. 향후 통합 계획은 [TODO](assets/TODO.md)와 주제 문서를 확인하세요.
- 저장소 최상위에는 공통 `LICENSE`가 없습니다. 파일별·asset별 권리를 확인해야 합니다.

## Troubleshooting

| 증상 | 확인할 내용 |
|---|---|
| Manim 빌드가 Cairo/Pango를 찾지 못함 | 위 Ubuntu 패키지 설치 후 `uv sync --locked --group sim-render` 재실행 |
| 한글이 □로 출력됨 | `fonts-nanum` 설치 및 장면이 선택한 font family 확인 |
| `ffmpeg`를 찾지 못함 | `ffmpeg -version` 확인, 실행 파일이 `PATH`에 있는지 확인 |
| Blender subprocess가 WSL에서 시작되지 않음 | WSL interop, Windows 실행 파일 경로, `BLENDER_BIN` 설정 확인. 실패 시 Ubuntu native Blender 사용 |
| STEP 파일이 clone에 없음 | [asset status](docs/assets/LIBRARY_STATUS.md)에서 로컬 전용 여부와 converter 상태 확인 |
| SoX 관련 경고 | 무음 Manim smoke에서 경고만 발생하고 FFmpeg 출력 검증이 통과할 수 있음. 음성 처리 경로는 별도로 확인 |
| TTS 생성 실패 | 외부 연결, Edge TTS dependency와 서비스 응답 확인. `--with-tts`를 빼면 무음 경로 사용 가능 |
| 선택 엔진 누락 | `uv sync`에 해당 `sim-*` group을 추가하고 `inspect_engineering_env.py` 결과 확인 |

## References & Documentation

- [Routing and topic selection](ROUTING.md)
- [V13 education pipeline](docs/v13/README.md)
- [Asset index](assets/README.md)
- [Education asset library](assets/education/README.md)
- [Asset source/license matrix](docs/assets/SOURCE_LICENSE_MATRIX.md)
- [Asset library status](docs/assets/LIBRARY_STATUS.md)
- [Missing asset and conversion report](docs/assets/MISSING_ASSETS.md)
- [V12 architecture](docs/v12/V12_ARCHITECTURE.md)
- [V12 integration evidence](docs/v12/INTEGRATION_REPORT.md)
- [Manim Community Linux installation](https://docs.manim.community/en/stable/installation/linux.html)
- [uv installation](https://docs.astral.sh/uv/getting-started/installation/)
- [Blender download](https://www.blender.org/download/)

## License & Attribution

최상위 공통 라이선스는 현재 제공되지 않습니다. 코드, 개별 모델, 외부 trace와 생성 asset의 라이선스 및 출처는 각각의 파일·폴더 문서에서 확인하세요. 외부 모델을 복사하거나 변환해 재배포할 때는 upstream license와 attribution 조건을 그대로 따라야 합니다. 교육용 procedural asset의 CC0 고지는 [해당 LICENSE](assets/education/LICENSE)에 한정됩니다.
