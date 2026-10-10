"""Small reusable Manim helpers that respect the existing project theme."""
from __future__ import annotations


def label_pair(scene, left, right, text_factory, palette):
    """Place two stable labels around a comparison; caller owns animation/timing."""
    left_label = text_factory(left, 22, palette.fg).move_to([-3.0, 2.1, 0])
    right_label = text_factory(right, 22, palette.fg).move_to([3.0, 2.1, 0])
    scene.add(left_label, right_label)
    return left_label, right_label
