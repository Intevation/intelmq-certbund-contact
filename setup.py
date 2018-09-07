#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import sys

from setuptools import find_packages, setup

REQUIRES = [
    'intelmq>=1.1.0rc2',
]

BOTS = []
bots = json.load(open(os.path.join(os.path.dirname(__file__), 'BOTS')))
for bot_type, bots in bots.items():
    for bot_name, bot in bots.items():
        module = bot['module']
        BOTS.append('{0} = {0}:BOT.run'.format(module))

ENTRY_POINTS = [
    "ripe_import = intelmq_certbund_contact.ripe.ripe_import:main",
    "ripe_diff = intelmq_certbund_contact.ripe.ripe_diff:main",
]

setup(
    name='intelmq_certbund_contact',
    version="0.1",
    maintainer='Intevation GmbH',
    maintainer_email='bernhard.herzog@intevation.de',
    python_requires='>=3.4',
    install_requires=REQUIRES,
    packages=find_packages("."),
    description=('IntelMQ Contacts is a contact database for IntelMQ'
                 ' with related expert bots'),
    entry_points={'console_scripts': BOTS + ENTRY_POINTS},
    scripts=["bin/ripe_download"],
)
