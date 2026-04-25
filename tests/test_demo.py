"""Tests for the demo() convenience function."""

from bokeh.models import GlyphRenderer, Label


def test_demo_returns_figure():
    """demo(show=False) returns a Bokeh figure without opening a browser."""
    from timeSpace import demo

    p = demo(show=False)
    assert p is not None
    assert hasattr(p, "renderers")


def test_demo_has_processes():
    """demo figure should contain process ellipse renderers."""
    from timeSpace import demo

    p = demo(show=False)
    glyph_renderers = [r for r in p.renderers if isinstance(r, GlyphRenderer)]
    # At minimum: diffusion lines, light cone, process patches/glyphs
    assert len(glyph_renderers) >= 3


def test_demo_has_labels():
    """demo figure should have Label annotations (magnitude labels)."""
    from timeSpace import demo

    p = demo(show=False)
    labels = [obj for obj in p.center if isinstance(obj, Label)]
    assert len(labels) >= 1


def test_demo_has_legend():
    """demo figure should include a legend."""
    from timeSpace import demo

    p = demo(show=False)
    assert len(p.legend) >= 1
