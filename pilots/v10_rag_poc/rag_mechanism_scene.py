"""Continuous, trace-driven RAG mechanics scene with a 2D embedding fallback."""
from pathlib import Path
import json
import os
import sys
import numpy as np
from manim import *

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "core/manim-robotics-education-skill/templates"))
from manim_kit import apply_theme, txt, BeatClock, P

sys.path.insert(0, str(ROOT / "core/ai-mechanism"))
from rag_visual_data import prepare_rag_visual_data

TRACE_PATH = Path(os.environ.get("V10_AI_TRACE", HERE / "data/ai_trace.json")).resolve()
TRACE = json.loads(TRACE_PATH.read_text(encoding="utf-8"))
DATA = prepare_rag_visual_data(TRACE)
CHUNKS, CHUNK_BY_ID = DATA["chunks"], {item["id"]: item for item in DATA["chunks"]}
QUERY, RANKING, COORDS, TOP = DATA["query"], DATA["ranking"], DATA["coords"], DATA["top_ids"]
SOURCE_LENGTH = DATA["source_length"] or max((c.get("char_end", 0) for c in CHUNKS), default=1)
try:
    DURATIONS = [float(value) for value in json.loads(os.environ.get("V10_RAG_DURATIONS", "[]"))]
except (TypeError, ValueError, json.JSONDecodeError):
    DURATIONS = []
if len(DURATIONS) != 4 or any(value <= 0 for value in DURATIONS):
    raise RuntimeError("V10_RAG_DURATIONS must contain four positive V9 manifest beat durations")
DESIGNED = [7.7, 5.4, 2.4 + .55*min(14, len(RANKING)),
            2.25 + 1.7*min(5, len(TOP))]


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
    chunk_ids = [chunk["id"] for chunk in CHUNKS]
    visible_indices = set(np.linspace(0, len(CHUNKS)-1, min(18, len(CHUNKS)), dtype=int).tolist())
    if DATA["representative_overlap"]:
        visible_indices.update(chunk_ids.index(DATA["representative_overlap"][key])
                               for key in ("left_id", "right_id"))
    visible_chunks = [chunk for index, chunk in enumerate(CHUNKS) if index in visible_indices]
    top_y = 1.8
    step = min(.29, 3.15 / max(1, len(visible_chunks)-1))
    rows = []
    for index, chunk in enumerate(visible_chunks):
        y = top_y - index * step
        start, end = chunk.get("char_start", 0), chunk.get("char_end", SOURCE_LENGTH)
        left = x0 + width * start / max(SOURCE_LENGTH, 1)
        right = x0 + width * end / max(SOURCE_LENGTH, 1)
        span = Line([left, y, 0], [right, y, 0], color=P.muted, stroke_width=10)
        start_tick = Line([left, y-.09, 0], [left, y+.09, 0], color=P.faint, stroke_width=1.5)
        end_tick = Line([right, y-.09, 0], [right, y+.09, 0], color=P.faint, stroke_width=1.5)
        cid = label(chunk["id"], 12 if len(CHUNKS) > 12 else 17, P.fg, 1.2).move_to([-6.25, y, 0])
        rows.append((VGroup(span, start_tick, end_tick, cid), left, right, y))
    ruler = VGroup(Line([x0, 2.25, 0], [x0+width, 2.25, 0], color=P.faint, stroke_width=1),
                   label("0", 15, P.muted).move_to([x0, 2.48, 0]),
            label(str(SOURCE_LENGTH), 15, P.muted).move_to([x0+width, 2.48, 0]))
    return rows, ruler, visible_chunks


def beat_time(index, value):
    # One frame is the smallest meaningful animation. A longer floor makes
    # several tiny actions overrun valid short manifest beats.
    return max(1 / 30, value * min(1.0, DURATIONS[index] / DESIGNED[index]))


