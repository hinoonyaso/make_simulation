"""Short, data-driven RAG visualization using one validated AI execution trace."""
from pathlib import Path
import importlib.util
import json
import sys
import numpy as np
from manim import *

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "core/manim-robotics-education-skill/templates"))
from manim_kit import apply_theme, txt, BeatClock, P

TRACE = json.loads((HERE / "data/ai_trace.json").read_text(encoding="utf-8"))
VALUES = {item["id"]: item for item in TRACE["intermediate_values"]}
CHUNKS = {item["id"]: item for item in TRACE["intermediate_values"]
          if item["kind"] == "text_chunk"}
QUERY = TRACE["inputs"][1]
RANKING = sorted((item for item in TRACE["intermediate_values"]
                  if item["kind"] == "squared_l2_distance"), key=lambda item: item["rank"])
COORDS = {item["id"]: item["xy"] for item in TRACE["visualization"]["coordinates"]}
TOP = TRACE["outputs"][0]["retrieved_ids"]


def label(s, size=30, color=P.fg, width=None):
    m = txt(s, size=size, color=color)
    if width and m.width > width:
        m.scale_to_fit_width(width)
    return m


def panel(title, body, x, y, w, h, color=P.muted, size=25):
    frame = RoundedRectangle(width=w, height=h, corner_radius=.12, stroke_color=color,
                             stroke_width=2, fill_color=P.bg, fill_opacity=1).move_to([x, y, 0])
    if h <= 1.5:
        head = label(title, 23, color, min(1.2, w*.23)).move_to([x-w/2+.7, y, 0])
        content = label(body, size, P.fg, w-1.65)
        if content.height > h-.12:
            content.scale_to_fit_height(h-.12)
        content.move_to([x+.78, y, 0])
        return VGroup(frame, head, content)
    head = label(title, 25, color, w-.35).move_to([x, y+h/2-.33, 0])
    content = label(body, size, P.fg, w-.42)
    if content.height > h-.9:
        content.scale_to_fit_height(h-.9)
    content.move_to([x, y-.15, 0])
    return VGroup(frame, head, content)


def heading(s):
    return label(s, 40, P.fg, 13).move_to([0, 3.15, 0])


