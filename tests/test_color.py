"""Tests for colour parsing and encoding."""

import base64

import pytest

from yeelight_matrix.color import encode, encode_many, to_hex, to_rgb


@pytest.mark.parametrize(
    "value,expected",
    [
        ("#ff0000", (255, 0, 0)),
        ("00ff00", (0, 255, 0)),
        ("#0000FF", (0, 0, 255)),
        ((12, 34, 56), (12, 34, 56)),
        ([1, 2, 3], (1, 2, 3)),
    ],
)
def test_to_rgb(value, expected):
    assert to_rgb(value) == expected


@pytest.mark.parametrize("value", ["#fff", "nothex", (1, 2), (300, 0, 0), 42])
def test_to_rgb_invalid(value):
    with pytest.raises(ValueError):
        to_rgb(value)


def test_to_hex_normalises():
    assert to_hex("#FF0000") == "#ff0000"
    assert to_hex((0, 128, 255)) == "#0080ff"


def test_encode_matches_base64():
    assert encode("#010203") == base64.b64encode(bytes([1, 2, 3])).decode()


def test_encode_many_concatenates():
    assert encode_many(["#010203", "#040506"]) == encode("#010203") + encode("#040506")
