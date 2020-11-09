asyncpg_migrate
====
  
## Description

Simple database migration tool inspired by ``` knex.js```.  
Migrations are by default applied in order of that they're sorted in ```migrations``` directory 

## Install
```bash
pip install asyncpg_migrate
```
## Usage

#### Display help
```
asyncpg_migrate -h
```

#### Add migration
```
asyncpg_migrate -a 'test migration'
```
migration will be added to migrations/${timestamp}_test_migration.py 
with following template
 
```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncpg

async def up(config):
    conn: asyncpg.Connection = await asyncpg.connect(**config)
    pass

async def down(config):
    conn: asyncpg.Connection = await asyncpg.connect(**config)
    pass
```

#### List migrations
```
asyncpg_migrate -l
``` 

#### Apply all migrations
```
asyncpg_migrate -m
```

#### Apply specific migration
```
asyncpg_migrate -m migrations/migration_file.py
```

#### Custom config -- different then conf/db.yaml (optional)
```
asyncpg_migrate -c conf/some.config.yaml
```

example config
```yaml
db:
  host: 127.0.0.1
  port: 5432
  user: postgres
  password: postgres
  database: asyncpg-migate-test
```

#### Custom migration directory (optional)
```
asyncpg_migrate -d /opt/my-migrations
```

#### Using environment variables instead of configuration file
```
PG_USER
PG_PASSWORD
PG_DBNAME
PG_HOST
PG_PORT
``` 
