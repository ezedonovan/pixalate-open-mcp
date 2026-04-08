"""Tests for the exponential backoff retry decorator."""

from unittest.mock import MagicMock, patch

import pytest

from pixalate_open_mcp.utils.exponential_backoff import exponential_backoff


class _TransientError(Exception):
    """Sentinel exception used in backoff tests to simulate transient failures."""


class _PermanentError(Exception):
    """Sentinel exception used in backoff tests to simulate a non-recoverable failure."""


@patch("builtins.print")
@patch("pixalate_open_mcp.utils.exponential_backoff.time.sleep")
def test_succeeds_on_first_try_no_retry(mock_sleep, mock_print):
    """Function that succeeds on first try should not trigger any sleep."""

    @exponential_backoff()
    def always_succeeds():
        return "ok"

    result = always_succeeds()

    assert result == "ok"
    mock_sleep.assert_not_called()


@patch("builtins.print")
@patch("pixalate_open_mcp.utils.exponential_backoff.time.sleep")
def test_retries_on_failure_then_succeeds(mock_sleep, mock_print):
    """Function that fails twice then succeeds should sleep exactly twice."""
    mock_func = MagicMock(side_effect=[_TransientError(), _TransientError(), "ok"])

    @exponential_backoff()
    def sometimes_fails():
        return mock_func()

    result = sometimes_fails()

    assert result == "ok"
    assert mock_sleep.call_count == 2


@patch("builtins.print")
@patch("pixalate_open_mcp.utils.exponential_backoff.time.sleep")
def test_raises_after_max_retries_exhausted(mock_sleep, mock_print):
    """Function that always fails should raise the original exception after max_retries."""

    @exponential_backoff(max_retries=3)
    def always_fails():
        raise _PermanentError

    with pytest.raises(_PermanentError):
        always_fails()

    # Should sleep max_retries - 1 times (2 times for max_retries=3)
    assert mock_sleep.call_count == 2


@patch("builtins.print")
@patch("pixalate_open_mcp.utils.exponential_backoff.time.sleep")
def test_respects_max_delay_cap(mock_sleep, mock_print):
    """Delay should never exceed max_delay when jitter is disabled."""
    call_count = 0

    @exponential_backoff(initial_delay=1, max_delay=5, jitter=False)
    def fails_five_times():
        nonlocal call_count
        call_count += 1
        if call_count <= 5:
            raise _TransientError
        return "ok"

    result = fails_five_times()

    assert result == "ok"
    for call_args in mock_sleep.call_args_list:
        delay = call_args[0][0]
        assert delay <= 5, f"Delay {delay} exceeded max_delay of 5"


@patch("builtins.print")
@patch("pixalate_open_mcp.utils.exponential_backoff.time.sleep")
def test_jitter_disabled_uses_exact_delay(mock_sleep, mock_print):
    """With jitter=False, first retry delay should be exactly initial_delay * 2^0 = 1.0."""
    call_count = 0

    @exponential_backoff(initial_delay=1, jitter=False)
    def fails_once():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise _TransientError
        return "ok"

    result = fails_once()

    assert result == "ok"
    mock_sleep.assert_called_once_with(1.0)


@patch("builtins.print")
@patch("pixalate_open_mcp.utils.exponential_backoff.time.sleep")
def test_jitter_adds_randomness(mock_sleep, mock_print):
    """With jitter=True, retry delay should be >= the base delay (jitter only adds, never subtracts)."""
    call_count = 0

    @exponential_backoff(initial_delay=1, jitter=True)
    def fails_once():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise _TransientError
        return "ok"

    result = fails_once()

    assert result == "ok"
    mock_sleep.assert_called_once()
    actual_delay = mock_sleep.call_args[0][0]
    # Base delay for first retry is initial_delay * 2^0 = 1.0; jitter only adds
    assert actual_delay >= 1.0, f"Expected delay >= 1.0 but got {actual_delay}"
