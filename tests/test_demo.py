"""Tests for the demo() convenience function."""

from bokeh.models import GlyphRenderer

from timeSpace import demo


def test_demo_returns_figure():
    """demo(show=False) returns a Bokeh figure without opening a browser."""
    p = demo(show=False)
    assert p is not None
    assert hasattr(p, "renderers")


def test_demo_has_processes():
    """demo figure should contain process ellipse renderers."""
    p = demo(show=False)
    glyph_renderers = [r for r in p.renderers if isinstance(r, GlyphRenderer)]
    # At minimum: diffusion lines, light cone, process patches/glyphs
    assert len(glyph_renderers) >= 3


def test_demo_has_labels():
    """demo figure should name its magnitude markers on extra axes."""
    p = demo(show=False)
    named = [a for a in p.below + p.right if getattr(a, "major_label_overrides", None)]
    assert len(named) == 2


def test_demo_has_legend():
    """demo figure should include a legend."""
    p = demo(show=False)
    assert len(p.legend) >= 1
