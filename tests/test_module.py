"""Tests for the Module grid model."""

import pytest

from yeelight_matrix.enums import ModuleType
from yeelight_matrix.module import Module


def test_defaults_to_black_and_unused():
    m = Module(ModuleType.CLEAR)
    assert m.led_count == 25
    assert m.colors == ["#000000"] * 25
    assert m.used is False


def test_spotlight_is_single_led():
    m = Module("1x1")
    assert m.led_count == 1
    assert not m.is_matrix


def test_set_pixel_addresses_row_major():
    m = Module(ModuleType.CLEAR)
    m.set_pixel(0, 0, "#ff0000")
    m.set_pixel(4, 4, "#00ff00")
    assert m.colors[0] == "#ff0000"
    assert m.colors[24] == "#00ff00"
    assert m.used is True


def test_set_pixel_out_of_range():
    m = Module(ModuleType.CLEAR)
    with pytest.raises(IndexError):
        m.set_pixel(5, 0, "#ffffff")


def test_set_grid_validates_length():
    m = Module(ModuleType.CLEAR)
    with pytest.raises(ValueError):
        m.set_grid(["#ffffff"] * 10)


def test_fill_and_clear():
    m = Module(ModuleType.BLUR)
    m.fill("#123456")
    assert m.colors == ["#123456"] * 25
    m.clear()
    assert m.colors == ["#000000"] * 25
    assert m.used is False
