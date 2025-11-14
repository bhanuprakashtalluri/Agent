from tools.embeddings_cache import DEFAULT_EMBEDDINGS_CACHE

def test_set_get_embedding():
    cache = DEFAULT_EMBEDDINGS_CACHE
    content = 'some text for embedding'
    model = 'test-model'
    vec = [0.1, 0.2, 0.3]
    cache.set(content, model, vec)
    got = cache.get(content, model)
    assert got == vec

