"""Tests for reading YAML, including the initial comment block handling.

Run with: python -m pytest tests
"""

import io
from collections import OrderedDict

import pytest

import rtyaml


def as_stream(text):
    """rtyaml only reads a leading comment block from a seekable stream."""
    return io.StringIO(text)


def test_load_dict_keeps_initial_comment():
    doc = as_stream("# hello\na: 1\nb: 2\n")
    data = rtyaml.load(doc)
    assert data == {"a": 1, "b": 2}
    assert rtyaml.dump(data).startswith("# hello\n")


def test_load_list_keeps_initial_comment():
    doc = as_stream("# hello\n- 1\n- 2\n")
    data = rtyaml.load(doc)
    assert data == [1, 2]
    assert rtyaml.dump(data).startswith("# hello\n")


def test_load_dict_without_comment():
    data = rtyaml.load(as_stream("a: 1\n"))
    assert data == {"a": 1}
    assert not rtyaml.dump(data).startswith("#")


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        # A scalar document cannot carry an attribute, so the comment is simply
        # not preserved. It used to raise AttributeError instead.
        ("# hello\njust a string\n", "just a string"),
        ("# hello\n42\n", 42),
        # A file that is nothing but comments loads as None.
        ("# hello\n", None),
        ("# hello\n# and more\n", None),
    ],
)
def test_load_uncarryable_document(text, expected):
    assert rtyaml.load(as_stream(text)) == expected


def test_load_all_multiple_documents():
    docs = list(rtyaml.load_all(as_stream("a: 1\n---\nb: 2\n")))
    assert docs == [{"a": 1}, {"b": 2}]


def test_load_all_with_initial_comment():
    # load_all returns a generator, which cannot carry the comment attribute.
    docs = list(rtyaml.load_all(as_stream("# hello\na: 1\n---\nb: 2\n")))
    assert docs == [{"a": 1}, {"b": 2}]


def test_load_preserves_key_order():
    data = rtyaml.load(as_stream("# hello\nz: 1\na: 2\nm: 3\n"))
    assert isinstance(data, OrderedDict)
    assert list(data.keys()) == ["z", "a", "m"]


def test_dump_to_stream_writes_comment_first():
    data = rtyaml.load(as_stream("# hello\na: 1\n"))
    out = io.StringIO()
    rtyaml.dump(data, out)
    assert out.getvalue().startswith("# hello\n")
