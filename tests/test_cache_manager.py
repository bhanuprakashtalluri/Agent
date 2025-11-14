import time
import os
from tools.cache_manager import CacheManager


def setup_module():
    # ensure a clean cache file per test run
    p = "cache/test_cache.db"
    if os.path.exists(p):
        os.remove(p)


def test_set_get_and_delete():
    cache = CacheManager(db_path="cache/test_cache.db")
    cache.clear()
    cache.set('llm', 'k1', {'a': 1})
    v = cache.get('llm', 'k1')
    assert v == {'a': 1}
    cache.delete('llm', 'k1')
    assert cache.get('llm', 'k1') is None


def test_ttl_expiry():
    cache = CacheManager(db_path="cache/test_cache.db")
    cache.clear()
    cache.set('llm', 'k2', 'temp', ttl_seconds=1)
    assert cache.get('llm', 'k2') == 'temp'
    time.sleep(1.2)
    assert cache.get('llm', 'k2') is None


def test_get_or_set_provider():
    cache = CacheManager(db_path="cache/test_cache.db")
    cache.clear()

    def provider():
        return {'computed': True}

    v = cache.get_or_set('llm', 'k3', provider, ttl_seconds=2)
    assert v == {'computed': True}
    # second call should hit cache
    v2 = cache.get_or_set('llm', 'k3', lambda: {'computed': False})
    assert v2 == {'computed': True}


if __name__ == '__main__':
    setup_module()
    test_set_get_and_delete()
    test_ttl_expiry()
    test_get_or_set_provider()
    print('All cache manager tests passed')