"""Admin CLI for inspecting and managing caches.

Usage:
    python3 -m tools.cache_admin list [--type TYPE]
    python3 -m tools.cache_admin clear [--type TYPE]
    python3 -m tools.cache_admin prune
    python3 -m tools.cache_admin           # interactive menu
"""
import argparse
import os
import sqlite3
import sys
from datetime import datetime

from .cache_manager import CacheManager


def main(argv=None):
    """Entry point for the cache administration command-line interface."""

    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='cmd')

    sub_list = sub.add_parser('list')
    sub_list.add_argument('--type', default=None)

    sub_clear = sub.add_parser('clear')
    sub_clear.add_argument('--type', default=None)

    sub_prune = sub.add_parser('prune')

    args = p.parse_args(argv)

    cache = CacheManager()

    if args.cmd is None:
        if sys.stdin.isatty():
            _interactive_loop(cache)
            return
        p.print_help()
        return

    if args.cmd == 'list':
        keys = cache.keys(args.type)
        for k in keys:
            print(k)
    elif args.cmd == 'clear':
        cache.clear(args.type)
        print('Cleared cache', args.type or 'all')
    elif args.cmd == 'prune':
        cache.prune()
        # also vacuum sqlite DBs if present
        dbp = cache.db_path
        if os.path.exists(dbp):
            print('Pruned cache and compacting DB')
    else:
        p.print_help()


def _interactive_loop(cache: CacheManager) -> None:
    """Render the interactive console menu and dispatch user choices."""

    while True:
        print("\nCache Admin Interface")
        print(f"Database: {cache.db_path}")
        print(" 1) List cache types")
        print(" 2) Show keys for a type")
        print(" 3) View entry details")
        print(" 4) Clear a cache type")
        print(" 5) Clear all caches")
        print(" 6) Prune caches")
        print(" 0) Exit")
        choice = input("Select option: ").strip().lower()
        if choice in {"0", "q", "quit", "exit"}:
            print("Goodbye.")
            break
        if choice == "1":
            _interactive_list_types(cache)
        elif choice == "2":
            _interactive_show_keys(cache)
        elif choice == "3":
            _interactive_view_entry(cache)
        elif choice == "4":
            _interactive_clear_type(cache)
        elif choice == "5":
            cache.clear()
            print("Cleared all cache entries.")
        elif choice == "6":
            _interactive_prune(cache)
        else:
            print("Unknown option. Please choose a menu number.")


def _interactive_list_types(cache: CacheManager) -> None:
    """Display available cache types along with counts and timestamps."""
    columns = _get_cache_columns(cache)
    select_parts = ["type", "COUNT(*) AS count", "MIN(timestamp) AS first_ts"]
    include_last_accessed = "last_accessed" in columns
    if include_last_accessed:
        select_parts.append("MAX(last_accessed) AS last_ts")
    query = "SELECT " + ", ".join(select_parts) + " FROM cache GROUP BY type ORDER BY type"
    rows = _fetch_rows(cache, query)
    if not rows:
        print("No cache entries found.")
        return
    heading = "\nType                          Count   First Seen          "
    heading += "Last Used" if include_last_accessed else "Last Seen"
    print(heading)
    print("-----------------------------------------------------------------")
    for row in rows:
        type_name = row[0] or "(none)"
        count = row[1] or 0
        first_seen = _format_ts(row[2])
        if include_last_accessed:
            last_used = _format_ts(row[3])
        else:
            last_used = first_seen
        print(f"{type_name:<30} {count:>6}   {first_seen:<19} {last_used:<19}")


def _interactive_show_keys(cache: CacheManager) -> None:
    """Show keys stored for a user-selected cache type."""
    cache_type = _prompt_cache_type(cache)
    if not cache_type:
        return
    keys = cache.keys(cache_type)
    if not keys:
        print(f"No keys stored for type '{cache_type}'.")
        return
    print(f"\nKeys for type '{cache_type}':")
    for idx, key in enumerate(keys, 1):
        print(f" {idx:>3}) {key}")


