#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path

from setuptools import find_packages, setup

REQUIRES = [
    'intelmq>=3.0.2',
    'psycopg2',
]

BOTS = []
base_path = './intelmq/bots'
bots = [botfile for botfile in Path(base_path).glob('**/*.py') if botfile.is_file() and not botfile.name.startswith('_')]
for file in bots:
    file = Path(str(file).replace(str(base_path), 'intelmq/bots'))
    module = '.'.join(file.with_suffix('').parts)
    BOTS.append('{0} = {0}:BOT.run'.format(module))

ENTRY_POINTS = [
    "ripe_import = intelmq_certbund_contact.ripe.ripe_import:main",
    "ripe_diff = intelmq_certbund_contact.ripe.ripe_diff:main",
]

setup(
    name='intelmq_certbund_contact',
    version="0.9.5",
    maintainer='Intevation GmbH',
    maintainer_email='sebastian.wagner@intevation.de',
    python_requires='>=3.4',
    install_requires=REQUIRES,
    packages=find_packages("."),
    description=('IntelMQ Contacts is a contact database for IntelMQ'
                 ' with related expert bots'),
    entry_points={'console_scripts': BOTS + ENTRY_POINTS},
    scripts=["bin/ripe_download",
             "bin/import-national-certs"],
)
