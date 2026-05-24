"""Tests for logslice.sample."""

import pytest

from logslice.sample import every_nth, reservoir_sample, sample_by_rate


# ---------------------------------------------------------------------------
# sample_by_rate
# ---------------------------------------------------------------------------

class TestSampleByRate:
    def test_rate_one_keeps_all(self):
        lines = ["a", "b", "c", "d"]
        result = list(sample_by_rate(lines, 1.0, seed=0))
        assert result == lines

    def test_rate_zero_raises(self):
        with pytest.raises(ValueError, match="rate must be in"):
            list(sample_by_rate(["a"], 0.0))

    def test_negative_rate_raises(self):
        with pytest.raises(ValueError, match="rate must be in"):
            list(sample_by_rate(["a"], -0.5))

    def test_rate_above_one_raises(self):
        with pytest.raises(ValueError, match="rate must be in"):
            list(sample_by_rate(["a"], 1.1))

    def test_empty_input(self):
        result = list(sample_by_rate([], 0.5, seed=42))
        assert result == []

    def test_seed_reproducible(self):
        lines = [str(i) for i in range(100)]
        r1 = list(sample_by_rate(lines, 0.3, seed=7))
        r2 = list(sample_by_rate(lines, 0.3, seed=7))
        assert r1 == r2

    def test_different_seeds_differ(self):
        lines = [str(i) for i in range(100)]
        r1 = list(sample_by_rate(lines, 0.5, seed=1))
        r2 = list(sample_by_rate(lines, 0.5, seed=2))
        assert r1 != r2


# ---------------------------------------------------------------------------
# reservoir_sample
# ---------------------------------------------------------------------------

class TestReservoirSample:
    def test_count_larger_than_input_returns_all(self):
        lines = ["x", "y", "z"]
        result = reservoir_sample(lines, 10, seed=0)
        assert sorted(result) == sorted(lines)

    def test_exact_count(self):
        lines = [str(i) for i in range(20)]
        result = reservoir_sample(lines, 5, seed=42)
        assert len(result) == 5
        for line in result:
            assert line in lines

    def test_count_zero_returns_empty(self):
        result = reservoir_sample(["a", "b", "c"], 0, seed=0)
        assert result == []

    def test_negative_count_raises(self):
        with pytest.raises(ValueError, match="count must be >= 0"):
            reservoir_sample(["a"], -1)

    def test_empty_input(self):
        result = reservoir_sample([], 5, seed=0)
        assert result == []

    def test_seed_reproducible(self):
        lines = [str(i) for i in range(50)]
        r1 = reservoir_sample(lines, 10, seed=3)
        r2 = reservoir_sample(lines, 10, seed=3)
        assert r1 == r2

    def test_all_sampled_are_unique(self):
        lines = [str(i) for i in range(30)]
        result = reservoir_sample(lines, 10, seed=99)
        assert len(result) == len(set(result))


# ---------------------------------------------------------------------------
# every_nth
# ---------------------------------------------------------------------------

class TestEveryNth:
    def test_n_one_returns_all(self):
        lines = ["a", "b", "c", "d"]
        assert list(every_nth(lines, 1)) == lines

    def test_n_two_returns_alternating(self):
        lines = ["a", "b", "c", "d", "e"]
        assert list(every_nth(lines, 2)) == ["a", "c", "e"]

    def test_n_three(self):
        lines = list(range(9))
        assert list(every_nth(lines, 3)) == [0, 3, 6]

    def test_n_larger_than_input(self):
        lines = ["only"]
        assert list(every_nth(lines, 100)) == ["only"]

    def test_empty_input(self):
        assert list(every_nth([], 2)) == []

    def test_n_zero_raises(self):
        with pytest.raises(ValueError, match="n must be >= 1"):
            list(every_nth(["a"], 0))

    def test_n_negative_raises(self):
        with pytest.raises(ValueError, match="n must be >= 1"):
            list(every_nth(["a"], -3))
