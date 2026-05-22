"""Tests for logslice.context module."""

import pytest
from logslice.context import lines_with_context, extract_lines


SAMPLE = [
    "alpha",
    "beta",
    "gamma match",
    "delta",
    "epsilon",
    "zeta match",
    "eta",
]


def _match(line):
    return "match" in line


def _collect(lines, before=0, after=0):
    return list(lines_with_context(lines, before=before, after=after, match_fn=_match))


class TestLinesWithContext:
    def test_no_context_returns_only_matches(self):
        results = _collect(SAMPLE)
        assert all(r["match"] for r in results)
        assert [r["line"] for r in results] == ["gamma match", "zeta match"]

    def test_before_context(self):
        results = _collect(SAMPLE, before=2)
        lines = [r["line"] for r in results]
        assert "beta" in lines
        assert "gamma match" in lines
        # 'alpha' is 2 lines before 'gamma match'
        assert "alpha" in lines

    def test_after_context(self):
        results = _collect(SAMPLE, before=0, after=1)
        lines = [r["line"] for r in results]
        assert "delta" in lines
        assert "eta" in lines

    def test_before_and_after_context(self):
        results = _collect(SAMPLE, before=1, after=1)
        lines = [r["line"] for r in results]
        assert "beta" in lines
        assert "gamma match" in lines
        assert "delta" in lines

    def test_no_duplicates_when_contexts_overlap(self):
        # 'zeta match' is 3 lines after 'gamma match'; with after=3 and before=3
        # there would be overlap
        results = _collect(SAMPLE, before=3, after=3)
        linenos = [r["lineno"] for r in results]
        assert len(linenos) == len(set(linenos)), "Duplicate line numbers found"

    def test_match_flag_set_correctly(self):
        results = _collect(SAMPLE, before=1, after=1)
        for r in results:
            if "match" in r["line"]:
                assert r["match"] is True
            else:
                assert r["match"] is False

    def test_empty_input(self):
        results = _collect([])
        assert results == []

    def test_no_matches(self):
        results = list(
            lines_with_context(["foo", "bar"], match_fn=lambda l: False)
        )
        assert results == []

    def test_all_match(self):
        data = ["a", "b", "c"]
        results = list(
            lines_with_context(data, before=0, after=0, match_fn=lambda l: True)
        )
        assert len(results) == 3
        assert all(r["match"] for r in results)

    def test_lineno_starts_at_one(self):
        results = _collect(SAMPLE)
        assert results[0]["lineno"] == 3  # 'gamma match' is line 3

    def test_negative_before_treated_as_zero(self):
        results = list(
            lines_with_context(SAMPLE, before=-5, after=0, match_fn=_match)
        )
        assert all(r["match"] for r in results)


def test_extract_lines():
    entries = [
        {"line": "foo", "lineno": 1, "match": False},
        {"line": "bar", "lineno": 2, "match": True},
    ]
    assert list(extract_lines(entries)) == ["foo", "bar"]
