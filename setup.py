#!/usr/bin/env python
# -*- coding: utf-8 -*-
import setuptools
import asyncpg_migrate

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="asyncpg-migrate",
    version=asyncpg_migrate.__version__,
    author="Michal Szczepanski",
    author_email="michal@vane.pl",
    description="Migration tool for asyncpg inspired by knex.js",
    long_description=long_description,
    long_description_content_type="text/markdown",
    entry_points={
        'console_scripts': [
            'asyncpg-migrate = asyncpg_migrate.asyncpg_migrate:run'
        ],
    },
    install_requires=[
        'asyncpg',
        'PyYAML',
    ],
    license='BSD 3-clause "New" or "Revised License"',
    url="https://github.com/vane/asyncpg-migrate",
    packages=setuptools.find_packages(),
    package_data={
        'asyncpg_migrate': [
            'conf/db.yaml',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        'License :: OSI Approved :: BSD License',
    ],
)
