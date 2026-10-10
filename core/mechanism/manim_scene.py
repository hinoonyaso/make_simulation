"""Small data-driven Manim renderer for the current executable mechanism pilots."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys

import numpy as np
from manim import *

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "core/manim-robotics-education-skill/templates"))
from manim_kit import apply_theme, txt, P
from core.mechanism.storyboard import validate_phase_contract
from core.mechanism.timeline import validate_timeline
from core.mechanism.pid_playback import PIDPlayback
from core.mechanism.engineering_playback import (
    engineering_state_for_frame, interpolation_for_signal, source_time_to_x,
)


def text(value, size=24, color=P.fg, width=None):
    mob = txt(str(value), size=size, color=color)
    if width and mob.width > width:
        mob.scale_to_fit_width(width)
    return mob


def polyline(points, color, width=3):
    line = VMobject(color=color, stroke_width=width)
    return line.set_points_as_corners([np.array(point, dtype=float) for point in points])


def flat_values(value):
    return np.asarray(value, dtype=float).reshape(-1)[:12]


class MechanismTraceScene(Scene):
    def construct(self):
        apply_theme(self)
        plan_path = Path(os.environ["V11_VISUAL_PLAN"])
        manifest_path = Path(os.environ["V11_VISUAL_MANIFEST"])
        self.plan = json.loads(plan_path.read_text(encoding="utf-8"))
        self.manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        beats = self.manifest["beats"]
        timeline = json.loads(Path(os.environ["V11_TIMELINE_PATH"]).read_text(encoding="utf-8"))
        errors = validate_timeline(timeline, expected_phase_ids=[beat.get("phase_id") for beat in beats])
        if errors:
            raise ValueError("invalid shared mechanism timeline: " + "; ".join(errors))
        self.timeline = timeline
        fps = timeline["fps"]
        if fps != 30:
            raise ValueError("common Manim renderer requires a 30 fps shared timeline")
        phases = {phase["phase_id"]: phase for phase in timeline["phases"]}
        title_mob = text(self.plan["title"], 34, P.fg, 13.2).to_edge(UP, buff=.35)
        self.add(title_mob)
        if self.plan["kind"] == "mcu_pid":
            self._render_pid(timeline)
            return
        isolate_phases = self.plan["kind"] == "engineering"
        graphic, transitions = self._build_graphic()
        errors = validate_phase_contract(beats, transitions)
        if errors:
            raise ValueError("invalid storyboard/renderer phase contract: " + "; ".join(errors))
        for index, beat in enumerate(beats):
            if isolate_phases:
                self.clear()
                self.add(title_mob)
            phase = phases[beat["phase_id"]]
            duration_frames = phase["presentation_end_frame"] - phase["presentation_start_frame"]
            duration = duration_frames / fps
            caption = text(beat["caption"], 20, P.muted, 12.5).move_to([0, -3.1, 0])
            header = text(f"{index+1:02d} / {len(beats):02d}", 16, P.active).to_corner(UR, buff=.4)
            anims = [FadeIn(header), FadeIn(caption)]
            # State transitions historically encoded outgoing objects with
            # FadeOut, but some builders reused a parent VGroup or omitted
            # stale children. Replace the complete per-beat scene state and
            # run only its incoming animations for deterministic isolation.
            state_animations = transitions[beat["phase_id"]]
            if isolate_phases:
                state_animations = [animation for animation in state_animations
                                    if not isinstance(animation, FadeOut)]
            anims.extend(state_animations)
            state_runtime = max([value for animation in state_animations
                                 if isinstance((value := getattr(animation, "run_time", .6)), (int, float))] + [.6])
            minimum_frames = max(1, int(round(state_runtime * fps)))
            if minimum_frames > duration_frames:
                raise ValueError(f"phase {beat['phase_id']} needs {minimum_frames} transition frames, "
                                 f"only {duration_frames} presentation frames are available")
            cursor_spec = getattr(self, "_phase_cursors", {}).get(beat["phase_id"])
            if cursor_spec:
                cursor, time_label, x0, x1, y_bottom, y_top = cursor_spec
                driver = ValueTracker(0)
                observed = getattr(self, "_engineering_frame_observed", None)
                if observed is None:
                    observed = self._engineering_frame_observed = {}

                def update_cursor(frame_index):
                    state = engineering_state_for_frame(self.plan, self.timeline, frame_index)
                    x = source_time_to_x(state["source_time_sec"], self.timeline["source_range_sec"], x0, x1)
                    cursor.put_start_and_end_on([x, y_bottom, 0], [x, y_top, 0])
                    time_label.become(text(f"source t = {state['source_time_sec']:.4f} s", 14, P.active)
                                      .move_to([x0 + 1.45, y_bottom - .3, 0]))
                    observed[frame_index] = state

                def cursor_animation(first_frame, span):
                    def update(_, alpha):
                        frame_index = first_frame + min(span - 1, int(round(alpha * span)))
                        update_cursor(frame_index)
                    return UpdateFromAlphaFunc(driver, update, rate_func=linear)

                start_frame = phase["presentation_start_frame"]
                self.play(*anims, cursor_animation(start_frame, minimum_frames),
                          run_time=minimum_frames / fps)
                remaining_frames = duration_frames - minimum_frames
                if remaining_frames:
                    self.play(cursor_animation(start_frame + minimum_frames, remaining_frames),
                              run_time=remaining_frames / fps)
            else:
                self.play(*anims, run_time=minimum_frames / fps)
                self.wait((duration_frames - minimum_frames) / fps)
            if isolate_phases:
                self.clear()
            else:
                self.remove(header, caption)
        debug_path = os.environ.get("V121_ENGINEERING_FRAME_DEBUG")
        if debug_path and getattr(self, "_engineering_frame_observed", None) is not None:
            Path(debug_path).write_text(json.dumps(
                [self._engineering_frame_observed[i] for i in sorted(self._engineering_frame_observed)],
                ensure_ascii=False), encoding="utf-8")

    def _build_graphic(self):
        kind = self.plan["kind"]
        if kind == "quantization":
            graphic, rows = self._quantization()
            keys = ["input", "integer_mapping", "dequantization"]
            if self.plan.get("activation_quantization"):
                keys.append("activation_quantization")
            return graphic, dict(zip(keys, rows))
        if kind == "nms": return self._nms()
        if kind == "mujoco_arm":
            graphic, rows = self._mujoco_arm()
            return graphic, dict(zip(["robot_setup", "joint_state", "end_effector_motion"], rows))
        if kind == "self_attention":
            graphic, rows = self._self_attention()
            return graphic, dict(zip(["input_projection", "qk_scores", "scaling_mask", "softmax", "weighted_value"], rows))
        if kind == "engineering": return self._engineering()
        raise ValueError(f"no Manim visual plan for mechanism: {kind}")

    def _engineering(self):
        """Shared trace based waveforms, event lanes, labels and equation state views."""
        p, topic = self.plan, self.plan["topic"]
        muted, active, result, sensor = P.muted, P.active, P.result, P.sensor
        board = Line([-5.8, -2.35, 0], [5.8, -2.35, 0], color=P.faint, stroke_width=1)

        def label(value, y=1.9, color=muted, size=24):
            return text(value, size, color, 11.5).move_to([0, y, 0])

        self._phase_cursors = {}

        def curve_group(signal_names, title_text, *, phase_id=None, x0=-5.5, x1=5.5,
                        plot_bottom=-1.65, plot_top=1.05, title_y=2.0):
            signals = p["signals"]
            available = [(name, signals[name]) for name in signal_names if name in signals]
            if not available:
                return VGroup(label(title_text), label("Trace 표본 없음", 0, P.error)), []
            source_range = self.timeline.get("source_range_sec")
            if not source_range or len(source_range) != 2 or source_range[1] <= source_range[0]:
                raise ValueError("engineering waveform requires a positive shared source-time range")
            units = {signal["unit"] for _, signal in available}
            stacked = len(units) > 1
            palette = [active, result, sensor, P.error]
            short_names = {"position":"x", "velocity":"v", "kinetic_energy":"K", "potential_energy":"U",
                           "total_energy":"E", "external_force":"F", "analytic_position":"x analytic",
                           "position_undamped":"c=0", "position_critical":"critical c",
                           "position_overdamped":"over c",
                           "phase_current_a":"i_a", "phase_current_b":"i_b", "phase_current_c":"i_c",
                           "current_d":"i_d", "current_q":"i_q", "torque":"τ", "torque_reference":"τ ref",
                           "current_d_reference":"i_d ref", "current_q_reference":"i_q ref",
                           "current_d_feedback":"i_d fb", "current_q_feedback":"i_q fb",
                           "speed_rad_s":"ω", "speed_reference":"ω ref", "speed_rpm":"rpm", "load_torque":"τ load"}
            graph = VGroup(label(title_text, title_y, muted, 22),
                           Line([x0,plot_bottom,0],[x1,plot_bottom,0],color=P.faint),
                           Line([x0,plot_bottom,0],[x0,plot_top,0],color=P.faint),
                           text(f"{source_range[0]:.4g} s",13,muted).move_to([x0+.35,plot_bottom-.2,0]),
                           text(f"{source_range[1]:.4g} s",13,muted).move_to([x1-.35,plot_bottom-.2,0]))
            anims = [FadeIn(graph[0]), Create(graph[1]), Create(graph[2]),
                     FadeIn(graph[3]), FadeIn(graph[4])]
            lane_height = (plot_top - plot_bottom) / max(1, len(available)) if stacked else plot_top-plot_bottom
            for idx, (name, signal) in enumerate(available):
                times = np.asarray(signal.get("timestamps", p.get("timestamps", [])), dtype=float)
                values = np.asarray(signal["values"], dtype=float)
                stride = max(1, len(values)//700)
                indices = list(range(0, len(values), stride))
                if indices[-1] != len(values)-1:
                    indices.append(len(values)-1)
                times, values = times[indices], values[indices]
                if len(times) < 2: continue
                xs = [source_time_to_x(float(t), source_range, x0, x1) for t in times]
                low, high = float(np.min(values)), float(np.max(values))
                if abs(high-low) < 1e-12:
                    low, high = low-1, high+1
                if stacked:
                    lane_bottom = plot_bottom + idx*lane_height + .08
                    lane_top = plot_bottom + (idx+1)*lane_height - .08
                else:
                    lane_bottom, lane_top = plot_bottom+.08, plot_top-.08
                ys = lane_bottom + (values-low)/(high-low)*(lane_top-lane_bottom)
                policy = interpolation_for_signal(name)
                points = []
                if policy == "zero_order_hold":
                    for sample_index, (x_value, y_value) in enumerate(zip(xs, ys)):
                        if sample_index:
                            points.append([float(x_value), float(ys[sample_index-1]), 0])
                        points.append([float(x_value), float(y_value), 0])
                    points.append([x1, float(ys[-1]), 0])
                else:
                    points = [[float(x_value),float(y_value),0] for x_value,y_value in zip(xs,ys)]
                    if times[-1] < source_range[1]:
                        points.append([x1, float(ys[-1]), 0])
                line = polyline(points, palette[idx % len(palette)], 3)
                if stacked:
                    tag_x = x0 + min(2.2, (x1 - x0) * .2)
                    tag_y = lane_top-.13
                    tag_width = 4.3
                else:
                    # Same-unit curves share one quantitative axis. Present
                    # their value ranges as a compact horizontal legend so
                    # labels do not overlap while descending over the plot.
                    tag_x = x0 + (idx + .5) * (x1 - x0) / len(available)
                    tag_y = 1.48
                    tag_width = min(3.2, (x1 - x0) / len(available) - .15)
                tag = text(f"{short_names.get(name, name)} · {signal['unit']}  [{low:.3g}, {high:.3g}]", 14 if stacked else 16,
                           palette[idx % len(palette)], tag_width)
                tag.move_to([tag_x, tag_y, 0])
                graph.add(line, tag)
                anims.extend([Create(line), FadeIn(tag)])
            cursor = Line([x0,plot_bottom,0],[x0,plot_top,0],color=P.active,stroke_width=2.5)
            time_label = text(f"source t = {source_range[0]:.4f} s",14,P.active).move_to([x0+1.45,plot_bottom-.3,0])
            graph.add(cursor, time_label)
            anims.extend([FadeIn(cursor), FadeIn(time_label)])
            if phase_id:
                self._phase_cursors[phase_id] = (cursor,time_label,x0,x1,plot_bottom,plot_top)
            return graph, anims

        if topic == "physics_oscillator":
            q = p["parameters"]
            x = float(p["signals"]["position"]["values"][0])
            mass = Square(.65, color=active, fill_opacity=.35).move_to([-3.3, 0, 0])
            mass_label = text(f"m={q['mass_kg']:g} kg", 18, P.fg).next_to(mass, DOWN, buff=.15)
            wall = Line([-5, -.5, 0],[-5, .5, 0],color=muted,stroke_width=5)
            spring_pts = [[-5+.10*i, .25+.15*((-1)**i),0] for i in range(1, 14)] + [[-3.63,.25,0]]
            spring = polyline(spring_pts, sensor, 3)
            dashpot = VGroup(Line([-4.7,-.55,0],[-4.7,-.15,0],color=result,stroke_width=3),
                             Rectangle(width=.48,height=.24,color=result).move_to([-4.32,-.35,0]),
                             Line([-4.08,-.35,0],[-3.63,-.35,0],color=result,stroke_width=3))
            setup = VGroup(wall,spring,dashpot,mass,mass_label,
                           label(f"초기 변위 x₀={x:.3f} m", -1.05, active, 19),
                           label("질량의 운동 → 스프링 복원력 + 감쇠력", 1.05, muted, 20))
            eq = VGroup(label(p["equation"],.75,active,30),
                        label(f"m={q['mass_kg']:g} kg   c={q['damping_n_s_m']:g} N·s/m   k={q['stiffness_n_m']:g} N/m",-.15,muted,20),
                        label(f"초기 조건: x(0)={q['initial_displacement_m']:g} m,  ẋ(0)={q['initial_velocity_m_s']:g} m/s",-.85,sensor,18))
            response, resp_anim = curve_group(["position","velocity"],"SciPy 수치 적분 · 공통 원본 시간축",
                                               phase_id="response")
            energy, energy_anim = curve_group(["kinetic_energy","potential_energy","total_energy"],
                                               "같은 해에서 계산한 에너지 · J",phase_id="validation")
            validation = p["validation"]
            validation_group = VGroup(label(f"SciPy DOP853 · SymPy 비교 오차 {validation['max_abs_analytic_error_m']:.2g} m" if validation.get("max_abs_analytic_error_m") is not None else "강제 응답: SciPy 적분 결과",.65,result,22),
                                      label(f"에너지 수지 잔차 {validation['energy_balance_residual_j']:.2g} J",-.05,active,21),
                                      label("각 곡선은 trace의 실제 계산 표본을 사용",-.8,muted,18))
            damping, damping_anim = curve_group(["position_undamped","position","position_critical","position_overdamped"],
                "감쇠별 위치 응답 · m",phase_id="damping")
            return VGroup(board,setup,eq,response,energy,validation_group,damping), {
                "setup":[FadeIn(setup)], "equation":[FadeOut(setup),FadeIn(eq)],
            "solution":[FadeOut(eq),FadeIn(validation_group)],
            "response":[FadeOut(validation_group),*resp_anim],
            "validation":[FadeOut(response),*energy_anim],
                "damping":[FadeOut(energy),FadeOut(validation_group),*damping_anim]}

        if topic == "can_arbitration":
            requests = p["requests"]
            request_lines = VGroup(*[text(f"{row['node']}  ID 0x{row['id']:03X}  {row['data_hex'] or 'RTR'}",
                                          22, active if row["node"] in p["winners"] else sensor, 10.5)
                                    for row in requests]).arrange(DOWN,buff=.42).move_to([0,.5,0])
            setup = VGroup(label("Classical CAN 2.0A · 표준 11비트 프레임",1.2,muted,22),request_lines)
            bits = np.asarray(p["bits"],dtype=int)
            fields = p["fields"]
            def digital_view(title, end, marked=False):
                end=max(1,min(int(end),len(bits)))
                start_x=-5.5; width=11.0/end
                top=1.0; low=-.7
                g=VGroup(label(title,1.8,muted,21),Line([-5.5,-1.05,0],[5.5,-1.05,0],color=P.faint))
                points=[]
                for i,b in enumerate(bits[:end]):
                    x=start_x+i*width; yy=top if b else low
                    points.extend(([x,yy,0],[x+width,yy,0]))
                    if i+1<end and bits[i+1]!=b: points.append([x+width,low if b else top,0])
                wave=polyline(points,active,3); g.add(wave)
                marker_mobs=[]
                if end <= 24:
                    for i,b in enumerate(bits[:end]):
                        g.add(text(str(int(b)),12,active if b==0 else muted).move_to([start_x+(i+.5)*width,-1.32,0]))
                if marked:
                    for item in p["events"]:
                        if item["event"] in {"ARBITRATION_LOST","ARBITRATION_WON"}:
                            xx=start_x+min(item["timestamp"],end)*width
                            marker=DashedLine([xx,-1.65,0],[xx,1.15,0],
                                              color=P.error if item["event"]=="ARBITRATION_LOST" else result)
                            marker_mobs.append(marker)
                            g.add(marker)
                return g, [FadeIn(g[0]),Create(g[1]),Create(wave),
                           *[Create(marker) for marker in marker_mobs]]
            request=VGroup(label("동시에 송신 요청",.55,active,25),*[
                text(f"{row['node']} → ID 비트 전송",19,sensor).move_to([0,.05-i*.42,0])
                for i,row in enumerate(requests)])
            arbitration,arb_anim=digital_view("중재 필드 · dominant 0이 recessive 1을 덮음", min(13,len(bits)), True)
            frame,frame_anim=digital_view("실제 생성된 프레임 비트열 · stuffing 포함",len(bits),False)
            status=VGroup(label("승자: "+(", ".join(p["winners"]) or "없음"),.75,result,27),
                          label(f"bitrate {p['bitrate_hz']/1000:g} kbit/s · {p['bit_count']} bits · ACK {'수신' if p['acknowledged'] else '없음'}",-.05,active,20),
                          label("CRC-15/CAN 0x4599 · receiver가 없으면 ACK 실패",-.8,muted,17))
            return VGroup(board,setup,request,arbitration,frame,status), {
                "bus_setup":[FadeIn(setup)], "simultaneous_request":[FadeOut(setup),FadeIn(request)],
                "arbitration":[FadeOut(request),*arb_anim],
                "frame_transmission":[FadeOut(arbitration),*frame_anim],
                "result":[FadeOut(frame),FadeIn(status)]}

        # PMSM FOC uses independently sampled solver and controller signals.
        pmsm_setup=VGroup(label("PMSM + Field-Oriented Control",.9,active,25),
                          label("motulator 0.9 · sensored model state",.1,muted,20),
                          label("평균화 인버터 · 고주파 스위칭 파형 미포함",-.7,P.error,18))
        three,three_anim=curve_group(["phase_current_a","phase_current_b","phase_current_c"],
                                     "3상 고정자 전류 · A_peak",phase_id="three_phase_current")
        dq,dq_anim=curve_group(["current_d","current_q"],"회전자 기준 d/q축 전류 · A_peak",
                               phase_id="dq_transform")
        dq_formula=text("theta_e = p * theta_m   |   i_abc -> i_alpha_beta -> i_dq",16,active,8.0).move_to([0,-2.08,0])
        dq.add(dq_formula); dq_anim.append(FadeIn(dq_formula))
        torque,torque_anim=curve_group(["current_q_reference","current_q_feedback"],
            "q축 전류 지령과 피드백 · 제어 샘플 · A_peak",phase_id="current_control")
        speed,speed_anim=curve_group(["speed_reference","speed_rad_s"],
            "속도 지령과 회전자 응답 · 공통 원본 시간축 · rad/s",phase_id="speed_response")
        load,load_anim=curve_group(["load_torque","current_q_feedback","speed_rad_s"],
            "부하 외란 · 신호별 단위/세로축, 공통 시간축",phase_id="load_disturbance",
            x0=-5.2,x1=5.2,plot_bottom=-1.55,plot_top=1.0,title_y=1.9)
        return VGroup(board,pmsm_setup,three,dq,torque,speed,load), {
            "machine_setup":[FadeIn(pmsm_setup)],
            "three_phase_current":[FadeOut(pmsm_setup),*three_anim],
            "dq_transform":[FadeOut(three),*dq_anim],
            "current_control":[FadeOut(dq),*torque_anim],
            "speed_response":[FadeOut(torque),*speed_anim],
            "load_disturbance":[FadeOut(speed),FadeOut(pmsm_setup),*load_anim]}

    def _quantization(self):
        p = self.plan
        original, quantized, restored = (flat_values(p[key]) for key in ("original", "quantized", "dequantized"))
        x0, x1, y = -5.4, 5.4, .25
        qmin, qmax = int(p["qmin"]), int(p["qmax"])
        real_low = min(float(np.min(original)), float(np.min(restored)), 0.0)
        real_high = max(float(np.max(original)), float(np.max(restored)), 0.0)
        def normalize(value, low, high):
            return 0.0 if high <= low else 2.0 * (float(value) - low) / (high - low) - 1.0
        axis = Line([x0, y, 0], [x1, y, 0], color=P.faint)
        axis_labels = VGroup(text("실수 가중치", 18, P.muted).move_to([-4.5, 1.3, 0]),
                             text(f"{p['bits']}비트 정수 코드", 18, P.active).move_to([0, 1.3, 0]),
                             text("복원값과 오차", 18, P.result).move_to([4.5, 1.3, 0]))
        positions = np.linspace(x0 + .6, x1 - .6, len(original))
        original_dots = VGroup()
        quant_dots = VGroup()
        restored_dots = VGroup()
        value_labels = VGroup()
        for i, (value, q, deq, x) in enumerate(zip(original, quantized, restored, positions)):
            y0 = y + normalize(value, real_low, real_high) * 1.15
            # Place the integer code on the same calibrated interval as its
            # dequantized real value; this makes zero_point's offset visible.
            yq = y + normalize(q, qmin, qmax) * 1.15
            yd = y + normalize(deq, real_low, real_high) * 1.15
            original_dots.add(Dot([x, y0, 0], radius=.075, color=P.muted))
            quant_dots.add(Square(.15, color=P.active, fill_opacity=.8).move_to([x, yq, 0]))
            restored_dots.add(Dot([x, yd, 0], radius=.07, color=P.result))
            value_labels.add(text(f"{value:.2f}", 13, P.fg).move_to([x, -1.25, 0]))
        scale_label = text(f"scale={np.asarray(p['scale']).reshape(-1)[0]:.5g}   zero point={np.asarray(p['zero_point']).reshape(-1)[0]:g}   code=[{qmin}, {qmax}]",
                           21, P.active).move_to([0, 2.1, 0])
        error_text = f"가중치 최대 절대 오차 = {p['max_absolute_error']:.5g}"
        if p.get("activation_max_absolute_error") is not None:
            error_text += f"   활성값 최대 오차 = {p['activation_max_absolute_error']:.5g}"
        error_label = text(error_text, 18 if p.get("activation_max_absolute_error") is not None else 21,
                           P.result, 12.5).move_to([0, -2.15, 0])
        code_labels = VGroup(*[text(f"{int(value)}", 12, P.active).next_to(mob, DOWN, buff=.06)
                               for value, mob in zip(quantized, quant_dots)])
        activation_group = VGroup()
        activation = p.get("activation_quantization")
        if activation:
            activation_values = list(zip(flat_values(activation["original"]),
                                         flat_values(activation["quantized"]),
                                         flat_values(activation["dequantized"])))[:7]
            rows = [text(f"활성값 {i+1}: {x:.3f} → {int(q)} → {restored:.3f}", 17, P.sensor, 8.8)
                    for i, (x, q, restored) in enumerate(activation_values)]
            activation_group = VGroup(text("별도 보정 범위로 활성값을 변환", 20, P.sensor), *rows,
                text(f"weight 최대 오차={p['max_absolute_error']:.5g}", 16, P.result),
                text(f"activation scale={np.asarray(activation['scale']).reshape(-1)[0]:.5g} · "
                     f"zero point={np.asarray(activation['zero_point']).reshape(-1)[0]:g} · "
                     f"최대 오차={activation['max_absolute_error']:.5g}", 16, P.sensor, 11))
            activation_group.arrange(DOWN, buff=.17).move_to([0, 0, 0])
        graphic = VGroup(axis, axis_labels, original_dots, quant_dots, restored_dots, value_labels,
                         scale_label, error_label, code_labels)
        if activation:
            graphic.add(activation_group)
        return graphic, [[Create(axis), FadeIn(axis_labels), FadeIn(original_dots), FadeIn(value_labels)],
                         [FadeIn(quant_dots), FadeIn(code_labels), FadeIn(scale_label)],
                         [FadeIn(restored_dots), FadeIn(error_label)]] + ([[
                             FadeOut(axis), FadeOut(axis_labels), FadeOut(original_dots), FadeOut(quant_dots),
                             FadeOut(restored_dots), FadeOut(value_labels), FadeOut(code_labels),
                             FadeOut(scale_label), FadeOut(error_label), FadeIn(activation_group)] ] if activation else [])

    def _nms(self):
        p = self.plan
        boxes = np.asarray(p["boxes_xyxy"], dtype=float)
        if not len(boxes):
            canvas = Rectangle(width=7.8, height=4.0, color=P.faint).move_to([-2.3, -.1, 0])
            threshold = text(f"confidence ≥ {p['confidence_threshold']:.2f}    IoU threshold = {p['iou_threshold']:.2f}",
                             20, P.muted).move_to([2.7, 2.3, 0])
            empty = text("비교할 검출 후보가 없습니다.", 23, P.active, 6.5).move_to([-2.3, 0, 0])
            result = text("유지 상자: 없음", 20, P.result).move_to([2.7, -2.45, 0])
            return VGroup(canvas, threshold, empty, result), {
                "candidates": [Create(canvas), FadeIn(threshold), FadeIn(empty)],
                "final_result": [FadeIn(result)]}
        lo, hi = boxes[:, :2].min(axis=0), boxes[:, 2:].max(axis=0)
        span = np.maximum(hi - lo, 1.0)
        canvas = Rectangle(width=7.8, height=4.0, color=P.faint).move_to([-2.3, -.1, 0])
        palette = [P.sensor, P.active, P.result, P.error, P.muted]
        candidates = VGroup()
        candidate_groups = {}
        labels = VGroup()
        box_mobs = {}
        center = canvas.get_center()
        for i, (box, score, item_id) in enumerate(zip(boxes, p["scores"], p["ids"])):
            x1, y1 = (box[:2]-lo)/span
            x2, y2 = (box[2:]-lo)/span
            width, height = max(.18, (x2-x1)*6.8), max(.18, (y2-y1)*3.3)
            pos = [center[0]-3.4+(x1+x2)*3.4, center[1]+1.65-(y1+y2)*1.65, 0]
            color = palette[i % len(palette)]
            rect = Rectangle(width=width, height=height, color=color, stroke_width=3).move_to(pos)
            label = text(f"{item_id}  {score:.2f}", 15, color, 2.0).next_to(rect, UP, buff=.04)
            candidate = VGroup(rect, label)
            candidates.add(candidate); candidate_groups[item_id] = candidate; box_mobs[item_id] = rect
            labels.add(label)
        threshold = text(f"confidence ≥ {p['confidence_threshold']:.2f}    IoU threshold = {p['iou_threshold']:.2f}",
                         20, P.muted).move_to([2.7, 2.3, 0])
        kept_label = (f"최종 유지: {len(p['kept_ids'])}개" if not p["kept_ids"] else
                      f"최종 유지: {len(p['kept_ids'])}개 · " + ", ".join(p["kept_ids"]))
        result = text(kept_label, 18, P.result, 6.2).move_to([2.7, -2.45, 0])
        comparison_label = text("confidence 통과 후보를 점수 순서로 비교", 17, P.active, 5.0).move_to([3.55, .3, 0])
        graphic = VGroup(canvas, candidates, threshold, result, comparison_label)
        steps = p["steps"]
        confidence_pass = set(p["confidence_pass_ids"])
        filtered = [FadeOut(group) for item_id, group in candidate_groups.items() if item_id not in confidence_pass]
        filter_label = text(f"confidence 통과 {len(confidence_pass)} / {len(p['ids'])}개",
                            20, P.active).move_to([2.7, 1.35, 0])
        comparisons = []
        for step in steps:
            winner = step["selected_id"]
            if winner in box_mobs:
                comparisons.append(Indicate(box_mobs[winner], color=P.active, scale_factor=1.05))
            for item in step["comparisons"]:
                candidate = item["candidate_id"]
                if candidate not in box_mobs: continue
                decision = "억제" if item["suppressed"] else "유지"
                label = text(f"{winner} × {candidate}\nIoU {item['iou']:.3f} → {decision}",
                             18, P.error if item["suppressed"] else P.result, 4.8).move_to([3.55, .3, 0])
                comparisons.extend([Indicate(box_mobs[candidate], color=P.error if item["suppressed"] else P.result),
                                    Transform(comparison_label, label), Wait(.16)])
        if comparisons:
            comparisons.insert(0, FadeIn(comparison_label))
        comparison_sequence = Succession(*comparisons).set_run_time(3.3) if comparisons else Wait(.1)
        transitions = {"candidates": [Create(canvas), FadeIn(threshold), FadeIn(candidates)],
                       "confidence_filter": [*filtered, FadeIn(filter_label)],
                       "final_result": [*[mob.animate.set_stroke(color=P.result if item in p["kept_ids"] else P.muted)
                                           for item, mob in box_mobs.items()], FadeIn(result)]}
        if steps:
            transitions["iou_comparison"] = [comparison_sequence]
        return graphic, transitions

    def _render_pid(self, timeline):
        playback = PIDPlayback(self.plan, timeline)
        rows, p = self.plan['samples'], self.plan
        x0, x1, y0 = -5.8, 1.8, -1.3
        max_t = max(row['time_s'] for row in rows) or 1.
        scale = max(1., max(abs(row[k]) for row in rows
                           for k in ('target_rad_s', 'motor_speed_rad_s', 'encoder_speed_rad_s')))
        def x(t): return x0 + (x1-x0)*t/max_t
        def y(v): return y0 + 2.8*v/scale
        self.add(Line([x0,y0,0],[x1,y0,0],color=P.faint),
                 text("목표 / 모터 / 엔코더 · rad/s",18,P.muted).move_to([-2,2.6,0]),
                 text("PWM [-1, 1] · 기록된 표본 유지",17,P.muted).move_to([-2,-2.5,0]))
        def curve(key, color, discrete=False, pwm=False):
            points=[]
            previous=None
            for row in rows:
                value = row[key]
                yy = (-2+value*.35) if pwm else y(value)
                if discrete and previous is not None:
                    points.append([x(row['time_s']), previous, 0])
                points.append([x(row['time_s']), yy, 0]); previous=yy
            return polyline(points,color,2)
        self.add(curve('target_rad_s',P.active,True),curve('motor_speed_rad_s',P.result),
                 curve('encoder_speed_rad_s',P.sensor,True),curve('pwm_duty',P.active,True,True))
        cursor=Line([x0,y0-.1,0],[x0,2.1,0],color=P.active)
        encoder_dot=Dot(radius=.065,color=P.sensor)
        motor_dot=Dot(radius=.065,color=P.result)
        pwm_dot=Dot(radius=.065,color=P.active)
        panel=VGroup(); footer=VGroup()
        self.add(cursor,encoder_dot,motor_dot,pwm_dot,panel,footer)
        observed={}
        debug_path=os.environ.get('V115_FRAME_DEBUG')
        last_key=None
        def display(frame):
            nonlocal last_key
            state=playback.state(frame)
            source=state['source_time_sec']; sample=state['sample_time_sec']
            cursor.set_x(x(source))
            encoder_dot.move_to([x(sample),y(state['encoder_speed_rad_s']),0])
            motor_dot.move_to([x(sample),y(state['motor_speed_rad_s']),0])
            pwm_dot.move_to([x(sample),-2+state['pwm_duty']*.35,0])
            key=(state['phase_id'],state['sample_index'])
            if key != last_key:
                lines=[f"표본 {state['sample_index']} · t={sample:.2f}s",
                       f"목표 {state['target_rad_s']:.2f} · 오차 {state['error_rad_s']:.2f}",
                       f"P {state['p_term']:.3f}   I {state['i_term']:.3f}   D {state['d_term']:.3f}",
                       f"PWM {state['pwm_duty']:.3f}",
                       f"모터 {state['motor_speed_rad_s']:.2f} rad/s",
                       f"엔코더 {state['encoder_speed_rad_s']:.2f} rad/s",
                       f"누적 계수 {state['encoder_count']}"]
                panel.become(VGroup(*[text(v,18,P.fg,4.5) for v in lines]).arrange(DOWN,buff=.23,aligned_edge=LEFT).move_to([4.3,.2,0]))
                last_key=key
            footer.become(text(f"영상 프레임 {frame} · 원본 t={source:.3f}s · {state['playback_state']}",16,P.muted).move_to([0,-3.25,0]))
            if debug_path: observed[frame]=state
        for phase in timeline['phases']:
            start,end=phase['presentation_start_frame'],phase['presentation_end_frame']
            display(start)
            # Manim renders alpha=i/N, with finish(alpha=1) after the last frame.
            def update(_,alpha,start=start,end=end):
                display(min(end-1,start+int(round(alpha*(end-start)))))
            self.play(UpdateFromAlphaFunc(cursor,update,rate_func=linear),run_time=(end-start)/timeline['fps'])
        if debug_path:
            Path(debug_path).write_text(json.dumps([observed[i] for i in sorted(observed)],ensure_ascii=False),encoding='utf-8')

    def _mujoco_arm(self):
        p = self.plan
        samples = p["samples"]
        names = p["joint_names"]
        shoulder_i = names.index("left_shoulder_pitch_joint")
        elbow_i = names.index("left_elbow_joint")
        x0, y0, width, height = -5, -1.5, 10, 3.4
        axes = VGroup(Line([x0, y0, 0], [x0+width, y0, 0], color=P.faint),
                      Line([x0, y0, 0], [x0, y0+height, 0], color=P.faint))
        max_t = max(row["t"] for row in samples) or 1.0
        def curve(index, color, offset):
            vals = [row["qpos"][index] for row in samples]
            scale = max(max(abs(v) for v in vals), .1)
            pts = [[x0+width*row["t"]/max_t, y0+height*.5+height*.4*(row["qpos"][index]/scale), 0]
                   for row in samples]
            return polyline(pts, color, 3)
        shoulder, elbow = curve(shoulder_i, P.sensor, 0), curve(elbow_i, P.result, 0)
        labels = VGroup(text("실제 MuJoCo 관절 상태", 20, P.fg),
                        text("어깨", 17, P.sensor), text("팔꿈치", 17, P.result)).arrange(RIGHT,buff=.5).move_to([0, 2.5, 0])
        ee_points = [[row["ee_pos"][0], row["ee_pos"][1], 0] for row in samples]
        xvals = [point[0] for point in ee_points]; yvals = [point[1] for point in ee_points]
        dx, dy = max(max(xvals)-min(xvals), 1e-3), max(max(yvals)-min(yvals), 1e-3)
        ee_line = polyline([[-4.5+9*(x-min(xvals))/dx, -1+2*(y-min(yvals))/dy, 0]
                            for x,y in zip(xvals,yvals)], P.active, 4)
        graphic=VGroup(axes,shoulder,elbow,labels,ee_line)
        return graphic, [[Create(axes), FadeIn(labels)], [Create(shoulder), Create(elbow)], [Create(ee_line)]]

    def _self_attention(self):
        p = self.plan
        n = len(p["tokens"])
        projected_rows = []
        for index, token in enumerate(p["tokens"]):
            vector_text = lambda values: "[" + ", ".join(f"{float(v):.2f}" for v in values) + "]"
            projected_rows.append(text(f"토큰 {index+1}  {vector_text(token)}   →   "
                f"Q {vector_text(p['q'][index])}   K {vector_text(p['k'][index])}   V {vector_text(p['v'][index])}",
                17, P.fg, 12.2))
        projection = VGroup(text("입력 벡터를 세 경로로 투영", 24, P.active), *projected_rows)
        projection.arrange(DOWN, buff=.32).move_to([0, .1, 0])
        def matrix(values, title, color):
            values = np.asarray(values, dtype=float)
            group = VGroup()
            for row in range(values.shape[0]):
                for col in range(values.shape[1]):
                    value = float(values[row, col])
                    cell = Square(.78, color=color, stroke_width=1.4,
                                  fill_opacity=.12 + .65 * min(1.0, abs(value)))
                    cell.move_to([-.39*(values.shape[1]-1)+col*.82,
                                  .39*(values.shape[0]-1)-row*.82, 0])
                    label = text(f"{value:.2f}", 15, P.fg).move_to(cell)
                    group.add(VGroup(cell, label))
            title_mob = text(title, 23, color, 10).move_to([0, 2.25, 0])
            row_tags = VGroup(*[text(f"Q{i+1}", 14, P.muted).move_to([-2.2, .39*(n-1)-i*.82, 0]) for i in range(n)])
            col_tags = VGroup(*[text(f"K{i+1}", 14, P.muted).move_to([-.39*(n-1)+i*.82, 1.45, 0]) for i in range(n)])
            return VGroup(title_mob, row_tags, col_tags, group)
        raw = matrix(p["raw_scores"], "질문 Q × 키 Kᵀ : 내적 점수", P.active)
        has_mask = any(any(bool(value) for value in row) for row in p.get("causal_mask", []))
        scaled_title_text = f"차원으로 나눈 점수 · ÷ {p['scale_factor']:.2f}"
        if has_mask:
            scaled_title_text += " · 미래 위치 가림"
        scaled = matrix(p["scaled_scores"], scaled_title_text, P.sensor)
        weights = matrix(p["attention_weights"], "행마다 정규화한 softmax 가중치", P.result)
        raw_title, row_tags, col_tags, score_cells = raw.submobjects
        scaled_title, _, _, scaled_cells = scaled.submobjects
        weights_title, _, _, weight_cells = weights.submobjects
        mask_marks = VGroup()
        if has_mask:
            for row in range(n):
                for col in range(n):
                    if p["causal_mask"][row][col]:
                        mask_marks.add(Cross(scaled_cells[row*n+col], stroke_color=P.error, stroke_width=3))
        output = VGroup(*[text("출력 토큰 " + str(i+1) + "  →  " + ", ".join(f"{v:.2f}" for v in row), 21, P.result)
                          for i, row in enumerate(p["output"])])
        output.arrange(DOWN, buff=.3).move_to([0, .55, 0])
        value_rows = VGroup(*[text(f"V{i+1} = [" + ", ".join(f"{v:.2f}" for v in row) + "]", 16, P.sensor)
                              for i, row in enumerate(p["v"])])
        value_rows.arrange(DOWN, buff=.12).move_to([0, -1.3, 0])
        note = text("각 출력 = 해당 행의 가중치 × V", 20, P.active).move_to([0, 1.75, 0])
        def reveal(group):
            title, rows, cols, cells = group.submobjects
            return AnimationGroup(FadeIn(title), FadeIn(rows), FadeIn(cols),
                                  LaggedStart(*[FadeIn(cell, shift=UP*.08) for cell in cells], lag_ratio=.08),
                                  lag_ratio=.05).set_run_time(2.2)
        def matrix_update(cells, next_cells, old_title, next_title):
            move_cells = Transform(cells, next_cells).set_run_time(.65)
            change_title = AnimationGroup(FadeOut(old_title), FadeIn(next_title)).set_run_time(.65)
            return AnimationGroup(move_cells, change_title, lag_ratio=0).set_run_time(.65)
        return VGroup(projection, raw, scaled, weights, output, note), [
            [FadeIn(projection)],
            [FadeOut(projection), reveal(raw)],
            [matrix_update(score_cells, scaled_cells, raw_title, scaled_title),
             *([FadeIn(mask_marks)] if has_mask else [])],
            [*([FadeOut(mask_marks)] if has_mask else []),
             matrix_update(score_cells, weight_cells, scaled_title, weights_title)],
            [FadeOut(score_cells), FadeOut(row_tags), FadeOut(col_tags), FadeOut(weights_title),
             FadeIn(note), FadeIn(output), FadeIn(value_rows)]]
