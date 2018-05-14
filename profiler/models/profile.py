# -*- coding: utf-8 -*-

from openerp import models, fields


class ProfilerProfile(models.Model):
    _name = 'profiler.profile'

    enable_postgresql = fields.Boolean()
    enable_python = fields.Boolean()
    date_started = fields.Char(readonly=True)
    date_finished = fields.Char(readonly=True)

    def enable(self):
        self.write(dict(
            date_started=fields.Datetime.now
        ))

    def disable(self):
        self.write(dict(
            date_finished=fields.Datetime.now
        ))
