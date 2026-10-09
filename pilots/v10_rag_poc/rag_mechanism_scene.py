"""Continuous, trace-driven RAG mechanics scene with a 2D embedding fallback."""
from pathlib import Path
import json
import sys
import numpy as np
from manim import *

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "core/manim-robotics-education-skill/templates"))
from manim_kit import apply_theme, txt, BeatClock, P

TRACE_PATH = HERE / "data/ai_trace.json"
TRACE = json.loads(TRACE_PATH.read_text(encoding="utf-8"))
VALUES = {item["id"]: item for item in TRACE["intermediate_values"]}
CHUNKS = [item for item in TRACE["intermediate_values"] if item["kind"] == "text_chunk"]
CHUNK_BY_ID = {item["id"]: item for item in CHUNKS}
QUERY = next(item for item in TRACE["inputs"] if item["kind"] == "query")
RANKING = sorted((item for item in TRACE["intermediate_values"]
                  if item["kind"] == "squared_l2_distance"), key=lambda item: item["rank"])
COORDS = {item["id"]: item["xy"] for item in TRACE["visualization"]["coordinates"]}
TOP = TRACE["outputs"][0]["retrieved_ids"]
SOURCE_LENGTH = len(TRACE["inputs"][0]["text"])


def label(s, size=26, color=P.fg, width=None):
    mob = txt(str(s), size=size, color=color)
    if width and mob.width > width:
        mob.scale_to_fit_width(width)
    return mob


def excerpt(chunk, limit=52):
    text = " ".join(chunk["value"].split())
    return text[:limit] + ("…" if len(text) > limit else "")


def heading(text):
    return label(text, 38, P.fg, 13.1).move_to([0, 3.25, 0])


def chunk_range_scene():
    """Render actual source offsets as aligned range bars, including overlap."""
    x0, width = -5.35, 10.7
    top_y, step = 1.95, .29
    rows = []
    for index, chunk in enumerate(CHUNKS):
        y = top_y - index * step
        start, end = chunk["char_start"], chunk["char_end"]
        left = x0 + width * start / SOURCE_LENGTH
        right = x0 + width * end / SOURCE_LENGTH
        span = Line([left, y, 0], [right, y, 0], color=P.muted, stroke_width=10)
        start_tick = Line([left, y-.09, 0], [left, y+.09, 0], color=P.faint, stroke_width=1.5)
        end_tick = Line([right, y-.09, 0], [right, y+.09, 0], color=P.faint, stroke_width=1.5)
        cid = label(chunk["id"], 18, P.fg).move_to([-6.1, y, 0])
        rows.append((VGroup(span, start_tick, end_tick, cid), left, right, y))
    ruler = VGroup(Line([x0, 2.25, 0], [x0+width, 2.25, 0], color=P.faint, stroke_width=1),
                   label("0", 15, P.muted).move_to([x0, 2.48, 0]),
                   label(str(SOURCE_LENGTH), 15, P.muted).move_to([x0+width, 2.48, 0]))
    return rows, ruler


