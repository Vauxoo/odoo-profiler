# -*- coding: utf-8 -*-

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

    @api.multi
    def enable(self):
        self.write(dict(
            date_started=fields.Datetime.now(),
            state='enabled'
        ))

    @api.multi
    def disable(self):
        self.write(dict(
            date_finished=fields.Datetime.now(),
            state='disabled'
        ))
