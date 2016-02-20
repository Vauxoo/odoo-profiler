from . import controllers  # noqa
import openerp
from cProfile import Profile
from . import core
from .core import profiling
from openerp.addons.web.http import JsonRequest
from openerp.service.server import ThreadedServer
import os
import logging


_logger = logging.getLogger(__name__)


def patch_openerp():
    """Modify OpenERP/Odoo entry points so that profile can record.

    Odoo is a multi-threaded program. Therefore, the :data:`profile` object
    needs to be enabled/disabled each in each thread to capture all the
    execution.

    For instance, OpenERP 7 spawns a new thread for each request.
    """
    _logger.info('Patching openerp.addons.web.http.JsonRequest.dispatch')
    orig_dispatch = JsonRequest.dispatch

    def dispatch(*args, **kwargs):
        with profiling():
            return orig_dispatch(*args, **kwargs)
    JsonRequest.dispatch = dispatch


def dump_stats():
    """Dump stats to standard file"""
    _logger.info('Dump stats')
    core.profile.dump_stats(os.path.expanduser('~/.openerp_server.stats'))


def patch_orm_methods():
    """Modify OpenERP/Odoo ORM methods so that profile can record."""
    origin_make_wrapper = openerp.api.make_wrapper

    _logger.info('Patching openerp.api.make_wrapper')
    def make_wrapper(*args, **kwargs):
        with profiling():
            return origin_make_wrapper(*args, **kwargs)
    openerp.api.make_wrapper = make_wrapper


def create_profile():
    """Create the global, shared profile object."""
    _logger.info('Create core.profile')
    core.profile = Profile()


def patch_stop():
    """When the server is stopped then save the result of cProfile stats"""
    origin_stop = ThreadedServer.stop

    _logger.info('Patching openerp.service.server.ThreadedServer.stop')
    def stop(*args, **kwargs):
        if openerp.tools.config['test_enable']:
            dump_stats()
        return origin_stop(*args, **kwargs)
    ThreadedServer.stop = stop


def post_load():
    _logger.info('Post load')
    create_profile()
    patch_openerp()
    if openerp.tools.config['test_enable']:
        # Enable profile in test mode for orm methods.
        _logger.info('Enabling core and apply patch')
        core.enabled = True
        patch_orm_methods()
        patch_stop()
