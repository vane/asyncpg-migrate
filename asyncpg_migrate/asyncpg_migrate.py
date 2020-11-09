#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import time
import argparse
from typing import List, Dict, Any
import asyncio
import asyncpg
from asyncpg_migrate.migrate_config import MigrateConfig

migration_template = """#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncpg

async def up(config):
    conn: asyncpg.Connection = await asyncpg.connect(**config)
    pass

async def down(config):
    conn: asyncpg.Connection = await asyncpg.connect(**config)
    pass
"""


# -
# Database
# -

async def ensure_migration_table(config: Dict) -> bool:
    """Create migration table if not exists"""
    conn: asyncpg.Connection = await asyncpg.connect(**config)
    await conn.execute('''CREATE TABLE IF NOT EXISTS migration (
        id SERIAL PRIMARY KEY, 
        file_name VARCHAR(200) NOT NULL, 
        date TIMESTAMP NOT NULL DEFAULT NOW()
    )''')
    return True


async def select_migrations(config: Dict) -> List[asyncpg.Record]:
    """Select all migrations from migration table"""
    conn: asyncpg.Connection = await asyncpg.connect(**config)
    return await conn.fetch('''SELECT * FROM migration''')


async def select_migration_file_name(config: Dict, file_name) -> asyncpg.Record:
    """Select migration by file name"""
    conn: asyncpg.Connection = await asyncpg.connect(**config)
    return await conn.fetchrow('''SELECT * FROM migration where file_name = $1''', file_name)


async def insert_migration(config: Dict, file_name):
    """Insert new migration"""
    conn: asyncpg.Connection = await asyncpg.connect(**config)
    await conn.execute('''INSERT INTO migration (file_name) VALUES ($1)''', file_name)


async def delete_migration(config: Dict, file_name):
    """Delete migration"""
    conn: asyncpg.Connection = await asyncpg.connect(**config)
    await conn.execute('''DELETE FROM migration where file_name = $1''', file_name)


# -
# Utils
# -

def import_module(directory: str, fname: str) -> Any:
    module_name = '.'.join(fname.split('.')[:-1])
    m = __import__(f'{directory}.{module_name}')
    return getattr(m, module_name)


def print_error(msg: str):
    print(f'--ERROR-- {msg}')


def print_info(msg: str):
    print(f'{msg}')


# -
# Argument call
# -

def add_migration(name: str, directory: str):
    """Add migration file"""
    dt = int(time.time())
    name = '_'.join(name.strip().split(' '))
    fpath = os.path.join(directory, f'{dt}_{name}.py')
    if os.path.exists(fpath):
        raise RuntimeError(f'Path {fpath} already exists')
    with open(fpath, 'w+') as f:
        f.write(migration_template)


async def migrate_database(config: Dict, fname: str, directory: str):
    """Migrate database to latest version"""
    await ensure_migration_table(config)
    if fname == 'all':
        await migrate_all(config, directory)
    else:
        await migrate_one(config, fname)


async def migrate_all(config: Dict, directory: str):
    """Migrate all missing migrations"""
    rows = await select_migrations(config)
    for fname in os.listdir(directory):
        if fname.endswith('.py') and not fname.startswith('__'):
            found = False
            for row in rows:
                r = dict(list(row.items()))
                if r['file_name'] == fname:
                    found = True
                    break
            if not found:
                module = import_module(directory=directory, fname=fname)
                await module.up(config)
                await insert_migration(config, file_name=fname)
                print_info(f'Applying {fname}')
            else:
                print_info(f'Skipping {fname}')
        pass
    pass


async def migrate_one(config: Dict, fpath: str):
    """Migrate one file"""
    if not os.path.exists(fpath):
        print_error(f'Migrate file `{fpath}` not exists')
        return
    fname = fpath.split('/')[-1]
    # check if migration exists
    result = await select_migration_file_name(config, file_name=fname)
    if result:
        print_error(f'Migration `{fpath}` found in migration table')
        return
    # migrate
    directory = '/'.join(fpath.split('/')[:-1])
    module = import_module(directory=directory, fname=fname)
    await module.up(config)
    await insert_migration(config, file_name=fname)
    print_info(f'Migrated file `{fpath}`')


