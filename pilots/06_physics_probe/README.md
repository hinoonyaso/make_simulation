# 실제 물리 구동 확인 파일럿

## 목적과 결정
현재 설명 영상의 Manim 전개를 유지하면서 Blender 구간에 실제 모터·바닥·장애물 반응을 넣을 수 있는지 확인한다. 전체 교육 영상이 아니라 **8초 무음 비교 실험**이다. 앞 4초는 장애물 없음, 뒤 4초는 드럼 있음이며 모두 2배속이다.

`physics_run.py`에서 Blender 5.2.1 LTS의 Bullet rigid body 엔진이 동적 차체, 바퀴, 접촉을 계산한다. 바퀴에는 각속도 모터 명령만 입력하고 로봇 위치와 회전은 키프레임으로 지정하지 않았다. `blender_scene.py`의 위치 키프레임은 계산 후 저장한 결과를 정확히 재생하기 위한 렌더 단계이다.

키프레임 주행은 접촉 반응의 근거가 될 수 없어 사용하지 않았다. 추가 엔진 설치 대신 이미 설치된 Blender를 사용했다. 기존 스튜디오 키트로 TurtleBot3 외형·복도·드럼·조명을 재사용했다.

## 데이터와 모형 경계
새 `data/`만 생성했다. 기존 `topics/`와 공용 키트는 수정하지 않았다. 교육용 단순 물리 모형이며 **실제 Nav2 또는 DWB 실행이 아니다**. 센서, 경로 계획, 제어 피드백이 없고 동일한 개방 루프 모터 명령을 비교한다.

차체 충돌체는 0.26×0.22×0.06m 상자, 질량 1.6kg이다. 실제 TurtleBot3 URDF와 일치하는 동역학 모형이 아니다. 바퀴 반경 0.033m, 윤거 0.288m, 마찰 계수와 저마찰 고정 캐스터는 단순화되어 있다. Blender 자동 관성 계산을 사용했고 하드웨어로 보정하지 않았다. 시각 외형과 충돌 상자 사이에 차이가 있다. 접촉 힘이나 솔버 접촉 manifold를 내보내지 않았으므로 정지 현상을 힘 측정으로 해석하지 않는다.

30fps, 중력 −9.81m/s², 프레임당 8 substeps, solver 50회, collision margin 1mm. 0.5초 안정화 후 목표 모터 속도 −6.060606rad/s. 부호는 조인트 축 관례에 따라 실제 전진 결과로 확인했다. 처음 반대 방향으로 움직인 `diagnostic_motor_sign_*`도 보존했다. 설정 전체는 trace에 포함된다.

## 확인한 결과
`output/physics_review.json`에 실행 측정값과 판정 범위가 있다.

| 항목 | 장애물 없음 | 드럼 있음 |
|---|---:|---:|
| 8초 전진 거리 | 1.24894m | 0.73092m |
| 반복 실행 최대 위치 차이 | 0m | 0m |
| substeps 16으로 변경한 끝 위치 차이 | 0.05348m | 0.02452m |
| 마지막 1초 최대 전진 속도 | 0.19917m/s | 0.00768m/s |

V9 trace 6개 검증 PASS. 동일 조건 위치 반복 검사 PASS. 16 substeps에서도 진행/정지 구분 유지. 끝 위치 6cm 이내라는 파일럿 판정 범위를 통과했지만 **시간 간격 수렴이나 실제 로봇 정확도를 입증하지 않았다**. 옆방향 미끄러짐이 계산 간격에 민감하다.

## 재실행
저장소 루트의 프로젝트 환경에서:

```bash
uv run python pilots/06_physics_probe/validate_physics.py
uv run python scripts/check_scene_style.py pilots/06_physics_probe/blender_scene.py
```

Windows Blender에 `physics_run.py -- --name baseline --substeps 8`을 전달한다. repeat는 동일 설정, fine은 substeps 16이다. `blender_scene.py`는 baseline trace를 소비한다.

## 키트·스킬 발견
- 키트에는 동적 차체/바퀴의 모터·힌지·캐스터 구성과 솔버 상태 내보내기가 없다. 로컬에서 먼저 만들었다. 반복 검증 후 키트 후보: articulated drive builder, solver trace exporter, measured wheel orientation replay.
- 목표 각속도의 부호를 시각적 전진 가정만으로 정하면 틀릴 수 있다. 작은 전진 실험으로 축 부호 확인이 필요하다.
- trace schema PASS는 물리 타당성 PASS가 아니다. 반복 실행, 계산 간격 민감도, 모형 한계와 렌더 재생의 출처를 별도로 기록한다.
- 기존 revision_04 데이터와 이번 물리 결과는 다른 모형이다. 한 영상에 넣을 때 동일 실행의 Manim 설명을 새로 연결해야 한다.

## 근거
- 로컬 `assets/turtlebot3/urdf/turtlebot3_waffle_pi.urdf`: 시각 좌표와 이번 단순 모형의 차이 확인.
- [Blender motor constraint API](https://docs.blender.org/api/5.1/bpy.types.RigidBodyConstraint.html): 모터 설정. 실행 중 5.2.1 속성 존재 확인.
- 실제 실행 데이터와 검증 스크립트가 결과 근거이며 영상 외형만으로 물리 정확도를 주장하지 않는다.

스타일 검사는 렌더 장면 PASS. 물리 계산 스크립트에는 스튜디오 키트 미사용 WARN이 있다. 이는 외형 렌더가 아닌 솔버 전용 파일이고 스튜디오 초기화로 동적 월드를 덮어쓰지 않기 위한 분리이다. 키트 자체 수정은 없다.

## 영상 검사
`output/physics_probe_ko.mp4`: 1920×1080, 30fps, 8초, 의도적 무음. Manifest require-media 및 delivery full-decode PASS. render-reviewer 방식으로 인코딩된 실제 프레임 5개를 확인했고 해당 범위 blocker/high 0개. 정상 속도 동영상 재생 검토는 미완료이므로 전체 교육 품질 PASS로 표시하지 않았다. 낮은 샘플 프리뷰의 표면 노이즈와 드럼 면 분할은 본편 제작 시 다듬을 항목이다. `output/render_review.json`에 범위를 기록했다.
