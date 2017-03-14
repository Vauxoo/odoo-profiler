# coding: utf-8
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
# Copyright 2014 Anybox <http://anybox.fr>
# Copyright 2016 Vauxoo (https://www.vauxoo.com) <info@vauxoo.com>
import logging
import os
from cProfile import Profile

import odoo
from odoo.http import WebRequest
from odoo.service.server import ThreadedServer

from . import core
from .core import profiling

_logger = logging.getLogger(__name__)


def patch_odoo():
    """Modify Odoo entry points so that profile can record.

    Odoo is a multi-threaded program. Therefore, the :data:`profile` object
    needs to be enabled/disabled each in each thread to capture all the
    execution.

    For instance, Odoo spawns a new thread for each request.
    """
    _logger.info('Patching odoo.http.WebRequest._call_function')
    webreq_f_origin = WebRequest._call_function

    def webreq_f(*args, **kwargs):
        with profiling():
            return webreq_f_origin(*args, **kwargs)
    WebRequest._call_function = webreq_f


def dump_stats():
    """Dump stats to standard file"""
    _logger.info('Dump stats')
    core.profile.dump_stats(os.path.expanduser('~/.openerp_server.stats'))


def create_profile():
    """Create the global, shared profile object."""
    _logger.info('Create core.profile')
    core.profile = Profile()


def patch_stop():
    """When the server is stopped then save the result of cProfile stats"""
    origin_stop = ThreadedServer.stop

    _logger.info('Patching odoo.service.server.ThreadedServer.stop')

    def stop(*args, **kwargs):
        if odoo.tools.config['test_enable']:
            dump_stats()
        return origin_stop(*args, **kwargs)
    ThreadedServer.stop = stop


def post_load():
    _logger.info('Post load')
    create_profile()
    patch_odoo()
    if odoo.tools.config['test_enable']:
        # Enable profile in test mode for orm methods.
        _logger.info('Enabling core and apply patch')
        core.enabled = True
        patch_stop()
