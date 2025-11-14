from tools.in_memory_cache import InMemoryCache
import time

def test_get_set_and_eviction():
    c = InMemoryCache(maxsize=2, default_ttl=1)
    c.set('a', 1)
    c.set('b', 2)
    assert c.get('a') == 1
    assert c.get('b') == 2
    # adding a new item should evict the oldest due to maxsize
    c.set('c', 3)
    vals = [c.get(k) for k in ['a','b','c']]
    assert sum(1 for v in vals if v is not None) == 2


def test_ttl_expiry():
    c = InMemoryCache(maxsize=10, default_ttl=1)
    c.set('x', 99)
    assert c.get('x') == 99
    time.sleep(1.2)
    assert c.get('x') is None