class RAGMechanismPoC(Scene):
    def construct(self):
        apply_theme(self)
        title = heading("문서 범위가 청크로 나뉜다")
        self.add(title)

        # Segment 1: exact character windows from the recorded splitter output.
        with BeatClock(self, DURATIONS[0]) as clock:
            rows, ruler, visible_chunks = chunk_range_scene()
            density_note = f" · {len(rows)}개 표시" if len(rows) < len(CHUNKS) else ""
            subhead = label(f"원문 {SOURCE_LENGTH}자 · 실제 char_start / char_end 범위{density_note}",
                            21, P.muted).move_to([0, 2.8, 0])
            self.play(FadeIn(subhead), Create(ruler), run_time=beat_time(0, .35)); clock.used += beat_time(0, .35)
            self.play(LaggedStart(*[Create(group) for group, _, _, _ in rows], lag_ratio=.08),
                      run_time=beat_time(0, 2.1)); clock.used += beat_time(0, 2.1)

            chosen = DATA["representative_overlap"]
            overlap = VGroup()
            if chosen:
                overlap_left = -5.35 + 10.7 * chosen["char_start"] / max(SOURCE_LENGTH, 1)
                overlap_right = -5.35 + 10.7 * chosen["char_end"] / max(SOURCE_LENGTH, 1)
                left_index = next(i for i, c in enumerate(visible_chunks) if c["id"] == chosen["left_id"])
                right_index = next(i for i, c in enumerate(visible_chunks) if c["id"] == chosen["right_id"])
                overlap_y = (rows[left_index][3] + rows[right_index][3]) / 2
                overlap = Line([overlap_left, overlap_y, 0], [overlap_right, overlap_y, 0],
                               color=P.active, stroke_width=12)
                rows[left_index][0][0].set_color(P.result)
                rows[right_index][0][0].set_color(P.result)
                detail_text = f"{chosen['left_id']} ↔ {chosen['right_id']} · 실제 겹침 {chosen['length']}자"
            else:
                detail_text = "실제 원문 구간 겹침 없음"
            detail = label(detail_text, 21, P.active, 11.7).move_to([0, -1.65, 0])
            excerpt_box = RoundedRectangle(width=11.2, height=1.05, corner_radius=.1,
                stroke_color=P.faint, fill_color=P.bg, fill_opacity=1).move_to([0, -2.55, 0])
            self.play(Create(overlap), FadeIn(detail), run_time=beat_time(0, .45)); clock.used += beat_time(0, .45)
            self.play(Create(excerpt_box), run_time=beat_time(0, .25)); clock.used += beat_time(0, .25)
            # A moving locator shows the source window that supplies each same-ID chunk.
            locator = Line([rows[0][1], rows[0][3], 0], [rows[0][2], rows[0][3], 0],
                           color=P.sensor, stroke_width=14)
            cards = []
            for chunk in visible_chunks:
                card = VGroup(
                    label(f"{chunk['id']}  [{chunk.get('char_start', 0)}, {chunk.get('char_end', SOURCE_LENGTH)})",
                          19, P.sensor).move_to([0, -2.37, 0]),
                    label(excerpt(chunk, 42), 13, P.fg, 10.7).move_to([0, -2.78, 0]))
                card.set_opacity(0)
                cards.append(card)
            self.play(Create(locator), run_time=beat_time(0, .15)); clock.used += beat_time(0, .15)
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
            movement_time = beat_time(0, 3.6)
            self.play(UpdateFromAlphaFunc(locator, follow_source_window),
                      UpdateFromAlphaFunc(cards_group, follow_chunk_text), run_time=movement_time)
            clock.used += movement_time
            clock.wait(beat_time(0, .8))

        # Segment 2: each stored chunk vector appears at its saved display coordinate.
        with BeatClock(self, DURATIONS[1]) as clock:
            self.play(Transform(title, heading("같은 ID의 청크가 벡터가 된다")),
                      *[FadeOut(mob) for mob in [subhead, ruler, *(row[0] for row in rows),
                                                  overlap, detail, excerpt_box, locator, cards_group]],
                      run_time=beat_time(1, .35))
            clock.used += beat_time(1, .35)
            points = np.asarray(list(COORDS.values()), dtype=float)
            scale_x = 2.0 / max(float(np.abs(points[:, 0]).max()), .01)
            scale_y = 1.55 / max(float(np.abs(points[:, 1]).max()), .01)
            plot_center_x = -4.0
            axes = VGroup(Line([-6.2, -1.95, 0], [-1.8, -1.95, 0], color=P.faint),
                          Line([-6.2, -1.95, 0], [-6.2, 1.9, 0], color=P.faint))
            self.play(Create(axes), run_time=beat_time(1, .25)); clock.used += beat_time(1, .25)
            dots = {}
            for chunk in CHUNKS:
                xy = COORDS[chunk["id"]]
                pos = [plot_center_x + xy[0]*scale_x, xy[1]*scale_y, 0]
                dot = Dot(pos, radius=.08, color=P.muted)
                tag = label(chunk["id"], 17, P.muted, 1.35)
                # Candidate identity and exact order are shown in the adjacent
                # score table; labeling a dense 2D projection duplicates that
                # information and hides the query/candidate geometry.
                tag.set_opacity(0)
                dots[chunk["id"]] = VGroup(dot, tag)
            self.play(LaggedStart(*[AnimationGroup(GrowFromCenter(mob[0]), FadeIn(mob[1]))
                                    for mob in dots.values()], lag_ratio=.08),
                      run_time=beat_time(1, 2.4)); clock.used += beat_time(1, 2.4)
            query_pos = [plot_center_x + COORDS[QUERY["id"]][0]*scale_x,
                         COORDS[QUERY["id"]][1]*scale_y, 0]
            query_dot = Star(n=5, outer_radius=.16, color=P.sensor,
                             fill_opacity=1).move_to(query_pos)
            query_tag = label("질문", 18, P.sensor, 1.0).move_to([-3.1, 1.45, 0])
            query_group = VGroup(query_dot, query_tag)
            query_card = RoundedRectangle(width=7.5, height=.64, corner_radius=.08,
                stroke_color=P.sensor, fill_color=P.bg, fill_opacity=1).move_to([0, -2.48, 0])
            query_text = VGroup(query_card,
                label(f"질문 · {QUERY['text']}", 19, P.sensor, 7.1).move_to([0, -2.48, 0]))
            self.play(GrowFromPoint(query_dot, ORIGIN), FadeIn(query_tag, shift=UP*.15),
                      FadeIn(query_text, shift=UP*.12), run_time=beat_time(1, .65)); clock.used += beat_time(1, .65)
            dimension = len(QUERY.get("embedding", QUERY.get("features", [])))
            note = label(f"{DATA['vector_label']} · {dimension}개 성분 축소 · Top-K 후보 ID만 표시 · 좌표 거리는 검색 점수가 아님",
                         19, P.muted, 11.8).move_to([0, -3.35, 0])
            self.play(FadeIn(note), run_time=beat_time(1, .25)); clock.used += beat_time(1, .25)
            clock.wait(beat_time(1, 1.5))

        # Segment 3: candidates are tested in recorded score order; one current link at a time.
        with BeatClock(self, DURATIONS[2]) as clock:
            self.play(Transform(title, heading("질문과 후보 청크의 점수로 순위를 정한다")),
                      FadeOut(query_text), run_time=beat_time(2, .3))
            clock.used += beat_time(2, .3)
            rows = []
            # Keep enough non-selected candidates to make the measured ranking
            # legible while avoiding a dense spreadsheet-like list.
            shown_ranking = RANKING[:max(8, min(10, len(TOP) + 4))]
            max_score = max(abs(item["value"]) for item in shown_ranking) or 1.0
            for index, item in enumerate(shown_ranking):
                y = 1.55 - index * min(.42, 3.5 / max(1, len(shown_ranking)-1))
                cid = item["source_id"]
                color = P.result if cid in TOP else P.muted
                rank = label(f"{item['rank']:02d}", 16, color).move_to([-.05, y, 0])
                name = label(cid, 16, color, 1.35).move_to([1.0, y, 0])
                normalized = max(0.08, abs(item["value"]) / max_score)
                bar = Line([1.9, y, 0], [1.9 + 2.45*normalized, y, 0],
                           color=color, stroke_width=6)
                value = label(f"{item['value']:.4f}", 16, color).move_to([5.5, y, 0])
                rows.append(VGroup(rank, name, bar, value))
            order_text = "낮은 점수 우선" if DATA["direction"] == "ascending" else "높은 점수 우선"
            score_title = label(f"기록된 {DATA['metric']} · {order_text}",
                                20, P.muted, 7.0).move_to([3.0, 2.2, 0])
            self.play(FadeIn(score_title), run_time=beat_time(2, .2)); clock.used += beat_time(2, .2)
            query_pos = query_dot.get_center()
            previous_link = None
            for item, row in zip(shown_ranking, rows):
                pos = dots[item["source_id"]][0].get_center()
                link = Line(query_pos, pos, color=P.active, stroke_width=2.4)
                if previous_link is None:
                    self.play(Create(link), FadeIn(row, shift=RIGHT*.08), run_time=beat_time(2, .55))
                else:
                    self.play(Transform(previous_link, link), FadeIn(row, shift=RIGHT*.08),
                              run_time=beat_time(2, .55))
                previous_link = link if previous_link is None else previous_link
                clock.used += beat_time(2, .55)
            top_note = label("실제 선택: " + " → ".join(TOP), 20, P.result, 6.7).move_to([3.0, -2.4, 0])
            selected_rows = [row for item, row in zip(shown_ranking, rows) if item["source_id"] in TOP]
            self.play(Indicate(VGroup(*selected_rows), color=P.result, scale_factor=1.03),
                      FadeIn(top_note), run_time=beat_time(2, .55)); clock.used += beat_time(2, .55)
            clock.wait(beat_time(2, 1.35))

        # Segment 4: selected source objects move into context, then feed the recorded answer.
        with BeatClock(self, DURATIONS[3]) as clock:
            self.play(Transform(title, heading("검색된 같은 청크가 문맥으로 모인다")),
                      *[FadeOut(row) for row in rows], FadeOut(score_title), FadeOut(top_note),
                      FadeOut(previous_link), FadeOut(axes), FadeOut(VGroup(*dots.values())),
                      FadeOut(query_group), FadeOut(note), run_time=beat_time(3, .35))
            clock.used += beat_time(3, .35)
            context_frame = RoundedRectangle(width=6.1, height=4.65, corner_radius=.14,
                stroke_color=P.active, stroke_width=2, fill_color=P.bg, fill_opacity=1).move_to([3.1, 0, 0])
            context_head = label("검색 결과가 context에 연결됨", 21, P.active).move_to([3.1, 1.8, 0])
            self.play(Create(context_frame), FadeIn(context_head), run_time=beat_time(3, .3)); clock.used += beat_time(3, .3)
            source_rows, target_rows = [], []
            shown_top = TOP[:5]
            row_height = min(.78, 2.5 / max(1, len(shown_top)))
            row_step = min(1.12, 2.5 / max(1, len(shown_top)-1)) if len(shown_top) > 1 else 0
            for index, cid in enumerate(shown_top):
                y = 1.0 - index*row_step
                chunk = CHUNK_BY_ID[cid]
                src_box = RoundedRectangle(width=5.4, height=row_height, corner_radius=.08,
                    stroke_color=P.result if index == 0 else P.muted,
                    fill_color=P.bg, fill_opacity=1).move_to([-3.15, y, 0])
                src = VGroup(src_box, label(cid, 16, P.result if index == 0 else P.muted, 1.3).move_to([-5.1, y, 0]),
                             label(excerpt(chunk, 22), 12, P.fg, 3.65).move_to([-2.55, y, 0]))
                dst_box = RoundedRectangle(width=5.6, height=row_height, corner_radius=.08,
                    stroke_color=P.result if index == 0 else P.active,
                    fill_color=P.bg, fill_opacity=1).move_to([3.1, y, 0])
                dst = VGroup(dst_box, label(cid, 16, P.result if index == 0 else P.active, 1.3).move_to([1.05, y, 0]),
                             label(excerpt(chunk, 22), 12, P.fg, 3.9).move_to([3.85, y, 0]))
                source_rows.append(src); target_rows.append(dst)
            for src, dst in zip(source_rows, target_rows):
                self.play(FadeIn(src, shift=RIGHT*.25), run_time=beat_time(3, .8)); clock.used += beat_time(3, .8)
                self.play(Transform(src, dst), run_time=beat_time(3, .9)); clock.used += beat_time(3, .9)
            output = TRACE["outputs"][0]
            answer = output.get("text", "")
            answer_box = RoundedRectangle(width=12.2, height=.85, corner_radius=.1,
                stroke_color=P.sensor, fill_color=P.bg, fill_opacity=1).move_to([0, -2.45, 0])
            output_label = ("기록된 답변: " + answer) if output.get("kind") == "answer" and answer else \
                           ("조립된 context · 생성 모델은 실행하지 않음" if answer else "조립된 context")
            answer_text = label(output_label, 17, P.fg, 11.7).move_to([0, -2.45, 0])
            self.play(Create(answer_box), Write(answer_text), run_time=beat_time(3, .6)); clock.used += beat_time(3, .6)
            clock.wait(beat_time(3, 1.0))
