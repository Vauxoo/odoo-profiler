# -*- coding: utf-8 -*-

import logging

from openerp.http import WebRequest

from .models.profiler_profile import ProfilerProfile

_logger = logging.getLogger(__name__)


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
        with ProfilerProfile.profiling():
            return webreq_f_origin(*args, **kwargs)
    WebRequest._call_function = webreq_f


def post_load():
    patch_odoo()
