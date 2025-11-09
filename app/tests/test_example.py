"""Example test file."""

import pytest


def test_example():
    """Example test."""
    assert 1 + 1 == 2


@pytest.mark.asyncio
async def test_async_example():
    """Example async test."""
    result = await async_function()
    assert result is True


async def async_function():
    """Example async function."""
    return True