class RAGMechanismPoC(Scene):
    def construct(self):
        apply_theme(self)
        title = heading("문서 범위가 청크로 나뉜다")
        self.add(title)

        # Segment 1: exact character windows from the recorded splitter output.
        with BeatClock(self, 8.5) as clock:
            rows, ruler = chunk_range_scene()
            subhead = label(f"원문 {SOURCE_LENGTH}자 · 실제 char_start / char_end 범위",
                            21, P.muted).move_to([0, 2.8, 0])
            self.play(FadeIn(subhead), Create(ruler), run_time=.35); clock.used += .35
            for group, _, _, _ in rows:
                self.play(Create(group), run_time=.2); clock.used += .2

            c05, c06 = CHUNK_BY_ID["C05"], CHUNK_BY_ID["C06"]
            overlap_start = max(c05["char_start"], c06["char_start"])
            overlap_end = min(c05["char_end"], c06["char_end"])
            overlap_width = width = 10.7
            overlap_left = -5.35 + width * overlap_start / SOURCE_LENGTH
            overlap_right = -5.35 + width * overlap_end / SOURCE_LENGTH
            overlap_y = (rows[4][3] + rows[5][3]) / 2
            overlap = Line([overlap_left, overlap_y, 0], [overlap_right, overlap_y, 0],
                           color=P.active, stroke_width=12)
            c05row, c06row = rows[4][0], rows[5][0]
            c05row[0].set_color(P.result); c06row[0].set_color(P.result)
            detail = VGroup(
                label(f"C05 [{c05['char_start']}, {c05['char_end']})", 19, P.result),
                label(f"C06 [{c06['char_start']}, {c06['char_end']})", 19, P.result),
                label(f"겹치는 원문 {overlap_end-overlap_start}자", 20, P.active),
            ).arrange(RIGHT, buff=.34).move_to([0, -1.65, 0])
            excerpt_box = RoundedRectangle(width=11.2, height=1.05, corner_radius=.1,
                stroke_color=P.faint, fill_color=P.bg, fill_opacity=1).move_to([0, -2.55, 0])
            self.play(Create(overlap), FadeIn(detail), run_time=.45); clock.used += .45
            self.play(Create(excerpt_box), run_time=.25); clock.used += .25
            # A moving locator shows the source window that supplies each same-ID chunk.
            locator = Line([rows[0][1], rows[0][3], 0], [rows[0][2], rows[0][3], 0],
                           color=P.sensor, stroke_width=14)
            cards = []
            for chunk in CHUNKS:
                card = VGroup(
                    label(f"{chunk['id']}  [{chunk['char_start']}, {chunk['char_end']})",
                          19, P.sensor).move_to([0, -2.37, 0]),
                    label(excerpt(chunk, 75), 17, P.fg, 10.7).move_to([0, -2.78, 0]))
                card.set_opacity(0)
                cards.append(card)
            self.play(Create(locator), run_time=.15); clock.used += .15
            cards_group = VGroup(*cards)
            self.add(cards_group)
            def follow_source_window(mob, alpha):
                position = alpha * (len(rows)-1)
                index = min(len(rows)-1, int(position))
                blend = position - index
                if index == len(rows)-1:
                    blend = 0
                current = rows[index]
                if blend and index + 1 < len(rows):
                    nxt = rows[index + 1]
                    left = current[1] * (1-blend) + nxt[1] * blend
                    right = current[2] * (1-blend) + nxt[2] * blend
                    y = current[3] * (1-blend) + nxt[3] * blend
                else:
                    left, right, y = current[1], current[2], current[3]
                mob.put_start_and_end_on([left, y, 0], [right, y, 0])
            def follow_chunk_text(_mob, alpha):
                selected = min(len(cards)-1, int(alpha * len(cards)))
                for index, card in enumerate(cards):
                    card.set_opacity(1 if index == selected else 0)
            self.play(UpdateFromAlphaFunc(locator, follow_source_window),
                      UpdateFromAlphaFunc(cards_group, follow_chunk_text), run_time=3.6)
            clock.used += 3.6
            clock.wait(.8)

        # Segment 2: each stored chunk vector appears at its saved display coordinate.
        with BeatClock(self, 8.5) as clock:
            self.play(Transform(title, heading("같은 ID의 청크가 벡터가 된다")),
                      *[FadeOut(mob) for mob in [subhead, ruler, *(row[0] for row in rows),
                                                  overlap, detail, excerpt_box, locator, cards_group]],
                      run_time=.35)
            clock.used += .35
            points = np.asarray(list(COORDS.values()), dtype=float)
            scale_x = 2.0 / max(float(np.abs(points[:, 0]).max()), .01)
            scale_y = 1.55 / max(float(np.abs(points[:, 1]).max()), .01)
            plot_center_x = -4.0
            axes = VGroup(Line([-6.2, -1.95, 0], [-1.8, -1.95, 0], color=P.faint),
                          Line([-6.2, -1.95, 0], [-6.2, 1.9, 0], color=P.faint))
            self.play(Create(axes), run_time=.25); clock.used += .25
            dots = {}
            for chunk in CHUNKS:
                xy = COORDS[chunk["id"]]
                pos = [plot_center_x + xy[0]*scale_x, xy[1]*scale_y, 0]
                dot = Dot(pos, radius=.08, color=P.muted)
                offsets = {"C01": [.22, .3, 0], "C02": [-.3, .27, 0],
                           "C03": [.24, .28, 0], "C04": [.36, -.18, 0]}
                tag = label(chunk["id"], 18, P.muted)
                if chunk["id"] in offsets:
                    tag.move_to(dot.get_center() + np.array(offsets[chunk["id"]]))
                else:
                    tag.next_to(dot, UP, buff=.06)
                dots[chunk["id"]] = VGroup(dot, tag)
            for mob in dots.values():
                self.play(GrowFromCenter(mob[0]), FadeIn(mob[1]), run_time=.35)
                clock.used += .35
            query_pos = [plot_center_x + COORDS[QUERY["id"]][0]*scale_x,
                         COORDS[QUERY["id"]][1]*scale_y, 0]
            query_dot = Star(n=5, outer_radius=.16, color=P.sensor,
                             fill_opacity=1).move_to(query_pos)
            query_tag = label("질문 Q0", 20, P.sensor).next_to(query_dot, UP, buff=.1)
            query_group = VGroup(query_dot, query_tag)
            query_card = RoundedRectangle(width=7.5, height=.64, corner_radius=.08,
                stroke_color=P.sensor, fill_color=P.bg, fill_opacity=1).move_to([0, -2.48, 0])
            query_text = VGroup(query_card,
                label(f"질문 Q0 · {QUERY['text']}", 19, P.sensor, 7.1).move_to([0, -2.48, 0]))
            self.play(GrowFromPoint(query_dot, ORIGIN), FadeIn(query_tag, shift=UP*.15),
                      FadeIn(query_text, shift=UP*.12), run_time=.65); clock.used += .65
            note = label("384차원 벡터를 PCA 좌표로 표시 · 화면의 거리는 실제 검색 점수가 아님",
                         19, P.muted, 11.8).move_to([0, -3.35, 0])
            self.play(FadeIn(note), run_time=.25); clock.used += .25
            clock.wait(1.5)

        # Segment 3: candidates are tested in recorded score order; one current link at a time.
        with BeatClock(self, 8.5) as clock:
            self.play(Transform(title, heading("질문과의 실제 거리로 순위를 정한다")),
                      FadeOut(query_text), run_time=.3)
            clock.used += .3
            rows = []
            max_score = max(item["value"] for item in RANKING)
            for index, item in enumerate(RANKING):
                y = 1.78 - index*.34
                cid = item["source_id"]
                color = P.result if item["rank"] <= len(TOP) else P.muted
                rank = label(f"{item['rank']:02d}", 17, color).move_to([.15, y, 0])
                name = label(cid, 19, color).move_to([.8, y, 0])
                bar = Line([1.35, y, 0], [1.35 + 3.0*item["value"]/max_score, y, 0],
                           color=color, stroke_width=6)
                value = label(f"{item['value']:.4f}", 18, color).move_to([5.25, y, 0])
                rows.append(VGroup(rank, name, bar, value))
            score_title = label("원본 384D 제곱 L2 · 낮은 점수부터 실제 검색 순위",
                                20, P.muted).move_to([3.0, 2.2, 0])
            self.play(FadeIn(score_title), run_time=.2); clock.used += .2
            query_pos = query_dot.get_center()
            previous_link = None
            for item, row in zip(RANKING, rows):
                pos = dots[item["source_id"]][0].get_center()
                link = Line(query_pos, pos, color=P.active, stroke_width=2.4)
                if previous_link is None:
                    self.play(Create(link), FadeIn(row, shift=RIGHT*.08), run_time=.55)
                else:
                    self.play(Transform(previous_link, link), FadeIn(row, shift=RIGHT*.08),
                              run_time=.55)
                previous_link = link if previous_link is None else previous_link
                clock.used += .55
            top_note = label("실제 선택: " + " → ".join(TOP), 24, P.result).move_to([3.0, -2.4, 0])
            self.play(Indicate(VGroup(*rows[:len(TOP)]), color=P.result, scale_factor=1.03),
                      FadeIn(top_note), run_time=.55); clock.used += .55
            clock.wait(1.35)

        # Segment 4: selected source objects move into context, then feed the recorded answer.
        with BeatClock(self, 8.5) as clock:
            self.play(Transform(title, heading("선택된 같은 청크가 답변 context가 된다")),
                      *[FadeOut(row) for row in rows], FadeOut(score_title), FadeOut(top_note),
                      FadeOut(previous_link), FadeOut(axes), FadeOut(VGroup(*dots.values())),
                      FadeOut(query_group), FadeOut(note), run_time=.35)
            clock.used += .35
            context_frame = RoundedRectangle(width=6.1, height=4.65, corner_radius=.14,
                stroke_color=P.active, stroke_width=2, fill_color=P.bg, fill_opacity=1).move_to([3.1, 0, 0])
            context_head = label("검색 결과가 context에 연결됨", 21, P.active).move_to([3.1, 1.8, 0])
            self.play(Create(context_frame), FadeIn(context_head), run_time=.3); clock.used += .3
            source_rows, target_rows = [], []
            for index, cid in enumerate(TOP):
                y = 1.0 - index*1.12
                chunk = CHUNK_BY_ID[cid]
                src_box = RoundedRectangle(width=5.4, height=.78, corner_radius=.08,
                    stroke_color=P.result if index == 0 else P.muted,
                    fill_color=P.bg, fill_opacity=1).move_to([-3.15, y, 0])
                src = VGroup(src_box, label(cid, 19, P.result if index == 0 else P.muted).move_to([-5.4, y, 0]),
                             label(excerpt(chunk, 48), 15, P.fg, 4.25).move_to([-2.8, y, 0]))
                dst_box = RoundedRectangle(width=5.6, height=.88, corner_radius=.08,
                    stroke_color=P.result if index == 0 else P.active,
                    fill_color=P.bg, fill_opacity=1).move_to([3.1, y, 0])
                dst = VGroup(dst_box, label(cid, 18, P.result if index == 0 else P.active).move_to([.95, y, 0]),
                             label(excerpt(chunk, 47), 14, P.fg, 4.35).move_to([3.55, y, 0]))
                source_rows.append(src); target_rows.append(dst)
            for src, dst in zip(source_rows, target_rows):
                self.play(FadeIn(src, shift=RIGHT*.25), run_time=.8); clock.used += .8
                self.play(Transform(src, dst), run_time=.9); clock.used += .9
            answer = TRACE["outputs"][0]["text"]
            answer_box = RoundedRectangle(width=12.2, height=.85, corner_radius=.1,
                stroke_color=P.sensor, fill_color=P.bg, fill_opacity=1).move_to([0, -2.45, 0])
            answer_text = label("기록된 답변: " + answer, 17, P.fg, 11.7).move_to([0, -2.45, 0])
            self.play(Create(answer_box), Write(answer_text), run_time=.6); clock.used += .6
            clock.wait(1.0)
