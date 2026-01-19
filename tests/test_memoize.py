import time

import pytest
from django.conf import settings
from django.core.cache import cache

from memoize_compat import delete_memoized, delete_memoized_verhash, memoize


@pytest.fixture(autouse=True)
def django_cache_settings():
    if not settings.configured:
        settings.configure(
            CACHES={
                "default": {
                    "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                    "LOCATION": "test-cache",
                }
            }
        )
    cache.clear()


def test_memoize_basic():
    calls = {"count": 0}

    @memoize(timeout=60)
    def add(a, b):
        calls["count"] += 1
        return a + b

    assert add(1, 2) == 3
    assert add(1, 2) == 3
    assert calls["count"] == 1


def test_memoize_different_args():
    calls = {"count": 0}

    @memoize(timeout=60)
    def add(a, b):
        calls["count"] += 1
        return a + b

    assert add(1, 2) == 3
    assert add(2, 3) == 5
    assert calls["count"] == 2


def test_delete_memoized_specific_call():
    calls = {"count": 0}

    @memoize(timeout=60)
    def mul(a, b):
        calls["count"] += 1
        return a * b

    assert mul(2, 3) == 6
    assert mul(2, 3) == 6
    assert calls["count"] == 1

    delete_memoized(mul, 2, 3)

    assert mul(2, 3) == 6
    assert calls["count"] == 2


def test_delete_memoized_whole_function():
    calls = {"count": 0}

    @memoize(timeout=60)
    def inc(x):
        calls["count"] += 1
        return x + 1

    assert inc(1) == 2
    assert inc(2) == 3
    assert calls["count"] == 2

    # NOTE: from cache
    assert inc(1) == 2
    assert inc(2) == 3
    assert calls["count"] == 2

    delete_memoized(inc)

    assert inc(1) == 2
    assert inc(2) == 3
    assert calls["count"] == 4


def test_delete_memoized_verhash():
    calls = {"count": 0}

    @memoize(timeout=60)
    def square(x):
        calls["count"] += 1
        return x * x

    assert square(3) == 9
    assert square(3) == 9
    assert calls["count"] == 1

    delete_memoized_verhash(square)

    assert square(3) == 9
    assert calls["count"] == 2


def test_kwargs_handling():
    calls = {"count": 0}

    @memoize(timeout=60)
    def combine(a, b=10):
        calls["count"] += 1
        return a + b

    assert combine(1, b=2) == 3
    assert combine(a=1, b=2) == 3
    assert calls["count"] == 1


def test_timeout_expiration():
    calls = {"count": 0}

    @memoize(timeout=1)
    def slow(x):
        calls["count"] += 1
        return x

    assert slow(1) == 1
    assert slow(1) == 1
    assert calls["count"] == 1

    time.sleep(1.1)

    assert slow(1) == 1
    assert calls["count"] == 2


def test_none_is_not_cached():
    calls = {"count": 0}

    @memoize(timeout=60)
    def returns_none(x):
        calls["count"] += 1
        return None

    assert returns_none(1) is None
    assert returns_none(1) is None
    assert calls["count"] == 2


def test_delete_memoized_bound_method():
    calls = {"count": 0}

    class Example:
        @memoize(timeout=60)
        def check(self, name):
            calls["count"] += 1
            return name

    example = Example()

    assert example.check("a") == "a"
    assert example.check("a") == "a"
    assert calls["count"] == 1

    delete_memoized(example.check, "a")

    assert example.check("a") == "a"
    assert calls["count"] == 2