def _interactive_view_entry(cache: CacheManager) -> None:
    """Inspect a specific cache entry including metadata and value preview."""
    cache_type = _prompt_cache_type(cache)
    if not cache_type:
        return
    key = input("Enter key to inspect: ").strip()
    if not key:
        print("No key provided.")
        return
    columns = _get_cache_columns(cache)
    select_cols = ["timestamp"]
    for optional_col in ("expires_at", "last_accessed", "format"):
        if optional_col in columns:
            select_cols.append(optional_col)
    query = "SELECT " + ", ".join(select_cols) + " FROM cache WHERE type=? AND key=?"
    meta = _fetch_rows(cache, query, (cache_type, key))
    if not meta:
        print("Entry not found.")
        return
    meta_row = meta[0]
    meta_map = {col: meta_row[idx] for idx, col in enumerate(select_cols)}
    timestamp = meta_map.get("timestamp")
    expires_at = meta_map.get("expires_at")
    last_accessed = meta_map.get("last_accessed")
    fmt = meta_map.get("format")
    value = cache.get(cache_type, key)
    print("\nMetadata:")
    print(f" Type:          {cache_type}")
    print(f" Key:           {key}")
    print(f" Created:       {_format_ts(timestamp)}")
    print(f" Last accessed: {_format_ts(last_accessed)}")
    print(f" Expires at:    {_format_ts(expires_at)}")
    if fmt:
        print(f" Stored format: {fmt}")
    if value is None:
        print(" Value:         <expired or unavailable>")
    else:
        preview = repr(value)
        if len(preview) > 500:
            preview = preview[:497] + "..."
        print(f" Value preview: {preview}")


def _interactive_clear_type(cache: CacheManager) -> None:
    """Prompt for a type and clear all associated entries."""
    cache_type = _prompt_cache_type(cache)
    if not cache_type:
        return
    confirm = input(f"Clear all entries for type '{cache_type}'? [y/N]: ").strip().lower()
    if confirm not in {"y", "yes"}:
        print("Cancelled.")
        return
    cache.clear(cache_type)
    print(f"Cleared cache type '{cache_type}'.")


def _interactive_prune(cache: CacheManager) -> None:
    """Collect pruning preferences and run :meth:`CacheManager.prune`."""
    remove_expired = input("Remove expired entries? [Y/n]: ").strip().lower()
    remove_flag = remove_expired not in {"n", "no"}
    keep_input = input("Keep only the most recent N entries (blank to skip): ").strip()
    keep_value = None
    if keep_input:
        try:
            keep_value = int(keep_input)
        except ValueError:
            print("Invalid number; keeping all entries.")
            keep_value = None
    cache.prune(remove_all_expired=remove_flag, keep_most_recent=keep_value)
    print("Prune operation completed.")


def _prompt_cache_type(cache: CacheManager) -> str:
    """Ask the user to select a cache type and return the identifier."""
    types = [row[0] for row in _fetch_rows(cache, "SELECT DISTINCT type FROM cache ORDER BY type")]
    if not types:
        print("No cache types available.")
        return ""
    print("\nAvailable cache types:")
    for idx, type_name in enumerate(types, 1):
        print(f" {idx:>3}) {type_name}")
    choice = input("Select by number or enter type name: ").strip()
    if not choice:
        return ""
    if choice.isdigit():
        idx = int(choice)
        if 1 <= idx <= len(types):
            return types[idx - 1]
        print("Invalid selection.")
        return ""
    if choice in types:
        return choice
    print("Type not recognized.")
    return ""


def _fetch_rows(cache: CacheManager, query: str, params=()):
    """Execute *query* against the cache database and return all rows."""
    with sqlite3.connect(cache.db_path) as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        return cur.fetchall()


def _format_ts(value) -> str:
    """Return a human-readable timestamp or hyphen when unavailable."""
    if value in (None, ""):
        return "-"
    try:
        value_int = int(value)
        return datetime.fromtimestamp(value_int).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(value)


_CACHE_COLUMNS = None


def _get_cache_columns(cache: CacheManager):
    """Fetch and memoize the set of columns available on the cache table."""
    global _CACHE_COLUMNS
    if _CACHE_COLUMNS is not None:
        return _CACHE_COLUMNS
    with sqlite3.connect(cache.db_path) as conn:
        cur = conn.cursor()
        try:
            cur.execute("PRAGMA table_info(cache)")
            _CACHE_COLUMNS = {row[1] for row in cur.fetchall()}
        except sqlite3.OperationalError:
            _CACHE_COLUMNS = set()
    return _CACHE_COLUMNS


if __name__ == '__main__':
    main()
