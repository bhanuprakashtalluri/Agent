"""Admin CLI for inspecting and managing caches.

Usage:
    python3 -m tools.cache_admin list [--type TYPE]
    python3 -m tools.cache_admin clear [--type TYPE]
    python3 -m tools.cache_admin prune
"""
import argparse
from .cache_manager import CacheManager
from .query_store import DEFAULT_QUERY_STORE
import os


def main(argv=None):
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='cmd')

    sub_list = sub.add_parser('list')
    sub_list.add_argument('--type', default=None)

    sub_clear = sub.add_parser('clear')
    sub_clear.add_argument('--type', default=None)

    sub_prune = sub.add_parser('prune')

    args = p.parse_args(argv)

    cache = CacheManager()

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


if __name__ == '__main__':
    main()
