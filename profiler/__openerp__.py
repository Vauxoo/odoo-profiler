# -*- coding: utf-8 -*-
{
    'name': "profiler",
    'author': "Vauxoo",
    'website': "http://www.vauxoo.com",
    'category': 'devtools',
    'version': '9.0.1.0.0',
    'depends': ["document"],
    'data': [
        'security/ir.model.access.csv',
        'views/profiler_profile_view.xml',
    ],
    'post_load': 'post_load',
    'installable': True,
}
