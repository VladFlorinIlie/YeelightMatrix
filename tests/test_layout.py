"""Tests for layout rendering and addressing."""

import pytest

from yeelight_matrix.enums import BasePosition, Orientation
from yeelight_matrix.exceptions import LayoutError
from yeelight_matrix.layout import Layout


def test_modules_logical_order_independent_of_base():
    types = ["5x5_clear", "5x5_blur", "1x1"]
    top = Layout("vertical", "top", types)
    bottom = Layout("vertical", "bottom", types)
    assert [m.type.value for m in top.modules] == types
    assert [m.type.value for m in bottom.modules] == types


def test_set_module_colors_maps_logical_index():
    layout = Layout("vertical", "bottom", ["5x5_clear", "1x1"])
    layout.set_module_colors(1, "#abcdef")  # the spotlight
    assert layout.module_at(1).type.value == "1x1"
    assert layout.module_at(1).colors == ["#abcdef"]


def test_set_module_colors_accepts_full_grid():
    layout = Layout("vertical", "top", ["5x5_clear"])
    grid = [f"#{i:02x}0000" for i in range(25)]
    layout.set_module_colors(0, grid)
    assert layout.module_at(0).colors == grid


def test_render_frame_length():
    # Each LED -> 3 bytes -> 4 base64 chars. 2x 5x5 + 1x 1x1 = 51 LEDs.
    layout = Layout("vertical", "top", ["5x5_clear", "5x5_clear", "1x1"])
    assert len(layout.render_frame()) == 51 * 4


def test_set_pixel_then_render_is_stable():
    layout = Layout("vertical", "top", ["5x5_clear"])
    layout.set_pixel(2, 2, "#ff0000")
    frame = layout.render_frame()
    assert isinstance(frame, str) and len(frame) == 25 * 4


def test_invalid_base_for_orientation():
    with pytest.raises(LayoutError):
        Layout("vertical", "left", ["5x5_clear"])


def test_set_image_requires_free_clear_module(tmp_path):
    layout = Layout("vertical", "top", ["1x1"])
    with pytest.raises(LayoutError):
        layout.set_image("does_not_matter.png", 0, 1)
