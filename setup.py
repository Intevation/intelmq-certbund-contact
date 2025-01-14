#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path

from setuptools import find_packages, setup

REQUIRES = [
    'intelmq>=3.0.2',
    'psycopg2',
    'intelmqmail',
]

ENTRY_POINTS = [
    "ripe_import = intelmq_certbund_contact.ripe.ripe_import:main",
    "ripe_diff = intelmq_certbund_contact.ripe.ripe_diff:main",
    # the entry points IntelMQ is searching for, see https://docs.intelmq.org/latest/dev/extensions-packages/#building-an-extension-package
    "intelmq.bots.experts.certbund_contact.expert = intelmq_certbund_contact.bots.experts.certbund_contact.expert:BOT.run",
    "intelmq.bots.experts.certbund_rules.expert = intelmq_certbund_contact.bots.experts.certbund_rules.expert:BOT.run"
]

setup(
    name='intelmq_certbund_contact',
    version="1.1.0",
    maintainer='Intevation GmbH',
    maintainer_email='sebastian.wagner@intevation.de',
    python_requires='>=3.4',
    install_requires=REQUIRES,
    packages=find_packages("."),
    description=('IntelMQ Contacts is a contact database for IntelMQ'
                 ' with related expert bots'),
    entry_points={'console_scripts': ENTRY_POINTS},
    scripts=["bin/ripe_download",
             "bin/import-national-certs"],
)
