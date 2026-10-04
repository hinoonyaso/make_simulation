from manim import *
from manim_kit import VisualReasoningScene, apply_theme

class BaseExplainer(VisualReasoningScene):
    """Subclass and implement construct(). Keep narration timestamps external or integrate your preferred voiceover plugin."""
    def setup(self):
        super().setup()
        apply_theme(self)
