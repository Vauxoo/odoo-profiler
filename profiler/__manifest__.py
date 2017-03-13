# coding: utf-8
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
# Copyright 2016 Vauxoo (https://www.vauxoo.com) <info@vauxoo.com>

{
    'name': 'profiler',
    'version': '10.0.1.0.0',
    'category': 'devtools',
    'license': 'AGPL-3',
    'author': 'Georges Racinet, Vauxoo',
    'website': 'http://anybox.fr',
    'depends': ['website'],
    'data': [
        'data/prfiler_excluding.xml',
        'security/group.xml',
        'views/profiler.xml'
    ],
    'qweb': [
        'static/src/xml/player.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'post_load': 'post_load',
}
