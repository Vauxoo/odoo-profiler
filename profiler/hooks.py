# coding: utf-8
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


def patch_orm_methods():
    """Show a command to modify OpenERP/Odoo ORM methods
    so that profile can record."""

    # TODO: Apply a monkey patch of nested method.
    fname_to_patch = os.path.join(os.path.dirname(odoo.http.__file__),
                                  "http.py")
    odoo_is_patched = 'with profiling():' in open(fname_to_patch).read()
    if odoo_is_patched:
        _logger.info('The method odoo.api.make_wrapper is patching!')
        return True
    patch_cmds = [
        'sed -i "s/response = f(\\*args, \\*\\*kw)/with profiling(): '
        'response = f(*args, **kw)/g"' + fname_to_patch,
        'sed -i "/# avoid hasattr/a ' + '\\ \\ \\ \\ \\ \\ \\ \\     '
        'from odoo.addons.profiler import profiling" ' + fname_to_patch]
    _logger.warn('You will need apply a manual patch to odoo.api.make_wrapper'
                 ' to record all ORM methods. Please execute follow commands:'
                 'Execute follow commands:\n' + '\n'.join(patch_cmds))
    return False


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
        patch_orm_methods()
        patch_stop()
