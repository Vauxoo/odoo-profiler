from . import controllers  # noqa
import openerp
from cProfile import Profile
from . import core
from .core import profiling, profiling_orm_methods  # noqa
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
    core.profile_orm_methods.dump_stats(
        os.path.expanduser('~/.openerp_server_orm_methods.stats'))


def patch_orm_methods():
    """Show a command to modify OpenERP/Odoo ORM methods
    so that profile can record."""

    # TODO: Apply a monkey patch of nested method.
    fname_to_patch = os.path.join(os.path.dirname(openerp.api.__file__),
                                  "api.py")
    odoo_is_patched = 'with profiling_orm_methods():' in \
        open(fname_to_patch).read()
    if odoo_is_patched:
        _logger.info('The method openerp.api.make_wrapper is patching!')
        return True
    patch_cmds = [
        'sed -i "s/return new_api/'
        'with profiling_orm_methods(): return new_api/g" ' +
        fname_to_patch,
        'sed -i "s/return old_api/'
        'with profiling_orm_methods(): return old_api/g" ' +
        fname_to_patch,
        'sed -i "/# avoid hasattr/a ' + '\\ \\ \\ \\ \\ \\ \\ \\ '
        'from openerp.addons.profiler import profiling_orm_methods" ' +
        fname_to_patch,
    ]
    _logger.warn('You will need apply a manual patch to odoo.api.make_wrapper'
                 ' to record all ORM methods. Please execute follow commands:'
                 'Execute follow commands:\n' + '\n'.join(patch_cmds))
    return False


def create_profile():
    """Create the global, shared profile object."""
    _logger.info('Create core.profile')
    core.profile = Profile()


def create_profile_orm_methods():
    """Create other global, shared profile object."""
    _logger.info('Create core.profile_orm_methods')
    core.profile_orm_methods = Profile()


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
        create_profile_orm_methods()
        patch_orm_methods()
        patch_stop()
