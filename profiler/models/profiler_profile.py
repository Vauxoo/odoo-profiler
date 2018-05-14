# -*- coding: utf-8 -*-

import base64
import logging
import os
import pstats
from contextlib import contextmanager
from cProfile import Profile
from cStringIO import StringIO

from openerp import api, fields, models, tools

DATETIME_FORMAT_FILE = "%Y%m%d_%H%M%S"
CPROFILE_EMPTY_CHARS = b"{0"

_logger = logging.getLogger(__name__)


class ProfilerProfile(models.Model):
    _name = 'profiler.profile'

    name = fields.Char()
    enable_python = fields.Boolean(default=True)
    enable_postgresql = fields.Boolean(
        default=False,
        help="It requires postgresql server logs seudo-enabled")
    use_index = fields.Boolean(
        default=False,
        help="Index human-readable cProfile attachment."
        "\nWarning: Uses more resources.")
    date_started = fields.Char(readonly=True)
    date_finished = fields.Char(readonly=True)
    state = fields.Selection([
        ('enabled', 'Enabled'),
        ('disabled', 'Disabled'),
    ], default='disabled', readonly=True)

    # TODO: Schedule a profiling in the future for a range of dates
    # TODO: One profile by each profiler.profile record
    profile = Profile()
    # TODO: multi-profiles
    enabled = None

    @api.multi
    def enable(self):
        self.ensure_one()
        _logger.info("Enabling profiler")
        self.write(dict(
            date_started=fields.Datetime.now(),
            state='enabled'
        ))
        ProfilerProfile.enabled = self.enable_python

    def get_stats_string(self, cprofile_path):
        pstats_stream = StringIO()
        pstats_obj = pstats.Stats(cprofile_path, stream=pstats_stream)
        pstats_obj.sort_stats('cumulative')
        pstats_obj.print_stats()
        pstats_stream.seek(0)
        stats_string = pstats_stream.read()
        pstats_stream = None
        return stats_string

    @api.model
    def dump_stats(self, started, finished, indexed=None):
        attachment = None
        with tools.osutil.tempdir() as dump_dir:
            started = fields.Datetime.from_string(
                started).strftime(DATETIME_FORMAT_FILE)
            finished = fields.Datetime.from_string(
                finished).strftime(DATETIME_FORMAT_FILE)
            cprofile_fname = 'stats_%d_%s_to_%s.cprofile' % (
                self.id, started, finished)
            cprofile_path = os.path.join(dump_dir, cprofile_fname)
            _logger.info("Dumping cProfile '%s'", cprofile_path)
            ProfilerProfile.profile.dump_stats(cprofile_path)
            with open(cprofile_path, "rb") as f_cprofile:
                datas = f_cprofile.read()
            if datas and datas != CPROFILE_EMPTY_CHARS:
                attachment = self.env['ir.attachment'].create({
                    'name': cprofile_fname,
                    'res_id': self.id,
                    'res_model': self._name,
                    'datas': base64.encodestring(datas),
                    'datas_fname': cprofile_fname,
                    'description': 'cProfile dump stats',
                })
                try:
                    if indexed:
                        attachment.index_content = (
                            self.get_stats_string(cprofile_path))
                except:
                    # Fancy feature but not stop process if fails
                    pass
                _logger.info("cProfile stats stored.")
            else:
                _logger.info("cProfile stats empty.")
        return attachment

    @api.multi
    def disable(self):
        self.ensure_one()
        _logger.info("Disabling profiler")
        self.write(dict(
            date_finished=fields.Datetime.now(),
            state='disabled'
        ))
        self.dump_stats(self.date_started, self.date_finished, self.use_index)
        ProfilerProfile.profile.clear()
        ProfilerProfile.enabled = False

    @staticmethod
    @contextmanager
    def profiling():
        """Thread local profile management, according to the shared "enabled"
        """
        if ProfilerProfile.enabled:
            _logger.debug("Catching profiling")
            ProfilerProfile.profile.enable()
        try:
            yield
        finally:
            if ProfilerProfile.enabled:
                ProfilerProfile.profile.disable()