def card_excerpt(text, limit=26):
    """Show a compact source heading and body excerpt without overflowing a card."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    title = lines[0] if lines else text.strip()
    body = lines[1] if len(lines) > 1 else ""
    title_limit = min(20, limit)
    title = title[:title_limit] + ("…" if len(title) > title_limit else "")
    if body:
        body = body[:14] + ("…" if len(body) > 14 else "")
        return title + "\n" + body
    return title


def make_chunks():
    source = panel("실제 입력 문서 · ai_basic.txt", TRACE["inputs"][0]["text"][:185] + "…",
                   0, .25, 10.8, 3.55, P.muted, 27)
    chunks = []
    for i, cid in enumerate(["C01", "C02", "C03"]):
        value = CHUNKS[cid]["value"]
        excerpt = card_excerpt(value, 34)
        row = panel(cid, excerpt, (i-1)*4.3, .15, 4.0, 2.1,
                    P.result if cid == "C02" else P.muted, 18)
        chunks.append(row)
    chunk_size = next(op["parameters"].get("chunk_size") for op in TRACE["operations"]
                      if op["id"] == "document.split")
    note = label(f"실제 splitter 결과 · {len(CHUNKS)}개 청크 · chunk_size {chunk_size}글자",
                 23, P.muted, 12).move_to([0, -2.2, 0])
    return source, chunks, note


class RAGMechanismPoC(Scene):
    def construct(self):
        apply_theme(self)
        current_heading = heading("문서가 실제 청크로 나뉜다")
        self.add(current_heading)

        # 8.5 seconds per source window; event times match the reused narration excerpts.
        with BeatClock(self, 8.5) as clock:
            source, chunks, note = make_chunks()
            self.play(FadeIn(source), run_time=.6); clock.used += .6
            self.play(FadeOut(source), run_time=.25); clock.used += .25
            self.play(*[FadeIn(row, shift=DOWN*.15) for row in chunks],
                      FadeIn(note), run_time=.55); clock.used += .55
            clock.wait(7.2)

        self.next_section("embedding_projection")
        new_heading = heading("384차원 임베딩을 2차원으로 투영")
        self.play(Transform(current_heading, new_heading),
                  *[FadeOut(row) for row in chunks], FadeOut(note), run_time=.5)
        with BeatClock(self, 8.5) as clock:
            clock.used += .5
            coords = TRACE["visualization"]["coordinates"]
            points = np.array([item["xy"] for item in coords], dtype=float)
            scale_x = 4.65 / max(float(np.max(np.abs(points[:, 0]))), .01)
            scale_y = 1.72 / max(float(np.max(np.abs(points[:, 1]))), .01)
            axes = VGroup(Line([-5, -1.9, 0], [5, -1.9, 0], color=P.faint),
                          Line([-5, -1.9, 0], [-5, 2.2, 0], color=P.faint))
            self.play(Create(axes), run_time=.2); clock.used += .2
            dots = {}
            for cid, xy in COORDS.items():
                pos = [xy[0]*scale_x, xy[1]*scale_y, 0]
                is_query = cid == "query:Q0"
                dot = (Star(n=5, outer_radius=.15, color=P.sensor, fill_opacity=1) if is_query
                       else Dot(pos, radius=.075, color=P.result if cid in TOP else P.muted)).move_to(pos)
                tag = label("질문" if is_query else cid, 21, P.sensor if is_query else
                            (P.result if cid in TOP else P.muted)).next_to(dot, UP, buff=.08)
                dots[cid] = VGroup(dot, tag)
            note = label("PCA 그림은 설명용 · 실제 순위는 원래 384차원에서 계산",
                         23, P.muted, 12).move_to([0, -2.65, 0])
            self.play(*[FadeIn(m, scale=.8) for m in dots.values()], FadeIn(note), run_time=.3)
            clock.used += .3
            clock.wait(7.5)

        self.next_section("retrieval_ranking")
        self.play(Transform(current_heading, heading("실제 거리 순서로 세 조각을 고른다")),
                  *[FadeOut(m) for m in [axes, note, *dots.values()]], run_time=.5)
        with BeatClock(self, 8.5) as clock:
            clock.used += .5
            rows = []
            for idx, item in enumerate(RANKING[:6]):
                y = 1.7 - idx*.58
                cid = item["source_id"]
                color = P.result if cid in TOP else P.muted
                name = label(cid, 25, color).move_to([-4.4, y, 0])
                raw = item["value"]
                bar = Line([-3.2, y, 0], [-3.2 + min(raw, 2.4)*2.05, y, 0],
                           color=color, stroke_width=8)
                score = label(f"{raw:.3f}", 23, color).move_to([2.5, y, 0])
                rank = label(f"#{item['rank']}", 22, color).move_to([4.0, y, 0])
                rows.append(VGroup(name, bar, score, rank))
            caption = label("제곱 L2 거리 · 작을수록 가까움 · 상위 3개 강조",
                            24, P.muted).move_to([0, -2.2, 0])
            self.play(*[FadeIn(row, shift=LEFT*.2) for row in rows], FadeIn(caption), run_time=1.0)
            clock.used += 1.0
            clock.wait(7.0)

        self.next_section("context_assembly")
        self.play(Transform(current_heading, heading("선택된 같은 ID가 context를 만든다")),
                  *[FadeOut(m) for m in [*rows, caption]], run_time=.5)
        with BeatClock(self, 8.5) as clock:
            clock.used += .5
            source_cards = []
            for idx, cid in enumerate(TOP):
                chunk = CHUNKS[cid]["value"]
                text_value = card_excerpt(chunk)
                y = 1.7 - idx*1.25
                card = panel(cid, text_value, -3.45, y, 5.6, 1.05,
                             P.result if idx == 0 else P.muted, 21)
                source_cards.append(card)
            context = RoundedRectangle(width=5.9, height=4.25, corner_radius=.12,
                                       stroke_color=P.active, stroke_width=2,
                                       fill_color=P.bg, fill_opacity=1).move_to([3.25, .15, 0]).set_z_index(-5)
            context_title = label("실제 context · 원문 일부", 27, P.active).move_to([3.25, 2.0, 0]).set_z_index(3)
            context_rows = [panel(cid, card_excerpt(CHUNKS[cid]["value"]), 3.25, 1.15-idx*1.28,
                                  5.5, 1.05, P.result if idx == 0 else P.active, 14)
                            for idx, cid in enumerate(TOP)]
            sep_note = label("빈 줄로 이어 붙임 · 청크 ID 보존", 22, P.muted).move_to([0, -2.2, 0])
            self.play(*[FadeIn(card, shift=LEFT*.2) for card in source_cards],
                      FadeIn(context), FadeIn(context_title), FadeIn(sep_note), run_time=.9)
            clock.used += .9
            self.play(*[Transform(source_cards[i], context_rows[i]) for i in range(3)], run_time=1.2)
            clock.used += 1.2
            clock.wait(5.9)
