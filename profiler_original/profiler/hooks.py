# coding: utf-8
# License AGPL-3 or later (http://www.gnu.org/licenses/lgpl).
# Copyright 2014 Anybox <http://anybox.fr>
# Copyright 2016 Vauxoo (https://www.vauxoo.com) <info@vauxoo.com>
import logging
import os
from contextlib import contextmanager
from cProfile import Profile
# import openerp

from openerp.http import WebRequest
# from openerp.service.server import ThreadedServer
_logger = logging.getLogger(__name__)

DEFAULT_PROFILER_FNAME = os.path.expanduser('~/.profiler.stats')


class CoreProfile(object):
    # The thread-shared profile object.
    profile = Profile()
    # Indicates if the whole profiling functionality is globally active or not.
    enabled = False

    @staticmethod
    @contextmanager
    def profiling():
        """Thread local profile management, according to the shared :data:`enabled`
        """
        if CoreProfile.enabled:
            CoreProfile.profile.enable()
        try:
            yield
        finally:
            if CoreProfile.enabled:
                CoreProfile.profile.disable()

    @staticmethod
    def dump_stats():
        """Dump stats to standard file"""
        profiler_fname = os.environ.get(
            "PROFILER_FNAME", DEFAULT_PROFILER_FNAME)
        _logger.info('Dump stats at %s', profiler_fname)
        CoreProfile.profile.dump_stats(profiler_fname)

def patch_odoo():
    """Modify Odoo entry points so that profile can record.

    Odoo is a multi-threaded program. Therefore, the :data:`profile` object
    needs to be enabled/disabled each in each thread to capture all the
    execution.

    For instance, Odoo spawns a new thread for each request.
    """
    _logger.info('Patching openerp.http.WebRequest._call_function')
    webreq_f_origin = WebRequest._call_function

    def webreq_f(*args, **kwargs):
        with CoreProfile.profiling():
            return webreq_f_origin(*args, **kwargs)
    WebRequest._call_function = webreq_f

# def _____patch_stop():
#     """When the server is stopped then save the result of cProfile stats"""
#     origin_stop = ThreadedServer.stop

#     _logger.info('Patching openerp.service.server.ThreadedServer.stop')

#     def stop(*args, **kwargs):
#         if openerp.tools.config['test_enable']:
#             dump_stats()
#         return origin_stop(*args, **kwargs)
#     ThreadedServer.stop = stop


def post_load():
    # _logger.info('Post load')
    # create_profile()
    patch_odoo()
#     # if openerp.tools.config['test_enable']:
#     #     # Enable profile in test mode for orm methods.
#     #     _logger.info('Enabling profiler and apply patch')
#     #     CoreProfile.enabled = True
