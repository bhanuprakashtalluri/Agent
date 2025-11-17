import importlib


def test_nl2sql_with_raw_sql_string():
    # ensure module is fresh
    mod = importlib.reload(importlib.import_module('tools.db_tools'))
    out = mod.nl2sql_query('SELECT * FROM orders;')
    assert isinstance(out, str)
    # Expect the header to contain order_number column
    assert 'order_number' in out


def test_nl2sql_with_dict_payload():
    mod = importlib.reload(importlib.import_module('tools.db_tools'))
    out = mod.nl2sql_query({'user_question': 'SELECT * FROM orders;'})
    assert isinstance(out, str)
    assert 'order_number' in out


def test_nl2sql_calls_llm_for_nl(monkeypatch):
    # Monkeypatch the cached_invoke to return a simple SELECT
    import tools.llm_cache as llm_cache

    called = {}

    def fake_cached_invoke(model, prompt, cache=None, cache_type='nl2sql', ttl_seconds=60, model_name=None, query_store=None):
        called['prompt'] = prompt
        return 'SELECT id, order_number FROM orders;'

    monkeypatch.setattr(llm_cache, 'cached_invoke', fake_cached_invoke)

    mod = importlib.reload(importlib.import_module('tools.db_tools'))
    out = mod.nl2sql_query('How many orders are there?')
    assert isinstance(out, str)
    assert 'order_number' in out
    assert 'prompt' in called
