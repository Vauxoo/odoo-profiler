# -*- coding: utf-8 -*-

from contextlib import contextmanager
from cProfile import Profile

from openerp import api, fields, models


class ProfilerProfile(models.Model):
    _name = 'profiler.profile'

    enable_postgresql = fields.Boolean()
    enable_python = fields.Boolean()
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
        self.write(dict(
            date_started=fields.Datetime.now(),
            state='enabled'
        ))
        self.enabled = True

    @api.multi
    def disable(self):
        self.write(dict(
            date_finished=fields.Datetime.now(),
            state='disabled'
        ))
        self.enabled = False
        self.profile.dump_stats("/tmp/borrar.stats")
        self.profile.clear()

    @staticmethod
    @contextmanager
    def profiling():
        """Thread local profile management, according to the shared "enabled"
        """
        if ProfilerProfile.enabled:
            ProfilerProfile.profile.enable()
        try:
            yield
        finally:
            if ProfilerProfile.enabled:
                ProfilerProfile.profile.disable()
