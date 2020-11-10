#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import yaml


class MigrateConfig:
    """Store and process configuration"""
    _conf = None
    _instance = None

    def _read_config(self, fname: str):
        with open(fname) as f:
            data = f.read()
            self._conf = yaml.safe_load(data)
            # validate config
            if not 'db' in self._conf:
                raise RuntimeError('Missing asyncpg parameter in config')
            return True
        raise RuntimeError(f'Failed to read config from file : {fname}')

    def init(self, fname: str):
        return self._read_config(fname)

    def db_config(self):
        if not self._conf:
            raise RuntimeError('Configuration not initialized')
        c = self._conf['db']
        return {
            'user': os.environ.get('PG_USER') or c.get('user', 'postgres'),
            'password': os.environ.get('PG_PASSWORD') or c.get('password', 'postgres'),
            'database': os.environ.get('PG_DBNAME') or c['database'],
            'host': os.environ.get('PG_HOST') or c.get('host', '127.0.0.1'),
            'port': os.environ.get('PG_PORT') or c.get('port', '5432'),
        }

    @classmethod
    def instance(cls):
        if not cls._instance:
            cls._instance = MigrateConfig()
        return cls._instance

    def get(self):
        if not self._conf:
            raise RuntimeError('Configuration not initialized')
        return self._conf