async def rollback_migration(config: Dict, fpath: str):
    """Rollback migration"""
    if not os.path.exists(fpath):
        print_error(f'Rollback file `{fpath}` not exists')
        return
    fname = fpath.split('/')[-1]
    # check if migration exists
    await ensure_migration_table(config)
    result = await select_migration_file_name(config, file_name=fname)
    if not result:
        print_error(f'Migration `{fpath}` not found in migration table')
        return
    directory = '/'.join(fpath.split('/')[:-1])
    module = import_module(directory=directory, fname=fname)
    await module.down(config)
    await delete_migration(config, file_name=fname)
    print_info(f'Rollback migration `{fname}`')


async def list_migrations(config: Dict, directory: str):
    await ensure_migration_table(config)
    rows = await select_migrations(config)
    todo = []
    done = []
    for fname in sorted(os.listdir(directory)):
        if fname.endswith('.py') and not fname.startswith('__'):
            for row in rows:
                r = dict(list(row.items()))
                if r['file_name'] == fname:
                    done.append(fname)
                    break
            else:
                todo.append(fname)

    [print_info(f'DONE {name}') for name in done]
    [print(f'TODO {name}') for name in todo]


def main(args: argparse.Namespace):
    """Main migration method"""
    # check if files exists
    if args.config and not os.path.exists(args.config):
        path_err = f'''Path --config {args.config} not exists
for example:
db:
  host: 127.0.0.1
  port: 5432
  user: postgres
  password: postgres
  database: asyncpg-migate-test
'''
        print_error(path_err)
        return
    if args.directory and not os.path.exists(args.directory):
        print_error(f'Directory --directory {args.directory} not exists')
        return
    # run migration commands
    if args.add_migration is not None:
        # add file
        add_migration(args.add_migration, args.directory)
    elif args.rollback_migration is not None and args.config is not None:
        # rollback
        config = MigrateConfig.instance()
        config.init(args.config)
        asyncio.get_event_loop().run_until_complete(
            rollback_migration(config.db_config(), args.rollback_migration)
        )
    elif args.migrate is not None and args.config is not None:
        # migrate file or all not migrated
        config = MigrateConfig.instance()
        config.init(args.config)
        asyncio.get_event_loop().run_until_complete(
            migrate_database(config.db_config(), args.migrate, args.directory)
        )
    elif args.list is not None and args.config is not None:
        config = MigrateConfig.instance()
        config.init(args.config)
        asyncio.get_event_loop().run_until_complete(
            list_migrations(config.db_config(), args.directory)
        )
    else:
        msg = """
        -h - help
        -m -c conf/local.yaml - migrate all
        -m migrations/1602549074_foo.py -c conf/local.yaml - migrate one 
        -a foo add file migrations/{timestamp}_foo.py
        -r migrations/1602549074_foo.py -c conf/local.yaml - remove one
        -l -c conf/local.yaml - list migrations
        """
        print_info(msg)
    pass


def run():
    sys.path.insert(0, os.getcwd())
    p = argparse.ArgumentParser()
    p.add_argument('-c', '--config', help='Configuration yaml file ex. `conf/db.yaml`', default='conf/db.yaml')
    p.add_argument('-d', '--directory', help='Migration directory default to `migrations`', default='migrations')
    p.add_argument('-a', '--add-migration', help='Add new migration file with `name of file`')
    p.add_argument('-r', '--rollback-migration', help='Rollback migration file based on provided file path')
    p.add_argument('-l', '--list', help='List migrations', nargs='?', const='all')
    p.add_argument('-m', '--migrate', help='Migrate database optional `file_path`', nargs='?', const='all')
    arguments = p.parse_args()
    main(arguments)


if __name__ == '__main__':
    run()
