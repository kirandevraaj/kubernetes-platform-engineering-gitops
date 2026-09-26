"""Bounded concurrency helpers for I/O-bound discovery."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable, Sequence
from typing import TypeVar

T = TypeVar("T")


async def map_bounded(
    items: Sequence[T],
    worker: Callable[[T], Awaitable],
    *,
    limit: int = 5,
) -> list:
    """Run async worker over items with a concurrency ceiling.

    More parallelism is not always faster — APIs throttle; keep ``limit`` modest.
    """
    if limit < 1:
        raise ValueError("limit must be >= 1")
    semaphore = asyncio.Semaphore(limit)
    results: list = [None] * len(items)

    async def _run(index: int, item: T) -> None:
        async with semaphore:
            results[index] = await worker(item)

    await asyncio.gather(*(_run(i, item) for i, item in enumerate(items)))
    return results


def timed_sequential(fn: Callable[[T], object], items: Sequence[T]) -> tuple[list, float]:
    started = time.perf_counter()
    out = [fn(item) for item in items]
    return out, time.perf_counter() - started


async def timed_concurrent(
    worker: Callable[[T], Awaitable],
    items: Sequence[T],
    *,
    limit: int = 5,
) -> tuple[list, float]:
    started = time.perf_counter()
    out = await map_bounded(items, worker, limit=limit)
    return out, time.perf_counter() - started
