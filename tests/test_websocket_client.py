import random

from bfxapi.websocket._client.bfx_websocket_client import _Delay


class TestDelay:
    """Tests for the exponential backoff _Delay class."""

    def test_initial_delay_is_random(self):
        random.seed(42)
        d = _Delay(backoff_factor=1.618)
        first = d.next()
        assert 1.0 <= first <= 5.0

    def test_backoff_increases(self):
        random.seed(42)
        d = _Delay(backoff_factor=2.0)
        d.next()  # initial random delay
        second = d.next()  # should be 1.92 * 2.0 = 3.84
        third = d.next()  # should be 3.84 * 2.0 = 7.68

        # After initial, delays should grow
        assert second < third

    def test_backoff_max_cap(self):
        d = _Delay(backoff_factor=100.0)
        # Force past initial
        d.next()  # initial
        # Each subsequent call multiplies by 100, but max is 60
        for _ in range(10):
            val = d.next()
        assert val <= 60.0

    def test_peek_does_not_advance(self):
        random.seed(42)
        d = _Delay(backoff_factor=1.618)
        peek1 = d.peek()
        peek2 = d.peek()
        assert peek1 == peek2

    def test_next_advances_past_peek(self):
        random.seed(42)
        d = _Delay(backoff_factor=1.618)
        peek_val = d.peek()
        next_val = d.next()
        assert next_val == peek_val
        # After next, peek should return a different (larger) value
        assert d.peek() != peek_val

    def test_reset(self):
        random.seed(42)
        d = _Delay(backoff_factor=2.0)
        d.next()  # initial
        d.next()  # advance
        d.next()  # advance more

        d.reset()
        # After reset, peek returns initial delay again
        peek = d.peek()
        assert 1.0 <= peek <= 5.0

    def test_backoff_factor_applied(self):
        d = _Delay(backoff_factor=2.0)
        d.next()  # initial random delay
        val1 = d.next()  # 1.92 * 2 = 3.84
        val2 = d.next()  # 3.84 * 2 = 7.68
        assert abs(val2 / val1 - 2.0) < 0.01
